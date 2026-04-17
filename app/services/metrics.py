import pandas as pd

def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["daily_return"] = (df["close"] - df["open"]) / df["open"]
    df["ma_7"]         = df["close"].rolling(7).mean()
    df["ma_30"]        = df["close"].rolling(30).mean()
    df["volatility"]   = df["close"].pct_change().rolling(20).std() * 100
    return df

def compute_correlation(df1: pd.DataFrame, df2: pd.DataFrame) -> float:
    merged = pd.merge(
        df1[["date","close"]].rename(columns={"close":"c1"}),
        df2[["date","close"]].rename(columns={"close":"c2"}),
        on="date"
    )
    if merged.empty:
        return 0.0
    return round(merged["c1"].corr(merged["c2"]), 4)