from fastapi import APIRouter, HTTPException, Query
from app.services.data_fetcher import (
    get_stock_data, get_summary, get_all_companies,
    get_top_movers, STOCKS
)
from app.services.metrics import compute_correlation
from app.models.schemas import (
    StockRecord, SummaryResponse, CompanyInfo,
    TopMoversResponse, CompareResponse
)
import pandas as pd

router = APIRouter(prefix="/api", tags=["stocks"])

@router.get("/companies", response_model=list[CompanyInfo])
def companies():
    return get_all_companies()

@router.get("/data/{symbol}", response_model=list[StockRecord])
def stock_data(symbol: str, days: int = Query(30, ge=7, le=365)):
    symbol = symbol.upper()
    if symbol not in STOCKS:
        raise HTTPException(404, f"{symbol} not found")
    data = get_stock_data(symbol, days)
    if not data:
        raise HTTPException(404, "No data. Run /api/refresh first.")
    return data

@router.get("/summary/{symbol}", response_model=SummaryResponse)
def summary(symbol: str):
    symbol = symbol.upper()
    result = get_summary(symbol)
    if not result:
        raise HTTPException(404, f"No summary data for {symbol}")
    return result

@router.get("/compare", response_model=CompareResponse)
def compare(
    symbol1: str = Query(...),
    symbol2: str = Query(...)
):
    s1, s2 = symbol1.upper(), symbol2.upper()
    d1 = get_stock_data(s1, 90)
    d2 = get_stock_data(s2, 90)
    if not d1 or not d2:
        raise HTTPException(404, "One or both symbols have no data")

    df1 = pd.DataFrame(d1)
    df2 = pd.DataFrame(d2)
    corr = compute_correlation(df1, df2)

    return {
        "symbol1": s1, "symbol2": s2,
        "correlation": corr,
        "data1": d1, "data2": d2
    }

@router.get("/top-movers", response_model=TopMoversResponse)
def top_movers(n: int = Query(5, ge=1, le=10)):
    return get_top_movers(n)

@router.post("/refresh")
def refresh():
    from app.services.data_fetcher import fetch_all
    fetch_all()
    return {"status": "ok", "message": "All stocks refreshed"}