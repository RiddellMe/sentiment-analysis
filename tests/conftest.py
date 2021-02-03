from datetime import datetime, timedelta

import pytest

from models import AggregateTickerData, TickerDataDTO
from classifier.naive_bayes import ClassificationData


@pytest.fixture
def ticker_aggregate_data_list():
    return [
        AggregateTickerData(ticker="AAPL", count=10),
        AggregateTickerData(ticker="TSLA", count=1000),
        AggregateTickerData(ticker="SPCE", count=50),
        AggregateTickerData(ticker="GME", count=30000)
    ]


@pytest.fixture
def ticker_return_data(ticker_aggregate_data_list):
    end_datetime = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    start_datetime = (end_datetime - timedelta(days=2))
    ticker_data = TickerDataDTO(aggregate_data=ticker_aggregate_data_list, from_date=start_datetime,
                                to_date=end_datetime)

    file_output = [['ticker', 'count', 'failed_during_fetch'], ['AAPL', '10', 'False'], ['TSLA', '1000', 'False'],
                   ['SPCE', '50', 'False'], ['GME', '30000', 'False']]
    return ticker_data, file_output


@pytest.fixture
def classification_data():
    training_data = [ClassificationData(comment="I love GME.buy and hold! TO THE MOON", classification=1),
                     ClassificationData(comment="BUY GME   ON OPEN. hold the line", classification=1),
                     ClassificationData(comment="gme order to buy 500 at open. already bought 200 yesterday",
                                        classification=1),
                     ClassificationData(comment="I hate GME. sell and short", classification=0),
                     ClassificationData(comment="Gme kinda sucks right now", classification=0),
                     ClassificationData(
                         comment="What the hell GME? hype is over. you should sell asap. shorts have you by the balls",
                         classification=0)]

    test_data = ["GME sucks. sell it at open. short interest is DOWN", "GME is going to the MOON. HOLD!",
                 "short sell that crap", "i bought another 100 at open. BUY",
                 "likely to hate yourself if you buy now..."]

    expected_output = [ClassificationData(comment='gme sucks sell it at open short interest is down', classification=0),
                       ClassificationData(comment='gme is going to the moon hold ', classification=1),
                       ClassificationData(comment='short sell that crap', classification=0),
                       ClassificationData(comment='i bought another 100 at open buy', classification=1),
                       ClassificationData(comment='likely to hate yourself if you buy now ', classification=0)]

    result_list = [['comment', 'classification'], ['gme is going to the moon hold ', 1], ['gme sucks sell it at open short interest is down', 0], ['short sell that crap', 0], ['i bought another 100 at open buy', 1], ['likely to hate yourself if you buy now ', 0]]
    return training_data, test_data, expected_output, result_list
