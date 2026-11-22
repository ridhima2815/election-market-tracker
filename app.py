from datetime import date,timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import load_countries,load_elections,settings
from src.storage import SQLiteStore
from src.etl.prices import get_prices
from src.etl.inflation import get_inflation
from src.etl.news import fetch_news
from src.etl.demo_news import demo_news
from src.etl.sentiment import score_news,aggregate_daily
from src.analytics.event_study import calculate_event_study
from src.analytics.sentiment_returns import analyze_sentiment_returns
from src.analytics.macro import trailing_return
from src.ui.charts import price_chart,sentiment_chart,car_chart,country_map

st.set_page_config(page_title="Election & Market Tracker",page_icon="🌍",layout="wide")
st.title("🌍 Election & Market Sentiment Tracker")
st.caption("Political events, markets, inflation and news tone. Research tool—not investment advice.")
countries=load_countries(); elections=load_elections(); store=SQLiteStore()
st.sidebar.header("Filters")
selected=st.sidebar.multiselect("Countries",list(countries),default=["IN","US","GB"])
end=date.today(); start=st.sidebar.date_input("Start date",value=end-timedelta(days=365*5)); end=st.sidebar.date_input("End date",value=end)
if start>=end: st.error("Start date must precede end date."); st.stop()
if st.sidebar.button("Refresh cached data"):
    st.cache_data.clear(); st.rerun()
st.sidebar.caption("DEMO_MODE="+str(settings.DEMO_MODE))

@st.cache_data(ttl=settings.CACHE_TTL,show_spinner=False)
def load_country(code,start_s,end_s):
    c=countries[code]; prices=get_prices(code,c["ticker"],start_s,end_s); inflation=get_inflation(c["iso3"])
    try:
        fresh=demo_news(code,c["name"],start_s,end_s) if settings.DEMO_MODE else fetch_news(code,c["name"],c["news_locale"],settings.NEWS_LIMIT)
        if not fresh.empty: fresh=score_news(fresh); store.save_headlines(fresh)
    except Exception: fresh=pd.DataFrame()
    old=store.get_headlines(code)
    news=old
    if not news.empty:
        news["published_at"]=pd.to_datetime(news.published_at,utc=True,errors="coerce")
        news=news[news.published_at>=pd.Timestamp(start_s,tz="UTC")]
        daily=aggregate_daily(news)
    else: daily=pd.DataFrame()
    return prices,inflation,news,daily

loaded={}
with st.spinner("Loading country datasets..."):
    for code in selected:
        try: loaded[code]=load_country(code,str(start),str(end))
        except Exception as e: loaded[code]=e

tabs=st.tabs(["Overview","Country Deep Dive","Event Study","Cross-Country Compare","Methodology & Quality"])
with tabs[0]:
    st.plotly_chart(country_map(countries),use_container_width=True)
    cols=st.columns(max(1,len(loaded)))
    for col,(code,data) in zip(cols,loaded.items()):
        with col:
            if isinstance(data,Exception):st.error(f"{code}: {data}");continue
            p,inf,news,daily=data
            st.metric(countries[code]["name"],f"{p.Close.iloc[-1]:,.2f}")
            st.metric("Inflation",f"{inf['value']:.2f}%" if inf["value"] is not None else "N/A",help=f"Source/year: {inf['source']} / {inf['year']}")
    for code,data in loaded.items():
        if isinstance(data,Exception):continue
        st.subheader(countries[code]["name"]); st.plotly_chart(price_chart(data[0],elections[elections.country==code]),use_container_width=True)
with tabs[1]:
    if selected:
        code=st.selectbox("Country",selected,key="deep"); data=loaded.get(code)
        if isinstance(data,Exception):st.error(str(data))
        elif data:
            p,inf,news,daily=data; c=countries[code]
            a,b,d=st.columns(3); a.metric("Latest index",f"{p.Close.iloc[-1]:,.2f}"); tr=trailing_return(p); b.metric("Trailing 12M return",f"{tr:.2f}%" if tr is not None else "N/A"); d.metric("Inflation",f"{inf['value']:.2f}%" if inf["value"] is not None else "N/A")
            st.plotly_chart(price_chart(p,elections[elections.country==code]),use_container_width=True,key=f"deep_dive_{code}")
            if not daily.empty:
                st.plotly_chart(sentiment_chart(daily),use_container_width=True)
                analysis=analyze_sentiment_returns(daily,p)
                x,y=st.columns(2); x.metric("Sentiment / next-day return Pearson", f"{analysis['pearson']:.3f}" if pd.notna(analysis['pearson']) else "N/A"); y.metric("Pearson p-value", f"{analysis['p_value']:.3f}" if pd.notna(analysis['p_value']) else "N/A")
                if analysis.get("lag_results"):
                    lag_table=pd.DataFrame(analysis["lag_results"]).T; st.subheader("Sentiment-return lead/lag correlations"); st.dataframe(lag_table,use_container_width=True)
            st.subheader("Collected headlines")
            if not news.empty: st.dataframe(news[["title","published_at","sentiment","sentiment_label","url"]].head(50),use_container_width=True)
            else: st.info("No headlines in database for selected range.")
with tabs[2]:
    if selected:
        code=st.selectbox("Event-study country",selected,key="event"); ev=elections[elections.country==code].sort_values("event_date",ascending=False)
        if not ev.empty:
            idx=st.selectbox("Election",ev.index,format_func=lambda i:f"{ev.loc[i,'election_type']} — {ev.loc[i,'event_date'].date()}")
            row=ev.loc[idx]
            if not bool(row.verified):st.warning("Event date is unverified; interpret results cautiously.")
            if row.event_date.date()>date.today():st.info("Election has not occurred.")
            else:
                data=loaded.get(code)
                if isinstance(data,Exception):st.error(str(data))
                elif data:
                    try:
                        market=get_prices("US","^GSPC",str(start),str(end)); result=calculate_event_study(data[0],market,row.event_date)
                        st.write({"event_day":str(result["event_day"]),"alpha":result["alpha"],"beta":result["beta"],"pre_volatility":result["pre_volatility"],"post_volatility":result["post_volatility"]})
                        st.plotly_chart(car_chart(result["abnormal_returns"],result["event_day"]),use_container_width=True); st.dataframe(pd.DataFrame(result["windows"]).T,use_container_width=True)
                    except Exception as exc:st.error(f"Event study unavailable: {exc}")
with tabs[3]:
    rows=[]
    for code,data in loaded.items():
        if isinstance(data,Exception):continue
        p,inf,news,daily=data; rows.append({"Country":countries[code]["name"],"Code":code,"Inflation (%)":inf["value"],"Inflation year":inf["year"],"12M return (%)":trailing_return(p),"Headline count":len(news)})
    table=pd.DataFrame(rows)
    if not table.empty:
        st.dataframe(table,use_container_width=True)
        if table["Inflation (%)"].notna().any():st.plotly_chart(px.scatter(table,x="Inflation (%)",y="12M return (%)",text="Country",title="Inflation vs trailing index return"),use_container_width=True)
with tabs[4]:
    st.markdown("""### Sentiment
VADER compound scores: positive >= 0.05; negative <= -0.05; otherwise neutral. Headlines are a noisy proxy for news tone, not public opinion.

### Event study
Event day is the first trading session on or after the supplied event date. The market model estimates alpha and beta using the pre-event estimation window [-250,-30]. AR = asset return - (alpha + beta × benchmark return); CAR is the sum of AR in the selected event window.

### Limitations
The default benchmark is the US S&P 500, which is not ideal for all countries. Election dates are not fully verified. Demo prices are synthetic. Correlation is not causation. News coverage and VADER language coverage vary across countries. This dashboard is not investment advice.
""")
    st.subheader("Election data and verification")
    st.dataframe(elections,use_container_width=True)
    bad=elections[elections.verified==False]
    if not bad.empty:st.warning("Verify unverified and placeholder election dates before research or publication.");st.dataframe(bad,use_container_width=True)
