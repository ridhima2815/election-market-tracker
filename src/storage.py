import sqlite3
from pathlib import Path
import pandas as pd
from src.config import settings

class SQLiteStore:
    def __init__(self, database_path=None):
        self.database_path = database_path or settings.DATABASE_PATH
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()
    def connect(self):
        return sqlite3.connect(self.database_path)
    def initialize(self):
        with self.connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS headlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL,
                published_at TEXT, sentiment REAL, sentiment_label TEXT, source TEXT,
                collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(country, url))""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_headlines_country ON headlines(country)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_headlines_date ON headlines(published_at)")
    def save_headlines(self, df):
        if df is None or df.empty: return
        rows = [tuple(row.get(k) for k in ("country","title","url","published_at","sentiment","sentiment_label","source")) for row in df.to_dict("records")]
        with self.connect() as conn:
            conn.executemany("INSERT OR IGNORE INTO headlines(country,title,url,published_at,sentiment,sentiment_label,source) VALUES(?,?,?,?,?,?,?)", rows)
    def get_headlines(self, country=None, limit=5000):
        sql = "SELECT * FROM headlines"
        params = []
        if country:
            sql += " WHERE country=?"
            params.append(country)
        sql += " ORDER BY published_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)
