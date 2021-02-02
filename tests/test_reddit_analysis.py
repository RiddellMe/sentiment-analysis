from reddit_analysis import sort_aggregate_data_by_count


def test_sort_aggregate_data_by_count_sorts_list(aggregate_data_list):
    agg_data = aggregate_data_list
    sort_aggregate_data_by_count(aggregate_data_list)

    for i in range(len(agg_data) - 1):
        assert agg_data[i].count > agg_data[i + 1].count
