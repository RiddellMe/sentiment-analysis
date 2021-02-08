import csv
import os

from service import file_service


# todo read file, assert, delete file
def test_file_writes_csv(ticker_return_data):
    ticker_data, file_output = ticker_return_data
    file_name = file_service.write_to_csv(ticker_data)
    with open(file_name, 'r') as f:
        reader = csv.reader(f)
        actual_output = list(reader)
    assert file_output == actual_output
    os.remove(file_name)
