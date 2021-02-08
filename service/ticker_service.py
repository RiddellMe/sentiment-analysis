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

from util.timer import Timer

_PUSHSHIFT_COMMENT_API = "https://api.pushshift.io/reddit/search/comment/"
_TICKER_FILES = ["ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt",
                 "ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt"]
# Number of times to retry calling the API if call fails
_API_RETRY_ATTEMPTS = 10
# How many upvotes the comment should have to be included in search
_UPVOTE_THRESHOLD = 2
# 100 is upper limit of search results. Do not increase above 100
_API_SEARCH_RESULT_SIZE = 100

# Two workers seems to be the max before we get a 409 response from api
_THREAD_COUNT = 2
_SECONDS_TO_SLEEP_BEFORE_NEW_REQUEST = 3

logger = logging.getLogger(__name__)


class AggregateTickerData(BaseModel):
    ticker: str
    count: int
    failed_during_fetch: bool = False


class TickerDataDTO(BaseModel):
    aggregate_data: List[AggregateTickerData]
    from_date: datetime
    to_date: datetime


def aggregate_ticker_comment_count(ticker_list: List[str], days_to_look_back: int = 1, subreddit_to_search: str = None,
                                   end_datetime: datetime = datetime.utcnow()) -> TickerDataDTO:
    timer = Timer()
    timer.start()
    start_datetime, end_datetime = get_start_and_end_date(end_datetime, days_to_look_back)
    aggregate_data_list: List[AggregateTickerData] = []
    if subreddit_to_search:
        logger.info(f"Searching in subreddit: {subreddit_to_search}")
    else:
        logger.info("Searching in all subreddits")
    with futures.ThreadPoolExecutor(max_workers=_THREAD_COUNT) as executor:
        future_list = []
        completed = 0
        for ticker in ticker_list:
            future_list.append(
                executor.submit(count_ticker_comments, ticker, start_datetime, end_datetime, subreddit_to_search))
        for future in futures.as_completed(future_list):
            completed += 1
            aggregate_data = future.result()
            if aggregate_data.count:
                aggregate_data_list.append(aggregate_data)
            if completed % 10 == 0:
                logger.info(f"Analyzed {completed} tickers. Elapsed time: {int(timer.get_elapsed_time())} seconds")
            logger.debug(
                f"Found {aggregate_data.count} mentions of {aggregate_data.ticker} with at least {_UPVOTE_THRESHOLD} upvotes from {start_datetime} to {end_datetime}.")
    sort_aggregate_data_by_count(aggregate_data_list)
    logger.info(aggregate_data_list)
    logger.info(f"Analyzed {len(ticker_list)} tickers in {int(timer.end())} seconds.")
    return TickerDataDTO(aggregate_data=aggregate_data_list, from_date=start_datetime, to_date=end_datetime)


def filter_comments_by_upvotes(comment_list: List[Dict]) -> int:
    upvoted_comments = 0
    for comment in comment_list:
        if comment.get("score") >= _UPVOTE_THRESHOLD:
            upvoted_comments += 1
    return upvoted_comments


def count_ticker_comments(ticker: str, from_date: datetime, to_date: datetime,
                          subreddit_to_search: Optional[str]) -> AggregateTickerData:
    # Turn datetime into unix timestamp with no milliseconds
    from_timestamp = int(from_date.timestamp())
    to_timestamp = int(to_date.timestamp())
    aggregate_data = AggregateTickerData(ticker=ticker, count=0)
    with requests.Session() as session:
        while True:
            try:
                api_call = create_api_call(aggregate_data.ticker, from_timestamp, to_timestamp, subreddit_to_search)
                content = get_comments_from_api(session, api_call)
            except ApiError:
                aggregate_data.failed_during_fetch = True
                break
            if len(content) < _API_SEARCH_RESULT_SIZE:
                break
            else:
                from_timestamp = content[_API_SEARCH_RESULT_SIZE - 1].get("created_utc")
            aggregate_data.count += filter_comments_by_upvotes(content)
    return aggregate_data


def create_api_call(ticker: str, from_timestamp: int, to_timestamp: int, subreddit_to_search: Optional[str]) -> str:
    logger.debug(
        f"Fetching {ticker} data from date: {datetime.fromtimestamp(from_timestamp)} to date: {datetime.fromtimestamp(to_timestamp)}")
    search_params = f"?q={ticker}&sort=asc&sort_type=created_utc&after={from_timestamp}&before={to_timestamp}&size={_API_SEARCH_RESULT_SIZE}"
    if subreddit_to_search:
        search_params += f"&subreddit={subreddit_to_search}"
    return os.path.join(_PUSHSHIFT_COMMENT_API, search_params)


def get_comments_from_api(session: requests.Session, api_call: str) -> List[Dict]:
    content: List[Dict] = []
    for retry_attempt in range(_API_RETRY_ATTEMPTS):
        resp = session.get(api_call)
        # Ensure we retry calling api when response is an error code
        if resp.status_code != 200:
            logger.debug(f"Error occurred during call to: {api_call}.\n"
                         f"Status code: {resp.status_code}\n"
                         f"Sleeping for {_SECONDS_TO_SLEEP_BEFORE_NEW_REQUEST + retry_attempt} seconds.")
            # We sleep for longer as number of retries increases to reduce requests on API
            sleep(_SECONDS_TO_SLEEP_BEFORE_NEW_REQUEST + retry_attempt)
            if retry_attempt is _API_RETRY_ATTEMPTS - 1:
                raise ApiError(f"{api_call} failed too many times in a row.")
        else:
            try:
                content = json.loads(resp.text).get("data")
                break
            except Exception as e:
                logger.exception(f"Unexpected exception occurred.\n"
                                 f"STATUS CODE: {resp.status_code}\n"
                                 f"API CALL: {api_call}\n"
                                 f"RESPONSE TEXT: {resp.text}")
                raise e
    return content


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


def sort_aggregate_data_by_count(data: List[AggregateTickerData]):
    data.sort(key=lambda x: x.count, reverse=True)


def get_ticker_comments(ticker: str, days_to_look_back: int = 1, subreddit_to_search: str = None,
                        end_datetime: datetime = datetime.utcnow()) -> List[str]:
    timer = Timer()
    timer.start()
    start_datetime, end_datetime = get_start_and_end_date(end_datetime, days_to_look_back)
    from_timestamp = int(start_datetime.timestamp())
    to_timestamp = int(end_datetime.timestamp())
    comments = []
    with requests.Session() as session:
        while True:
            try:
                api_call = create_api_call(ticker, from_timestamp, to_timestamp, subreddit_to_search)
                content = get_comments_from_api(session, api_call)
            except ApiError:
                break
            if len(content) < _API_SEARCH_RESULT_SIZE:
                break
            else:
                from_timestamp = content[_API_SEARCH_RESULT_SIZE - 1].get("created_utc")
        comments.extend(get_comments_from_content(content))
    logger.debug(
        f"Found {len(comments)} comments of {ticker} with at least {_UPVOTE_THRESHOLD} upvotes from {start_datetime} to {end_datetime}.")
    logger.info(f"Analyzed {len(comments)} comments from ticker: {ticker} in {int(timer.end())} seconds")
    return comments


def get_comments_from_content(content: List[Dict]):
    return [comment.get("body") for comment in content]


def get_start_and_end_date(end_datetime: datetime, days_to_look_back: int):
    end_datetime = end_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
    start_datetime = (end_datetime - timedelta(days=days_to_look_back))
    logger.info(f"Start date is: {start_datetime}, end date is: {end_datetime}")
    return start_datetime, end_datetime


class ApiError(Exception):
    pass
