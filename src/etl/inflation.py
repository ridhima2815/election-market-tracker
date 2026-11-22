import requests
import pandas as pd
from src.config import settings

URL = "https://api.worldbank.org/v2/country/{iso3}/indicator/FP.CPI.TOTL.ZG"
def get_world_bank_inflation(iso3):
    r = requests.get(URL.format(iso3=iso3), params={"format":"json","per_page":100}, timeout=settings.REQUEST_TIMEOUT)
    r.raise_for_status()
    payload = r.json()
    if len(payload)<2 or not payload[1]: return {"value":None,"year":None,"source":"World Bank"}
    df = pd.DataFrame(payload[1]).dropna(subset=["value"])
    if df.empty: return {"value":None,"year":None,"source":"World Bank"}
    row = df.iloc[0]
    return {"value":float(row["value"]),"year":int(row["date"]),"source":"World Bank"}
def get_inflation(iso3):
    if settings.DEMO_MODE: return {"value":4.2,"year":2024,"source":"Demo data"}
    try: return get_world_bank_inflation(iso3)
    except Exception as exc: return {"value":None,"year":None,"source":f"Unavailable: {exc}"}
