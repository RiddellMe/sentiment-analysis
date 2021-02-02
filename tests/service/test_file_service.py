from service import file_service


def test_file_writes_csv(aggregate_data_list):
    file_service.write_to_csv(aggregate_data_list)
