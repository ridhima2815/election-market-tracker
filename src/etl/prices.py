from __future__ import annotations
import time
import numpy as np
import pandas as pd
import yfinance as yf
from src.config import settings

class PriceProvider:
    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        raise NotImplementedError

class YahooProvider(PriceProvider):
    def fetch(self, ticker, start, end):
        data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False, threads=False)
        return normalize_prices(data)

class StooqProvider(PriceProvider):
    def fetch(self, ticker, start, end):
        from pandas_datareader import data as pdr
        symbol = ticker.replace("^", "").lower()
        data = pdr.DataReader(symbol, "stooq", start=start, end=end)
        return normalize_prices(data)

def normalize_prices(data: pd.DataFrame) -> pd.DataFrame:
    if data is None or data.empty: raise ValueError("Empty price dataset")
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    if "Close" not in df.columns:
        if "Adj Close" in df.columns: df["Close"] = df["Adj Close"]
        else: raise ValueError("Missing Close column")
    df = df[["Close"]].copy()
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna().sort_index()
    if df.empty or (df["Close"] <= 0).any(): raise ValueError("Invalid price data")
    idx = pd.to_datetime(df.index)
    if idx.tz is not None: idx = idx.tz_localize(None)
    df.index = idx.normalize()
    return df[~df.index.duplicated(keep="last")]

def demo_prices(country, start, end):
    dates = pd.bdate_range(start, end)
    if not len(dates): return pd.DataFrame(columns=["Close"], index=dates)
    seed = sum(ord(c) for c in country)
    rng = np.random.default_rng(seed)
    base = {"IN":22000,"US":5000,"GB":8000,"JP":38000,"DE":18000,"FR":7500,"BR":130000,"KR":2700}.get(country,1000)
    returns = rng.normal(0.00025, 0.009, len(dates))
    close = base * np.exp(np.cumsum(returns))
    return pd.DataFrame({"Close": close}, index=dates)

def fetch_prices(ticker, start, end, providers=None, attempts=3):
    providers = providers or [YahooProvider(), StooqProvider()]
    errors=[]
    for provider in providers:
        for attempt in range(attempts):
            try: return normalize_prices(provider.fetch(ticker,start,end))
            except Exception as exc:
                errors.append(f"{provider.__class__.__name__}: {exc}")
                if attempt < attempts-1: time.sleep(2**attempt)
    raise RuntimeError("All price providers failed: " + " | ".join(errors))

def get_prices(country, ticker, start, end):
    if settings.DEMO_MODE: return demo_prices(country,start,end)
    return fetch_prices(ticker,start,end)

def daily_returns(prices):
    return normalize_prices(prices)["Close"].pct_change().dropna()
