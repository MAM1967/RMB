#!/usr/bin/env python3
"""
Test script to scrape a few companies and verify the pipeline works.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.src.config.settings import get_settings
from backend.src.db.client import get_supabase_client
from backend.src.logging_config import configure_logging, get_logger
from backend.src.scrapers.company_scraper import scrape_company

logger = get_logger()


def main():
    """Test scraping with a few sample companies."""
    configure_logging()
    
    settings = get_settings()
    supabase = get_supabase_client(settings)
    
    # Get a few test companies - one from each ATS platform
    test_companies = []
    
    for ats in ["ashby", "greenhouse", "lever"]:
        result = supabase.table("companies").select("id,name,ats").eq("ats", ats).limit(1).execute()
        if result.data:
            test_companies.append(result.data[0]["id"])
            print(f"Found {ats} company: {result.data[0]['id']} ({result.data[0]['name']})")
    
    if not test_companies:
        print("No test companies found!")
        return
    
    print(f"\nTesting scraper with {len(test_companies)} companies...\n")
    
    total_inserted = 0
    for company_id in test_companies:
        print(f"Scraping {company_id}...")
        inserted = scrape_company(company_id, settings)
        total_inserted += inserted
        print(f"  → Inserted {inserted} jobs\n")
    
    print(f"✅ Test complete! Total jobs inserted: {total_inserted}")


if __name__ == "__main__":
    main()
