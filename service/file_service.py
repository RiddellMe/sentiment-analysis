import csv
from datetime import datetime
from typing import List

from reddit_analysis import AggregateTickerData


def write_to_csv(aggregate_data: List[AggregateTickerData]):
    with open(f'ticker_data_{datetime.utcnow().timestamp()}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(AggregateTickerData.__fields__)
        for ticker_data in aggregate_data:
            writer.writerow(ticker_data.dict().values())