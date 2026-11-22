import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
LEXICON={"corruption":-2.5,"scandal":-2.0,"crisis":-2.0,"fraud":-2.5,"resignation":-1.5,"protest":-1.0,"violence":-2.5,"war":-3.0,"terrorism":-3.0,"victory":2.5,"landslide":2.5,"reform":1.5,"stability":1.5,"growth":1.5,"agreement":1.5,"peace":2.0}
def create_analyzer():
    analyzer=SentimentIntensityAnalyzer(); analyzer.lexicon.update(LEXICON); return analyzer
def classify_sentiment(score):
    return "positive" if score>=0.05 else "negative" if score<=-0.05 else "neutral"
def score_text(text, analyzer=None):
    analyzer=analyzer or create_analyzer(); score=analyzer.polarity_scores(str(text))["compound"]
    return {"sentiment":score,"sentiment_label":classify_sentiment(score)}
def score_news(df):
    if df is None or df.empty: return pd.DataFrame() if df is None else df.copy()
    analyzer=create_analyzer(); result=df.copy(); scores=result["title"].apply(lambda text: score_text(text,analyzer))
    result["sentiment"]=scores.map(lambda x:x["sentiment"]); result["sentiment_label"]=scores.map(lambda x:x["sentiment_label"]); return result
def aggregate_daily(df):
    if df is None or df.empty: return pd.DataFrame()
    x=df.copy(); x["published_at"]=pd.to_datetime(x["published_at"],utc=True,errors="coerce"); x=x.dropna(subset=["published_at"]); x["date"]=x["published_at"].dt.date
    return x.groupby("date").agg(sentiment_mean=("sentiment","mean"),sentiment_median=("sentiment","median"),positive_pct=("sentiment_label",lambda s:(s=="positive").mean()*100),negative_pct=("sentiment_label",lambda s:(s=="negative").mean()*100),n=("title","count")).reset_index()
