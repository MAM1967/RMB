"""
Entrypoint script for the daily scrape workflow.
"""

from __future__ import annotations

import argparse

from backend.src.config.settings import get_settings
from backend.src.db.client import get_supabase_client
from backend.src.logging_config import configure_logging, get_logger
from backend.src.scrapers.company_scraper import scrape_companies

logger = get_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run daily job scrape.")
    parser.add_argument(
        "--companies",
        nargs="*",
        help="Optional list of company IDs to scrape. Defaults to all companies with careers URLs.",
    )
    parser.add_argument(
        "--ats",
        choices=["ashby", "greenhouse", "lever", "all"],
        default="all",
        help="Filter by ATS platform (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of companies to scrape (for testing)",
    )
    return parser.parse_args()


def load_companies_from_db(ats_filter: str = "all", limit: int | None = None) -> list[str]:
    """Load company IDs from Supabase database."""
    settings = get_settings()
    supabase = get_supabase_client(settings)
    
    query = supabase.table("companies").select("id,ats,careers_url")
    
    # Filter by ATS platform
    if ats_filter != "all":
        query = query.eq("ats", ats_filter)
    
    # Only get companies with careers URLs
    query = query.not_.is_("careers_url", "null")
    
    result = query.execute()
    
    company_ids = [row["id"] for row in result.data if row.get("careers_url")]
    
    if limit:
        company_ids = company_ids[:limit]
    
    return company_ids


def main() -> None:
    configure_logging()
    args = parse_args()
    
    if args.companies:
        company_ids = args.companies
        logger.info("using_provided_companies", count=len(company_ids))
    else:
        company_ids = load_companies_from_db(ats_filter=args.ats, limit=args.limit)
        logger.info(
            "loaded_companies_from_db",
            count=len(company_ids),
            ats_filter=args.ats,
        )
    
    if not company_ids:
        logger.warning("no_companies_to_scrape")
        print("No companies found to scrape.")
        return
    
    print(f"Scraping {len(company_ids)} companies...")
    results = scrape_companies(company_ids)
    
    print(f"\n✅ Scraping complete!")
    print(f"   Companies processed: {results['companies_processed']}")
    print(f"   Total jobs inserted: {results['total_inserted']}")


 if __name__ == "__main__":
    main()

