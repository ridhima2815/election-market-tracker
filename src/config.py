from pathlib import Path
import os
import yaml
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
FIXTURE_DIR = DATA_DIR / "fixtures"
OUTPUT_DIR = ROOT / "outputs"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class Settings:
    DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in {"1", "true", "yes"}
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "tracker.db"))
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    FRED_API_KEY = os.getenv("FRED_API_KEY", "")
    SENTIMENT_BACKEND = os.getenv("SENTIMENT_BACKEND", "vader")
    NEWS_LIMIT = int(os.getenv("NEWS_LIMIT", "50"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
settings = Settings()

def load_countries() -> dict:
    with (CONFIG_DIR / "countries.yaml").open(encoding="utf-8") as f:
        countries = yaml.safe_load(f)["countries"]
    for code, country in countries.items():
        country["code"] = code
    return countries

def load_elections() -> pd.DataFrame:
    df = pd.read_csv(CONFIG_DIR / "elections.csv")
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df["verified"] = df["verified"].astype(str).str.lower().map({"true": True, "false": False})
    return df
