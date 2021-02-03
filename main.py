import logging

from service import file_service, ticker_service

logger = logging.getLogger(__name__)


def count_stock_tickers():
    # tickers = get_list_of_tickers()  # This is not required if you provide your own list of tickers
    tickers = ["GME", "AAPL", "SPCE", "TSLA"]
    subreddit = "wallstreetbets"  # pick a subreddit, or leave blank to analyze all subreddits
    prev_day_count = 4
    data = ticker_service.aggregate_ticker_comment_count(tickers, prev_day_count, subreddit)
    file_service.write_to_csv(data)


def naive_bayes_sentiment_analysis():
    ticker = "AAPL"
    subreddit = "wallstreetbets"
    prev_day_count = 4
    comments = ticker_service.get_ticker_comments(ticker, prev_day_count, subreddit)
    print(comments)
    # todo: come up with some training data


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s : %(threadName)s : %(lineno)d - %(message)s",
                        datefmt="%X")
    logger.info(f"#### Running script from {__file__} ####")
    naive_bayes_sentiment_analysis()
    count_stock_tickers()
