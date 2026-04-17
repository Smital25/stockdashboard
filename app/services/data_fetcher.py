import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/stocks.db")

STOCKS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "WIPRO":    "WIPRO.NS",
    "ICICIBANK":"ICICIBANK.NS",
    "BAJFINANCE":"BAJFINANCE.NS",
    "SBIN":     "SBIN.NS",
    "ADANIENT": "ADANIENT.NS",
    "TATAMOTORS":"TATAMOTORS.NS",
}

# ---------------- DB ---------------- #

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            symbol      TEXT,
            date        TEXT,
            open        REAL,
            high        REAL,
            low         REAL,
            close       REAL,
            volume      INTEGER,
            daily_return REAL,
            ma_7        REAL,
            volatility  REAL,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.commit()
    conn.close()

# ---------------- FETCH ---------------- #

def fetch_and_store(symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
    ticker = STOCKS.get(symbol)
    if not ticker:
        return None

    try:
        df = yf.download(
    ticker,
    period=period,
    auto_adjust=True,
    progress=False,
    threads=False
)
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

    # ✅ handle empty / failed data
    if df is None or df.empty:
        print(f"⚠️ No data for {symbol} (skipping)")
        return None

    # flatten multi-level columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["symbol"] = symbol

    # metrics
    df["daily_return"] = (df["close"] - df["open"]) / df["open"]
    df["ma_7"] = df["close"].rolling(7).mean()
    df["volatility"] = df["close"].pct_change().rolling(20).std() * 100

    df = df[
        ["symbol","date","open","high","low","close","volume",
         "daily_return","ma_7","volatility"]
    ].dropna(subset=["close"])

    conn = get_db()

    # remove old data for symbol
    conn.execute("DELETE FROM stock_prices WHERE symbol = ?", (symbol,))
    conn.commit()

    # insert new data
    df.to_sql(
        "stock_prices",
        conn,
        if_exists="append",
        index=False,
        method="multi"
    )

    conn.close()
    return df

def fetch_all():
    init_db()
    for symbol in STOCKS:
        print(f"Fetching {symbol}...")
        result = fetch_and_store(symbol)

        if result is None:
            print(f"⚠️ Skipped {symbol}")
        else:
            print(f"✅ Stored {symbol}")

    print("✅ Done.")

# ---------------- QUERIES ---------------- #

def get_stock_data(symbol: str, days: int = 30) -> list[dict]:
    conn = get_db()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    rows = conn.execute("""
        SELECT * FROM stock_prices
        WHERE symbol = ? AND date >= ?
        ORDER BY date ASC
    """, (symbol, cutoff)).fetchall()

    conn.close()

    cols = ["symbol","date","open","high","low","close","volume",
            "daily_return","ma_7","volatility"]

    return [dict(zip(cols, r)) for r in rows]

def get_summary(symbol: str) -> dict:
    conn = get_db()

    row = conn.execute("""
        SELECT
            MAX(high),
            MIN(low),
            AVG(close),
            AVG(daily_return),
            AVG(volatility)
        FROM stock_prices
        WHERE symbol = ?
        AND date >= date('now', '-365 days')
    """, (symbol,)).fetchone()

    conn.close()

    if not row or row[0] is None:
        return {}

    return {
        "symbol": symbol,
        "high_52w": round(row[0], 2),
        "low_52w": round(row[1], 2),
        "avg_close": round(row[2], 2),
        "avg_return": round(row[3] * 100, 4),
        "avg_volatility": round(row[4], 4),
    }

def get_all_companies() -> list[dict]:
    return [{"symbol": s, "ticker": t} for s, t in STOCKS.items()]

def get_top_movers(n: int = 5) -> dict:
    conn = get_db()

    rows = conn.execute("""
        SELECT symbol, daily_return
        FROM stock_prices
        WHERE date = (SELECT MAX(date) FROM stock_prices)
        ORDER BY daily_return DESC
    """).fetchall()

    conn.close()

    data = [
        {"symbol": r[0], "daily_return": round(r[1] * 100, 2)}
        for r in rows
    ]

    return {
        "gainers": data[:n],
        "losers": list(reversed(data[-n:]))
    }

# ---------------- CLI RUN ---------------- #

if __name__ == "__main__":
    fetch_all()