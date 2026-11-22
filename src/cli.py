import argparse
from pathlib import Path
import pandas as pd
from src.config import load_countries,OUTPUT_DIR,settings
from src.storage import SQLiteStore
from src.etl.news import fetch_news
from src.etl.demo_news import demo_news
from src.etl.sentiment import score_news
from src.etl.inflation import get_inflation

def refresh(codes):
    countries=load_countries(); store=SQLiteStore()
    for code in codes:
        c=countries[code]; print(f"Refreshing {c['name']}...")
        try:
            news=demo_news(code,c["name"],"2024-01-01","2024-12-31") if settings.DEMO_MODE else fetch_news(code,c["name"],c["news_locale"],settings.NEWS_LIMIT)
            if not news.empty:store.save_headlines(score_news(news));print(f"Saved {len(news)} headlines")
            print("Inflation:",get_inflation(c["iso3"]))
        except Exception as exc:print(f"{code} refresh failed: {exc}")
def report(code):
    df=SQLiteStore().get_headlines(code); OUTPUT_DIR.mkdir(exist_ok=True)
    csv=OUTPUT_DIR/f"{code}_news.csv"; html=OUTPUT_DIR/f"{code}_report.html"; df.to_csv(csv,index=False);df.to_html(html,index=False);print(f"Wrote {csv} and {html}")
def main():
    p=argparse.ArgumentParser(description="Election Market Tracker CLI"); sub=p.add_subparsers(dest="command",required=True)
    r=sub.add_parser("refresh");r.add_argument("--countries",default="all")
    q=sub.add_parser("report");q.add_argument("--country",required=True)
    args=p.parse_args(); countries=load_countries()
    if args.command=="refresh":refresh(list(countries) if args.countries=="all" else args.countries.split(","))
    else:report(args.country)
if __name__=="__main__":main()
