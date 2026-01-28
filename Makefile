 .PHONY: install lint test type-check format scrape metrics

 install:
 	poetry install

 lint:
 	poetry run ruff check backend tests
 	poetry run black --check backend tests

 format:
 	poetry run black backend tests

 type-check:
 	poetry run mypy backend tests

 test:
 	poetry run pytest --cov=backend --cov-report=term-missing

 scrape:
 	poetry run python scripts/run_daily_scrape.py

 metrics:
 	poetry run python scripts/compute_metrics.py

