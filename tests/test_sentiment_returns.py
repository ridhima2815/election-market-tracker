import pandas as pd
from src.analytics.sentiment_returns import analyze_sentiment_returns
def test_empty():
    result=analyze_sentiment_returns(pd.DataFrame(),pd.DataFrame());assert pd.isna(result["pearson"])
