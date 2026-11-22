import numpy as np
import pandas as pd
from src.analytics.event_study import align_event_day,market_model
def test_alignment():
    p=pd.DataFrame({"Close":[1,2,3]},index=pd.to_datetime(["2024-01-01","2024-01-03","2024-01-04"]));assert align_event_day(p,"2024-01-02")==pd.Timestamp("2024-01-03")
def test_market_model():
    rng=np.random.default_rng(2);m=pd.Series(rng.normal(0,.01,200));a=.001+1.5*m+rng.normal(0,.001,200);alpha,beta=market_model(a,m);assert abs(beta-1.5)<.1;assert abs(alpha-.001)<.002
