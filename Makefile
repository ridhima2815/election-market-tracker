.PHONY: install run demo refresh report test lint format docker docker-run
install:
	pip install -r requirements.txt
run:
	streamlit run app.py
demo:
	DEMO_MODE=1 streamlit run app.py
refresh:
	python -m src.cli refresh --countries all
report:
	python -m src.cli report --country IN
test:
	pytest -v
lint:
	ruff check .
format:
	black .
docker:
	docker build -t election-market-tracker .
docker-run:
	docker run -p 8501:8501 election-market-tracker
