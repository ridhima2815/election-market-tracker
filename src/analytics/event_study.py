import numpy as np
import pandas as pd
from scipy import stats

def align_event_day(prices,event_date):
    idx=pd.to_datetime(prices.index).normalize(); event=pd.Timestamp(event_date).normalize(); candidates=idx[idx>=event]
    if not len(candidates): raise ValueError("No trading date on/after event")
    day=candidates[0]
    if (day-event).days>7: raise ValueError("Next available trading day is over 7 days away")
    return day

def market_model(asset_returns,market_returns):
    pair=pd.concat([asset_returns.rename("asset"),market_returns.rename("market")],axis=1).dropna()
    if len(pair)<30: return float(pair.asset.mean()) if len(pair) else 0.0,0.0
    beta,alpha,_,_,_=stats.linregress(pair.market,pair.asset)
    return float(alpha),float(beta)

def calculate_event_study(prices,market_prices,event_date,estimation_window=(-250,-30),event_windows=((-1,1),(-5,5),(0,10),(0,30))):
    asset=prices.copy(); market=market_prices.copy(); asset.index=pd.to_datetime(asset.index).normalize(); market.index=pd.to_datetime(market.index).normalize()
    ar=asset.Close.pct_change(); mr=market.Close.pct_change(); event=align_event_day(asset,event_date); loc=asset.index.get_loc(event)
    if not isinstance(loc,int): raise ValueError("Duplicate index dates")
    a=max(0,loc+estimation_window[0]); b=max(0,loc+estimation_window[1]); est=ar.iloc[a:b]; alpha,beta=market_model(est,mr.reindex(est.index))
    abnormal=ar-(alpha+beta*mr.reindex(ar.index)); windows={}
    for start,end in event_windows:
        lo=max(0,loc+start); hi=min(len(asset),loc+end+1); series=abnormal.iloc[lo:hi].dropna(); car=float(series.sum()); n=len(series)
        t=float(car/(series.std(ddof=1)*np.sqrt(n))) if n>1 and series.std(ddof=1)>0 else np.nan
        p=float(2*stats.t.sf(abs(t),n-1)) if n>1 and np.isfinite(t) else np.nan
        windows[f"{start}_{end}"]={"CAR":car,"t_stat":t,"p_value":p,"observations":n}
    pre=ar.iloc[max(0,loc-30):loc]; post=ar.iloc[loc:min(len(ar),loc+30)]
    return {"event_day":event,"alpha":alpha,"beta":beta,"windows":windows,"abnormal_returns":abnormal,"pre_volatility":float(pre.std()),"post_volatility":float(post.std())}
def average_car(results,window):
    values=[r["windows"][window]["CAR"] for r in results if window in r.get("windows",{})]
    return {"mean":float(np.mean(values)) if values else np.nan,"std":float(np.std(values,ddof=1)) if len(values)>1 else np.nan,"n":len(values)}
