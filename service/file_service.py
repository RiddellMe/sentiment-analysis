import csv

from models import AggregateTickerData, TickerDataDTO

_DATE_FMT = "%Y%m%d"


def write_to_csv(data: TickerDataDTO):
    file_name = f'ticker_{len(data.aggregate_data)}_{data.from_date.strftime(_DATE_FMT)}-{data.to_date.strftime(_DATE_FMT)}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(AggregateTickerData.__fields__)
        for ticker_data in data.aggregate_data:
            writer.writerow(ticker_data.dict().values())
    return file_name
