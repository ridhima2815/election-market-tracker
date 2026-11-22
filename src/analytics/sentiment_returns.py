import numpy as np
import pandas as pd
from scipy import stats

def analyze_sentiment_returns(sentiment,prices,max_lag=5,minimum_observations=10):
    empty={"pearson":np.nan,"spearman":np.nan,"p_value":np.nan,"lag_results":{},"rolling":pd.DataFrame()}
    if sentiment is None or sentiment.empty or prices is None or prices.empty: return empty
    s=sentiment.copy(); s["date"]=pd.to_datetime(s.date); s=s.set_index("date"); p=prices.copy(); p.index=pd.to_datetime(p.index); returns=p.Close.pct_change()
    aligned=pd.concat([s.sentiment_mean,returns.shift(-1).rename("return")],axis=1).dropna()
    if len(aligned)<minimum_observations: return {**empty,"aligned":aligned}
    pr=stats.pearsonr(aligned.sentiment_mean,aligned["return"]); sr=stats.spearmanr(aligned.sentiment_mean,aligned["return"]); lags={}
    for lag in range(-max_lag,max_lag+1):
        pair=pd.concat([s.sentiment_mean,returns.shift(-lag).rename("return")],axis=1).dropna()
        if len(pair)<minimum_observations: lags[lag]={"correlation":np.nan,"p_value":np.nan,"n":len(pair)}
        else:
            test=stats.pearsonr(pair.iloc[:,0],pair.iloc[:,1]); lags[lag]={"correlation":float(test.statistic),"p_value":float(test.pvalue),"n":len(pair)}
    rolling=aligned.rolling(30).corr()
    return {"pearson":float(pr.statistic),"spearman":float(sr.statistic),"p_value":float(pr.pvalue),"lag_results":lags,"rolling":rolling,"aligned":aligned}
