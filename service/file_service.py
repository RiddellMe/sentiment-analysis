import csv
from datetime import datetime
from typing import List

from classifier.naive_bayes import ClassificationData
from service.ticker_service import TickerDataDTO, AggregateTickerData

_DATE_FMT = "%Y%m%d"


def write_ticker_count_to_csv(data: TickerDataDTO):
    file_name = f'ticker_{len(data.aggregate_data)}_{data.from_date.strftime(_DATE_FMT)}-{data.to_date.strftime(_DATE_FMT)}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(AggregateTickerData.__fields__)
        for ticker_data in data.aggregate_data:
            writer.writerow(ticker_data.dict().values())
    return file_name


def write_comment_sentiment_to_csv(data: List[ClassificationData], ticker: str):
    file_name = f'sentiment_analysis_{ticker}_{len(data)}_{datetime.utcnow().strftime(_DATE_FMT)}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(ClassificationData.__fields__)
        for classification_data in data:
            writer.writerow(classification_data.dict().values())
    return file_name


def read_csv(file_name: str):
    with open(file_name, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    return data
