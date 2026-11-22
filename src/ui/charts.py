import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def price_chart(prices, elections=None):
    fig = go.Figure()
    if prices is None or prices.empty:
        return fig
    y = prices.Close / prices.Close.iloc[0] * 100
    fig.add_trace(go.Scatter(x=y.index, y=y, mode="lines", name="Rebased index"))
    if elections is not None:
        for _, row in elections.iterrows():
            date = pd.Timestamp(row.event_date)
            if y.index.min() <= date <= y.index.max():
                fig.add_vline(x=date.timestamp() * 1000, line_dash="dash", annotation_text="Election")
    fig.update_layout(title="Index performance (start=100)", yaxis_title="Rebased value", template="plotly_white")
    return fig

def sentiment_chart(sentiment):
    if sentiment is None or sentiment.empty:
        return go.Figure()
    return px.line(sentiment, x="date", y="sentiment_mean", title="Daily headline sentiment").add_hline(y=0, line_dash="dash")

def car_chart(abnormal, event_day):
    if abnormal is None or abnormal.empty:
        return go.Figure()
    cum = abnormal.cumsum()
    fig = px.line(x=cum.index, y=cum.values, labels={"x": "Date", "y": "Cumulative abnormal return"}, title="Cumulative abnormal returns")
    fig.add_vline(x=pd.Timestamp(event_day).timestamp() * 1000, line_dash="dash")
    return fig

def country_map(countries, values=None):
    rows = [{"Country": c["name"], "Code": code, "Lat": c["latitude"], "Lon": c["longitude"], "Sentiment": (values or {}).get(code, 0)} for code, c in countries.items()]
    return px.scatter_geo(pd.DataFrame(rows), lat="Lat", lon="Lon", hover_name="Country", color="Sentiment", projection="natural earth", title="Country coverage")