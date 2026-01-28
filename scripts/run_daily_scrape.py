 """
 Entrypoint script for the daily scrape workflow.
 """

 from __future__ import annotations

 import argparse

 from backend.src.config.settings import CONFIG_DIR
 from backend.src.logging_config import configure_logging
 from backend.src.scrapers.company_scraper import scrape_companies


 def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run daily job scrape.")
    parser.add_argument(
        "--companies",
        nargs="*",
        help="Optional list of company IDs to scrape. Defaults to config file.",
    )
    return parser.parse_args()


 def load_default_companies() -> list[str]:
    # Lazy import to avoid mandatory dependency at import time
    import json  # noqa: WPS433

    companies_path = CONFIG_DIR / "companies.json"
    with companies_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [c["id"] for c in raw.get("companies", [])]


 def main() -> None:
    configure_logging()
    args = parse_args()
    company_ids = args.companies or load_default_companies()
    scrape_companies(company_ids)


 if __name__ == "__main__":
    main()

