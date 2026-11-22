import re
from urllib.parse import quote
import feedparser
import pandas as pd
import requests
from src.config import settings
USER_AGENT="Mozilla/5.0 (compatible; ElectionMarketTracker/1.0)"
def clean_title(title): return re.sub(r"\s+-\s+[^-]+$", "", str(title)).strip()
def normalize_url(url): return str(url).strip().split("&ved=")[0].split("&usg=")[0]
def fetch_news(country_code, country_name, locale="en-US", limit=50):
    query=quote(f"{country_name} election politics government")
    lang, region=locale.split("-")
    url=f"https://news.google.com/rss/search?q={query}&hl={locale}&gl={region}&ceid={region}:{lang}"
    response=requests.get(url,headers={"User-Agent":USER_AGENT},timeout=settings.REQUEST_TIMEOUT)
    response.raise_for_status()
    feed=feedparser.parse(response.content)
    rows=[]
    for entry in feed.entries[:limit]:
        title=clean_title(entry.get("title","")); link=normalize_url(entry.get("link",""))
        if not title or not link: continue
        published=pd.Timestamp(entry.published) if entry.get("published") else pd.Timestamp.now(tz="UTC")
        if published.tzinfo is None: published=published.tz_localize("UTC")
        else: published=published.tz_convert("UTC")
        rows.append({"country":country_code,"title":title,"url":link,"published_at":published,"source":entry.get("source",{}).get("title","")})
    df=pd.DataFrame(rows)
    if df.empty: return df
    return df.drop_duplicates(subset=["title"]).drop_duplicates(subset=["url"]).reset_index(drop=True)
