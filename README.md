# Election & Market Sentiment Tracker

Streamlit analytics dashboard for election calendars, market indices, inflation and news sentiment across India, the United States, United Kingdom, Japan, Germany, France, Brazil and South Korea.

## Features
- Election calendar with verified/unverified flags
- Country overview and interactive map
- Yahoo Finance index prices, rebased charts and event markers
- World Bank CPI inflation series
- Google News RSS headline collection and SQLite persistence
- VADER sentiment scores with a small political lexicon
- Market-model event study and CAR windows
- Sentiment-return correlations and lag analysis module
- CLI refresh and CSV/HTML report exports
- Demo mode, Docker, tests and GitHub workflows

## Install
Python 3.11 recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Demo mode is enabled by default. It uses deterministic synthetic prices; live news is attempted if network access is available. To use live market prices and World Bank data, set `DEMO_MODE=0` in `.env` and restart.

## CLI
```bash
python -m src.cli refresh --countries all
python -m src.cli refresh --countries IN,US,GB
python -m src.cli report --country IN
pytest -v
ruff check .
```
Reports are saved in `outputs/`.

## Docker
```bash
docker build -t election-market-tracker .
docker run --rm -p 8501:8501 election-market-tracker
```
Open http://localhost:8501.

## Methodology
Daily simple returns are calculated from adjusted prices. Event day is the first trading session on or after an election date. The market model estimates alpha and beta in the [-250,-30] trading-day estimation window where available; with fewer than 30 aligned observations it uses a constant-mean fallback. Abnormal return is `asset return - (alpha + beta * benchmark return)`. CAR is the sum of abnormal returns over [-1,+1], [-5,+5], [0,+10] and [0,+30]. The current default benchmark in the dashboard is the S&P 500 for all countries, a limitation; use local/country-appropriate benchmarks for research.

VADER compound sentiment thresholds: positive >= 0.05, negative <= -0.05, neutral otherwise. Headline tone is not public opinion and sentiment correlation is not causal inference.

## Election data quality
The CSV contains some deliberately unverified placeholder future dates and records requiring verification. Confirm all rows against official election authorities before research/publication. Do not interpret placeholder dates as confirmed election schedules.

## Limitations
- Synthetic demo prices are not historical observations.
- The default S&P 500 benchmark is not appropriate for every country.
- News RSS coverage and language quality vary.
- VADER is not a specialist political-finance model.
- Event studies can be confounded by other news/events.
- The dashboard is not financial advice.
