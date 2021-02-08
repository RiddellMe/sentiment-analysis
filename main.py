import logging
import os

from classifier.naive_bayes import NaiveBayes
from service import file_service, ticker_service

logger = logging.getLogger(__name__)


def count_stock_tickers():
    # tickers = get_list_of_tickers()  # This is not required if you provide your own list of tickers
    tickers = ["GME", "AAPL", "SPCE", "TSLA"]
    subreddit = "wallstreetbets"  # pick a subreddit, or leave blank to analyze all subreddits
    prev_day_count = 4
    data = ticker_service.aggregate_ticker_comment_count(tickers, prev_day_count, subreddit)
    file_service.write_ticker_count_to_csv(data)


def naive_bayes_sentiment_analysis():
    ticker = "PLTR"
    subreddit = "wallstreetbets"
    prev_day_count = 4
    comments = ticker_service.get_ticker_comments(ticker, prev_day_count, subreddit)
    training_data_list = file_service.read_csv(os.path.join(os.path.dirname(__file__), "training_data.csv"))
    naive_bayes = NaiveBayes(words_to_ignore=[ticker])
    training_data = naive_bayes.convert_from_list(training_data_list)
    naive_bayes.train(training_data)
    data = naive_bayes.test(comments)
    file_service.write_comment_sentiment_to_csv(data.classification_list, ticker)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s : %(threadName)s : %(lineno)d - %(message)s",
                        datefmt="%X")
    logger.info(f"#### Running script from {__file__} ####")
    naive_bayes_sentiment_analysis()
    # count_stock_tickers()
