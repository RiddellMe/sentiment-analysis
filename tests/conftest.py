import pytest

from reddit_analysis import AggregateTickerData


@pytest.fixture
def aggregate_data_list():
    return [
        AggregateTickerData(ticker="AAPL", count=10),
        AggregateTickerData(ticker="TSLA", count=1000),
        AggregateTickerData(ticker="SPCE", count=50),
        AggregateTickerData(ticker="GME", count=30000)
    ]
