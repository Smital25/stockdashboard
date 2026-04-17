from pydantic import BaseModel
from typing import Optional

class StockRecord(BaseModel):
    symbol:       str
    date:         str
    open:         float
    high:         float
    low:          float
    close:        float
    volume:       int
    daily_return: float
    ma_7:         Optional[float]
    volatility:   Optional[float]

class SummaryResponse(BaseModel):
    symbol:         str
    high_52w:       float
    low_52w:        float
    avg_close:      float
    avg_return:     float
    avg_volatility: float

class CompanyInfo(BaseModel):
    symbol: str
    ticker: str

class TopMover(BaseModel):
    symbol:       str
    daily_return: float

class TopMoversResponse(BaseModel):
    gainers: list[TopMover]
    losers:  list[TopMover]

class CompareResponse(BaseModel):
    symbol1:     str
    symbol2:     str
    correlation: float
    data1:       list[StockRecord]
    data2:       list[StockRecord]