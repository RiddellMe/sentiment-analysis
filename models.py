from datetime import datetime
from typing import List

from pydantic import BaseModel


class AggregateTickerData(BaseModel):
    ticker: str
    count: int
    failed_during_fetch: bool = False


class TickerDataDTO(BaseModel):
    aggregate_data: List[AggregateTickerData]
    from_date: datetime
    to_date: datetime
