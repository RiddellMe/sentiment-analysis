import json
import logging
import os
from concurrent import futures
from datetime import datetime, timedelta
from time import sleep
from typing import Dict, List, Optional
from urllib import request

import requests
from pydantic import BaseModel

from utils.timer import Timer

_PUSHSHIFT_COMMENT_API = "https://api.pushshift.io/reddit/search/comment/"
_TICKER_FILES = ["ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt",
                 "ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt"]
# How much karma the comment should have to be included in search
_KARMA_THRESHOLD = 3
# 100 is upper limit of search results. Do not increase above 100
_API_SEARCH_RESULT_SIZE = 100

# Two workers seems to be the max before we get a 409 response from api
_THREAD_COUNT = 2
_SECONDS_TO_SLEEP_BEFORE_NEW_REQUEST = 3

logger = logging.getLogger(__name__)


class AggregateTickerData(BaseModel):
    ticker: str
    count: int


def aggregate_ticker_comment_count(ticker_list: List[str], days_to_look_back: int = 1,
                                   subreddit_to_search: str = None) -> List[AggregateTickerData]:
    timer = Timer()
    timer.start()
    start_date = (datetime.utcnow() - timedelta(days=days_to_look_back))
    aggregate_data_list: List[AggregateTickerData] = []
    if subreddit_to_search:
        logger.info(f"Searching in subreddit: {subreddit_to_search}")
    else:
        logger.info("Searching in all subreddits")
    with futures.ThreadPoolExecutor(max_workers=_THREAD_COUNT) as executor:
        future_list = []
        completed = 0
        for ticker in ticker_list:
            future_list.append(executor.submit(count_ticker_comments, ticker, start_date, subreddit_to_search))
        for future in futures.as_completed(future_list):
            completed += 1
            aggregate_data = future.result()
            count = aggregate_data.count
            if count:
                aggregate_data_list.append(aggregate_data)
            if completed % 10 == 0:
                logger.info(f"Analyzed {completed} tickers. Elapsed time: {int(timer.get_elapsed_time())} seconds")
            logger.debug(
                f"Found {count} mentions of {aggregate_data.ticker} with at least {_KARMA_THRESHOLD} karma over the last {days_to_look_back} day(s).")
    logger.info(aggregate_data_list)
    logger.info(f"Analyzed {len(ticker_list)} tickers in {timer.end()} seconds.")
    return aggregate_data_list


def filter_comments_with_no_karma(comment_list: List[Dict]) -> int:
    upvoted_comments = 0
    for comment in comment_list:
        if comment.get("score") >= _KARMA_THRESHOLD:
            upvoted_comments += 1
    return upvoted_comments


def count_ticker_comments(ticker: str, from_date: datetime, subreddit_to_search: Optional[str]) -> AggregateTickerData:
    # Turn datetime into unix timestamp with no milliseconds
    from_timestamp = int(from_date.timestamp())
    number_upvoted_comments = 0
    with requests.Session() as session:
        more_iterations_available = True
        while more_iterations_available:
            logger.debug(f"Fetching {ticker} data from date: {datetime.fromtimestamp(from_timestamp)}")
            search_params = f"?q={ticker}&sort=asc&sort_type=created_utc&after={from_timestamp}&size={_API_SEARCH_RESULT_SIZE}"
            if subreddit_to_search:
                search_params += f"&subreddit={subreddit_to_search}"
            api_call = os.path.join(_PUSHSHIFT_COMMENT_API, search_params)
            for retry_attempt in range(10):
                bad_status_code = False
                resp = session.get(api_call)
                # Ensure these commonly encountered error codes are re-requested
                if resp.status_code in [429, 522, 525]:
                    logger.warning(f"Error occurred during call to: {api_call}.\n"
                                   f"Status code: {resp.status_code}\n"
                                   f"Sleeping for {_SECONDS_TO_SLEEP_BEFORE_NEW_REQUEST} seconds.")
                    sleep(_SECONDS_TO_SLEEP_BEFORE_NEW_REQUEST)
                else:
                    try:
                        content: List[Dict] = json.loads(resp.text).get("data")
                        break
                    except Exception as e:
                        logger.exception(f"Unexpected exception occurred.\n"
                                         f"STATUS CODE: {resp.status_code}\n"
                                         f"API CALL: {api_call}\n"
                                         f"RESPONSE TEXT: {resp.text}")
                        raise e
            if not content or len(content) < _API_SEARCH_RESULT_SIZE:
                more_iterations_available = False
            else:
                from_timestamp = content[_API_SEARCH_RESULT_SIZE - 1].get("created_utc")
            number_upvoted_comments += filter_comments_with_no_karma(content)

    return AggregateTickerData(ticker=ticker, count=number_upvoted_comments)


def get_list_of_tickers() -> List[str]:
    ticker_list = []
    for url in _TICKER_FILES:
        filename = os.path.basename(url)
        # Skip downloading NASDAQ ticker files if they have been downloaded previously
        if os.path.isfile(filename):
            logger.info(f"{filename} already exists. Skip fetching tickers.")
        else:
            logger.info(f"Fetching {filename} from source.")
            request.urlretrieve(url, filename)
        with open(filename, "r") as f:
            for j, line in enumerate(f):
                # Ignore first row (only contains metadata)
                if j != 0:
                    ticker = line.split("|")[0]
                    # Remove duplicate ticker(s) (if any)
                    if ticker not in ticker_list:
                        ticker_list.append(ticker)
    logger.info(f"Sourced {len(ticker_list)} tickers")
    return ticker_list


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(threadName)s : %(lineno)d - %(message)s",
                        datefmt="%X")
    logger.info(f"#### Running script from {__file__} ####")
    subreddit = "wallstreetbets"  # pick a subreddit, or leave blank to analyze all subreddits
    tickers = get_list_of_tickers()  # This is not required if you provide your own list of tickers
    prev_day_count = 1
    aggregate_ticker_comment_count(tickers, prev_day_count, subreddit)
