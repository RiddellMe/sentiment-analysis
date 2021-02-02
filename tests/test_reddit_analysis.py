from reddit_analysis import AggregateTickerData, sort_aggregate_data_by_count


def test_sort_aggregate_data_by_count_sorts_list():
    agg_data = [
        AggregateTickerData(ticker="AAPL", count=10),
        AggregateTickerData(ticker="TSLA", count=1000),
        AggregateTickerData(ticker="SPCE", count=50),
        AggregateTickerData(ticker="GME", count=30000)
    ]
    sort_aggregate_data_by_count(agg_data)

    assert agg_data[0].ticker is "GME"
    assert agg_data[1].ticker is "TSLA"
    assert agg_data[2].ticker is "SPCE"
    assert agg_data[3].ticker is "AAPL"
