from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.event_study import calculate_event_study
from src.analytics.macro import trailing_return
from src.analytics.sentiment_returns import analyze_sentiment_returns
from src.config import load_countries, load_elections, settings
from src.etl.demo_news import demo_news
from src.etl.inflation import get_inflation
from src.etl.news import fetch_news
from src.etl.prices import get_prices
from src.etl.sentiment import aggregate_daily, score_news
from src.storage import SQLiteStore
from src.ui.charts import car_chart, price_chart, sentiment_chart

INDEX_NAMES = {
    "IN": "Nifty 50",
    "US": "S&P 500",
    "GB": "FTSE 100",
    "JP": "Nikkei 225",
    "DE": "DAX",
    "FR": "CAC 40",
    "BR": "Ibovespa",
    "KR": "KOSPI",
}

st.set_page_config(page_title="Election & Market Tracker", page_icon="🌍", layout="wide")
st.title("🌍 Election & Market Sentiment Tracker")
st.caption("Political events, markets, inflation and news tone. Research tool—not investment advice.")

countries = load_countries()
elections = load_elections()
store = SQLiteStore()


def index_label(code):
    return countries[code].get("index_name") or INDEX_NAMES.get(code, countries[code]["ticker"])


st.sidebar.header("Filters")
selected = st.sidebar.multiselect("Countries", list(countries), default=["IN", "US", "GB"])
today = date.today()
start = st.sidebar.date_input("Start date", value=today - timedelta(days=365 * 5))
end = st.sidebar.date_input("End date", value=today)
if start >= end:
    st.error("Start date must precede end date.")
    st.stop()
if st.sidebar.button("Refresh cached data"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("DEMO_MODE=" + str(settings.DEMO_MODE))


@st.cache_data(ttl=settings.CACHE_TTL, show_spinner=False)
def load_country(code, start_s, end_s):
    c = countries[code]
    prices = get_prices(code, c["ticker"], start_s, end_s)
    inflation = get_inflation(c["iso3"])
    news_error = None
    fresh = pd.DataFrame()
    try:
        fresh = (
            demo_news(code, c["name"], start_s, end_s)
            if settings.DEMO_MODE
            else fetch_news(code, c["name"], c["news_locale"], settings.NEWS_LIMIT)
        )
        if not fresh.empty:
            fresh = score_news(fresh)
            try:
                store.save_headlines(fresh)
            except Exception as save_exc:
                news_error = f"Database save skipped: {save_exc}"
    except Exception as exc:
        news_error = str(exc)

    try:
        old = store.get_headlines(code)
    except Exception:
        old = pd.DataFrame()

    news = old if not old.empty else fresh
    if not news.empty:
        news = news.copy()
        news["published_at"] = pd.to_datetime(
            news["published_at"], utc=True, errors="coerce", format="mixed"
        )
        valid = news["published_at"].isna() | (
            news["published_at"] >= pd.Timestamp(start_s, tz="UTC")
        )
        news = news[valid].sort_values("published_at", ascending=False)
        daily = aggregate_daily(news.dropna(subset=["published_at"]))
    else:
        daily = pd.DataFrame()
    return prices, inflation, news, daily, news_error


loaded = {}
with st.spinner("Loading country datasets..."):
    for code in selected:
        try:
            loaded[code] = load_country(code, str(start), str(end))
        except Exception as e:
            loaded[code] = e

tabs = st.tabs(
    ["Overview", "Country Deep Dive", "Event Study", "Cross-Country Compare", "Methodology & Quality"]
)

with tabs[0]:
    items = list(loaded.items())
    for i in range(0, len(items), 4):
        row_items = items[i : i + 4]
        cols = st.columns(len(row_items))
        for col, (code, data) in zip(cols, row_items):
            with col:
                if isinstance(data, Exception):
                    st.error(f"{code}: {data}")
                    continue
                p, inf, _, _, _ = data
                tr = trailing_return(p)
                inf_val = f"{inf['value']:.2f}%" if inf["value"] is not None else "N/A"
                with st.container(border=True):
                    st.markdown(f"**{countries[code]['name']}** · {index_label(code)}")
                    st.metric(
                        "Latest Close",
                        f"{p.Close.iloc[-1]:,.2f}",
                        delta=f"{tr:+.2f}% (12M)" if tr is not None else None,
                    )
                    st.caption(f"Inflation: **{inf_val}** ({inf['source']} {inf['year']})")

    perf_frames = []
    for code, data in loaded.items():
        if isinstance(data, Exception):
            continue
        p = data[0]
        if p.empty:
            continue
        dates = p["Date"] if "Date" in p.columns else p.index
        rebased = (p["Close"] / p["Close"].iloc[0]) * 100
        perf_frames.append(
            pd.DataFrame(
                {
                    "Date": dates,
                    "Rebased Index (Start = 100)": rebased.values,
                    "Market": f"{countries[code]['name']} ({index_label(code)})",
                }
            )
        )
    if perf_frames:
        perf_df = pd.concat(perf_frames, ignore_index=True)
        fig_perf = px.line(
            perf_df,
            x="Date",
            y="Rebased Index (Start = 100)",
            color="Market",
            title="Stock Market Performance Comparison (Rebased to 100)",
        )
        fig_perf.update_layout(hovermode="x unified", legend_title_text="Index")
        st.plotly_chart(fig_perf, use_container_width=True, key="overview_perf")

    inf_rows = []
    for code, data in loaded.items():
        if isinstance(data, Exception):
            continue
        inf = data[1]
        if inf["value"] is not None:
            inf_rows.append(
                {
                    "Country": countries[code]["name"],
                    "Inflation (%)": inf["value"],
                    "Year": str(inf["year"]),
                }
            )
    if inf_rows:
        inf_df = pd.DataFrame(inf_rows).sort_values("Inflation (%)", ascending=False)
        fig_inf = px.bar(
            inf_df,
            x="Country",
            y="Inflation (%)",
            text="Inflation (%)",
            color="Inflation (%)",
            color_continuous_scale="Tealgrn",
            hover_data=["Year"],
            title="Annual CPI Inflation Rate by Country (%)",
        )
        fig_inf.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig_inf.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_inf, use_container_width=True, key="overview_inf")

with tabs[1]:
    if selected:
        code = st.selectbox("Country", selected, key="deep")
        data = loaded.get(code)
        if isinstance(data, Exception):
            st.error(str(data))
        elif data:
            p, inf, news, daily, news_error = data
            c = countries[code]
            a, b, d = st.columns(3)
            a.metric(f"{index_label(code)} ({c['ticker']})", f"{p.Close.iloc[-1]:,.2f}")
            tr = trailing_return(p)
            b.metric("Trailing 12M return", f"{tr:.2f}%" if tr is not None else "N/A")
            d.metric("Inflation", f"{inf['value']:.2f}%" if inf["value"] is not None else "N/A")
            st.plotly_chart(
                price_chart(p, elections[elections.country == code]),
                use_container_width=True,
                key=f"deep_dive_{code}",
            )
            if not daily.empty:
                st.plotly_chart(
                    sentiment_chart(daily),
                    use_container_width=True,
                    key=f"sentiment_{code}",
                )
                analysis = analyze_sentiment_returns(daily, p)
                x, y = st.columns(2)
                x.metric(
                    "Sentiment / next-day return Pearson",
                    f"{analysis['pearson']:.3f}" if pd.notna(analysis["pearson"]) else "N/A",
                )
                y.metric(
                    "Pearson p-value",
                    f"{analysis['p_value']:.3f}" if pd.notna(analysis["p_value"]) else "N/A",
                )
                if analysis.get("lag_results"):
                    lag_table = pd.DataFrame(analysis["lag_results"]).T
                    st.subheader("Sentiment-return lead/lag correlations")
                    st.dataframe(lag_table, use_container_width=True)
            st.subheader("Collected headlines")
            if not news.empty:
                st.dataframe(
                    news[["title", "published_at", "sentiment", "sentiment_label", "url"]].head(50),
                    use_container_width=True,
                    column_config={"url": st.column_config.LinkColumn("Article Link")},
                )
            elif news_error:
                st.warning(f"Could not fetch live headlines: {news_error}")
            else:
                st.info("No headlines found for the selected country and date range.")

with tabs[2]:
    if selected:
        code = st.selectbox("Event-study country", selected, key="event")
        ev = elections[elections.country == code].sort_values("event_date", ascending=False)
        if not ev.empty:
            idx = st.selectbox(
                "Election",
                ev.index,
                format_func=lambda i: (
                    f"{ev.loc[i, 'election_type']} — {ev.loc[i, 'event_date'].date()}"
                ),
            )
            row = ev.loc[idx]
            if not bool(row.verified):
                st.warning("Event date is unverified; interpret results cautiously.")
            if row.event_date.date() > date.today():
                st.info("Election has not occurred.")
            else:
                data = loaded.get(code)
                if isinstance(data, Exception):
                    st.error(str(data))
                elif data:
                    try:
                        market = get_prices("US", "^GSPC", str(start), str(end))
                        result = calculate_event_study(data[0], market, row.event_date)
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("Aligned Event Day", str(result["event_day"])[:10])
                        m2.metric(
                            "Alpha (α)",
                            f"{result['alpha']:.5f}" if pd.notna(result["alpha"]) else "N/A",
                            help="Baseline daily return from OLS market model ([-250, -30]).",
                        )
                        m3.metric(
                            "Beta (β)",
                            f"{result['beta']:.3f}" if pd.notna(result["beta"]) else "N/A",
                            help="Sensitivity of the index to the US S&P 500 benchmark.",
                        )
                        pre_v = result["pre_volatility"]
                        post_v = result["post_volatility"]
                        m4.metric(
                            "Pre-Event Vol (30D)",
                            f"{pre_v * 100:.2f}%" if pd.notna(pre_v) else "N/A",
                        )
                        vol_delta = (
                            f"{(post_v - pre_v) * 100:+.2f} pp"
                            if pd.notna(pre_v) and pd.notna(post_v)
                            else None
                        )
                        m5.metric(
                            "Post-Event Vol (30D)",
                            f"{post_v * 100:.2f}%" if pd.notna(post_v) else "N/A",
                            delta=vol_delta,
                            delta_color="inverse",
                        )
                        st.plotly_chart(
                            car_chart(result["abnormal_returns"], result["event_day"]),
                            use_container_width=True,
                            key=f"car_{code}_{idx}",
                        )
                        st.subheader("Event Window Statistics")
                        st.dataframe(pd.DataFrame(result["windows"]).T, use_container_width=True)
                    except Exception as exc:
                        st.error(f"Event study unavailable: {exc}")

with tabs[3]:
    rows = []
    for code, data in loaded.items():
        if isinstance(data, Exception):
            continue
        p, inf, news, _, _ = data
        rows.append(
            {
                "Country": countries[code]["name"],
                "Index": index_label(code),
                "Code": code,
                "Inflation (%)": inf["value"],
                "Inflation year": inf["year"],
                "12M return (%)": trailing_return(p),
                "Headline count": len(news),
            }
        )
    table = pd.DataFrame(rows)
    if not table.empty:
        st.dataframe(table, use_container_width=True)
        if table["Inflation (%)"].notna().any():
            st.plotly_chart(
                px.scatter(
                    table,
                    x="Inflation (%)",
                    y="12M return (%)",
                    text="Country",
                    title="Inflation vs trailing index return",
                ),
                use_container_width=True,
            )

with tabs[4]:
    st.markdown(
        """### Sentiment
VADER compound scores: positive >= 0.05; negative <= -0.05; otherwise neutral. Headlines are a noisy proxy for news tone, not public opinion.

### Event study
Event day is the first trading session on or after the supplied event date. The market model estimates alpha and beta using the pre-event estimation window [-250,-30]. AR = asset return - (alpha + beta × benchmark return); CAR is the sum of AR in the selected event window.

### Limitations
The default benchmark is the US S&P 500, which is not ideal for all countries. Election dates are not fully verified. Demo prices are synthetic. Correlation is not causation. News coverage and VADER language coverage vary across countries. This dashboard is not investment advice.
"""
    )
    st.subheader("Election data and verification")
    st.dataframe(elections, use_container_width=True)
    bad = elections[~elections["verified"].astype(bool)]
    if not bad.empty:
        st.warning("Verify unverified and placeholder election dates before research or publication.")
        st.dataframe(bad, use_container_width=True)