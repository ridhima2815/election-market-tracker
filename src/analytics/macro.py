import pandas as pd
def trailing_return(prices,months=12):
    if prices is None or prices.empty:return None
    p=prices.sort_index(); target=p.index[-1]-pd.DateOffset(months=months); base=p.loc[p.index<=target]
    if base.empty:return None
    return float((p.Close.iloc[-1]/base.Close.iloc[-1]-1)*100)
def build_macro_table(data):
    return pd.DataFrame([{"Country":v["name"],"Inflation (%)":v.get("inflation"),"Inflation Year":v.get("inflation_year"),"12M Index Return (%)":v.get("return_12m")} for v in data.values()])
