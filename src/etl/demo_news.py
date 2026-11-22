import pandas as pd

SAMPLE = [
    ("The government announced a new economic reform plan", 0.55),
    ("Opposition criticized the budget and called for accountability", -0.35),
    ("Markets welcomed the policy announcement", 0.42),
    ("Political leaders reached an agreement after negotiations", 0.30),
    ("Officials faced questions over a corruption investigation", -0.62),
    ("Election commission published updated voting guidance", 0.05),
    ("Protests continued amid political uncertainty", -0.45),
    ("The ruling coalition reported a strong electoral victory", 0.70),
]

def demo_news(country_code, country_name, start, end):
    dates = pd.date_range(start, end, freq="D")
    rows=[]
    if not len(dates): return pd.DataFrame()
    for i, day in enumerate(dates[-min(len(dates), 120):]):
        title, score = SAMPLE[i % len(SAMPLE)]
        rows.append({"country":country_code,"title":f"{country_name}: {title}","url":f"https://demo.invalid/{country_code}/{i}","published_at":pd.Timestamp(day,tz="UTC"),"source":"Demo fixture","sentiment":score,"sentiment_label":"positive" if score>=.05 else "negative" if score<=-.05 else "neutral"})
    return pd.DataFrame(rows)
