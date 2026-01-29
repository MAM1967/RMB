"""
Migration script to import CSV data into Supabase.

This script migrates:
1. Companies data from companies.csv + ats_scan_results.csv
2. Job postings (if available in future CSV files)
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.src.config.settings import get_settings
from backend.src.db.client import get_supabase_client
from backend.src.logging_config import configure_logging, get_logger

logger = get_logger()

# Load environment
load_dotenv()


def detect_ats_platform(careers_url: str | None) -> str:
    """
    Detect ATS platform from careers URL pattern.
    
    Returns: 'ashby', 'greenhouse', 'lever', 'workday', or 'unknown'
    """
    if not careers_url:
        return "unknown"
    
    url_lower = careers_url.lower()
    
    if "ashbyhq.com" in url_lower or "ashby" in url_lower:
        return "ashby"
    elif "greenhouse.io" in url_lower or "boards.greenhouse.io" in url_lower:
        return "greenhouse"
    elif "lever.co" in url_lower or "jobs.lever.co" in url_lower:
        return "lever"
    elif "workday" in url_lower or "myworkdayjobs.com" in url_lower:
        return "workday"
    else:
        return "unknown"


def slugify_company_id(company_name: str) -> str:
    """
    Convert company name to a slug suitable for use as company_id.
    
    Examples:
    - "JPMorgan Chase" -> "jpmorgan-chase"
    - "Bank of America" -> "bank-of-america"
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = company_name.lower().strip()
    # Replace common separators
    for char in [" ", ".", ",", "&", "/", "(", ")"]:
        slug = slug.replace(char, "-")
    # Remove multiple consecutive hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def load_companies_csv(csv_path: Path) -> dict[str, dict[str, Any]]:
    """
    Load companies.csv and return a dict keyed by domain.
    
    Returns: {domain: {company_name, domain, sector, estimated_size}}
    """
    companies = {}
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle different possible column name variations
            domain = row.get("domain", "").strip()
            company_name = row.get("company_name", "").strip()
            
            # Skip if domain or company_name is missing, or if it's a duplicate header row
            if not domain or not company_name:
                continue
            
            # Skip if domain looks like a header (contains "domain" or is empty)
            if domain.lower() == "domain" or company_name.lower() == "company_name":
                continue
            
            companies[domain] = {
                "company_name": company_name,
                "domain": domain,
                "sector": row.get("sector", "").strip(),
                "estimated_size": row.get("estimated_size", "").strip(),
            }
    
    return companies


def load_ats_results_csv(csv_path: Path) -> dict[str, dict[str, Any]]:
    """
    Load ats_scan_results.csv and return a dict keyed by domain.
    
    Returns: {domain: {careers_url, status, pattern_matched}}
    """
    results = {}
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row.get("domain", "").strip()
            
            if not domain:
                continue
            
            results[domain] = {
                "careers_url": row.get("careers_url", "").strip() or None,
                "status": row.get("status", "").strip(),
                "pattern_matched": row.get("pattern_matched", "").strip() or None,
            }
    
    return results


def migrate_companies(supabase, companies_data: dict, ats_results: dict) -> int:
    """
    Migrate companies data to Supabase companies table.
    
    Returns: Number of companies inserted/updated
    """
    inserted = 0
    updated = 0
    batch = []
    
    for domain, company_info in companies_data.items():
        ats_info = ats_results.get(domain, {})
        careers_url = ats_info.get("careers_url")
        ats_platform = detect_ats_platform(careers_url)
        
        # Use domain as company_id, or create slug from company_name
        company_id = slugify_company_id(company_info["company_name"])
        company_name = company_info["company_name"]
        
        # Only insert companies that have a careers_url (FOUND status)
        if ats_info.get("status") != "FOUND" or not careers_url:
            logger.debug(
                "skipping_company",
                domain=domain,
                reason="no_careers_url" if not careers_url else "not_found",
            )
            continue
        
        batch.append({
            "id": company_id,
            "name": company_name,
            "ats": ats_platform,
            "careers_url": careers_url,
        })
    
    # Batch upsert companies (100 at a time)
    for i in range(0, len(batch), 100):
        chunk = batch[i:i+100]
        try:
            result = supabase.table("companies").upsert(
                chunk,
                on_conflict="id",
            ).execute()
            
            inserted += len(chunk)
            logger.info(
                "companies_batch_upserted",
                batch_size=len(chunk),
                total_inserted=inserted,
            )
        
        except Exception as e:
            logger.error(
                "companies_batch_error",
                batch_start=i,
                error=str(e),
            )
            # Try individual inserts for this batch
            for company in chunk:
                try:
                    supabase.table("companies").upsert(
                        company,
                        on_conflict="id",
                    ).execute()
                    inserted += 1
                except Exception as e2:
                    logger.error(
                        "company_migration_error",
                        company_id=company.get("id"),
                        error=str(e2),
                    )
    
    logger.info(
        "companies_migration_complete",
        inserted=inserted,
        total=len(companies_data),
    )
    
    return inserted




def main() -> None:
    """Main migration entrypoint."""
    configure_logging()
    
    logger.info("csv_migration_started")
    
    # Get settings and Supabase client
    settings = get_settings()
    
    try:
        supabase = get_supabase_client(settings)
    except Exception as e:
        logger.error("supabase_connection_error", error=str(e))
        print(
            "\nERROR: Could not connect to Supabase."
            "\nPlease ensure your .env file has:"
            "\n  SUPABASE_URL=https://your-project.supabase.co"
            "\n  SUPABASE_KEY=your-anon-key"
        )
        sys.exit(1)
    
    # Load CSV files
    base_dir = Path(__file__).parent.parent
    companies_csv = base_dir / "companies.csv"
    ats_results_csv = base_dir / "ats_scan_results.csv"
    
    if not companies_csv.exists():
        logger.error("csv_file_not_found", file=str(companies_csv))
        print(f"ERROR: {companies_csv} not found")
        sys.exit(1)
    
    if not ats_results_csv.exists():
        logger.error("csv_file_not_found", file=str(ats_results_csv))
        print(f"ERROR: {ats_results_csv} not found")
        sys.exit(1)
    
    # Load data
    logger.info("loading_csv_files")
    companies_data = load_companies_csv(companies_csv)
    ats_results = load_ats_results_csv(ats_results_csv)
    
    logger.info(
        "csv_data_loaded",
        companies_count=len(companies_data),
        ats_results_count=len(ats_results),
    )
    
    # Migrate companies
    inserted = migrate_companies(supabase, companies_data, ats_results)
    
    logger.info("csv_migration_complete", companies_inserted=inserted)
    print(f"\n✅ Migration complete! Inserted/updated {inserted} companies.")


if __name__ == "__main__":
    main()
