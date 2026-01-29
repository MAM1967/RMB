#!/usr/bin/env python3
"""
Simple migration script to import CSV data into Supabase.
Uses Supabase client directly without backend package dependencies.
"""

import csv
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client

# Load environment from project root
base_dir = Path(__file__).parent.parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=str(env_path), override=True)


def detect_ats_platform(careers_url: Optional[str]) -> str:
    """Detect ATS platform from careers URL pattern."""
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
    """Convert company name to a slug suitable for use as company_id."""
    slug = company_name.lower().strip()
    for char in [" ", ".", ",", "&", "/", "(", ")"]:
        slug = slug.replace(char, "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    return slug


def main():
    """Main migration entrypoint."""
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print(
            "\nERROR: Missing Supabase credentials."
            "\nPlease set in your .env file:"
            "\n  SUPABASE_URL=https://your-project.supabase.co"
            "\n  SUPABASE_KEY=your-anon-key"
            "\n\nYou can find these in your Supabase project settings under API."
        )
        sys.exit(1)
    
    # Create Supabase client
    print(f"Connecting to Supabase at: {supabase_url}")
    try:
        supabase = create_client(supabase_url, supabase_key)
        # Test connection
        test_result = supabase.table("companies").select("id").limit(1).execute()
        print("✓ Successfully connected to Supabase")
    except Exception as e:
        print(f"✗ Failed to connect to Supabase: {e}")
        print(f"  URL: {supabase_url}")
        print(f"  Key (first 20 chars): {supabase_key[:20]}...")
        sys.exit(1)
    
    # Load CSV files
    base_dir = Path(__file__).parent.parent
    companies_csv = base_dir / "companies.csv"
    ats_results_csv = base_dir / "ats_scan_results.csv"
    
    if not companies_csv.exists():
        print(f"ERROR: {companies_csv} not found")
        sys.exit(1)
    
    if not ats_results_csv.exists():
        print(f"ERROR: {ats_results_csv} not found")
        sys.exit(1)
    
    # Load companies data
    companies_data = {}
    with open(companies_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle column names with/without leading spaces
            domain = (row.get("domain") or row.get(" domain", "")).strip()
            company_name = (row.get("company_name") or row.get("company_name", "")).strip()
            sector = (row.get("sector") or row.get(" sector", "")).strip()
            estimated_size = (row.get("estimated_size") or row.get(" estimated_size", "")).strip()
            
            if not domain or not company_name:
                continue
            
            # Skip header rows (check if domain or company_name is literally "domain" or "company_name")
            if domain.lower() == "domain" or company_name.lower() == "company_name":
                continue
            
            companies_data[domain] = {
                "company_name": company_name,
                "domain": domain,
                "sector": sector,
                "estimated_size": estimated_size,
            }
    
    # Load ATS results
    ats_results = {}
    with open(ats_results_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row.get("domain", "").strip()
            if not domain:
                continue
            
            ats_results[domain] = {
                "careers_url": row.get("careers_url", "").strip() or None,
                "status": row.get("status", "").strip(),
                "pattern_matched": row.get("pattern_matched", "").strip() or None,
            }
    
    print(f"Loaded {len(companies_data)} companies and {len(ats_results)} ATS results")
    
    # Prepare batch for insertion
    batch = []
    skipped = 0
    
    for domain, company_info in companies_data.items():
        ats_info = ats_results.get(domain, {})
        careers_url = ats_info.get("careers_url")
        
        # Only insert companies that have a careers_url (FOUND status)
        if ats_info.get("status") != "FOUND" or not careers_url:
            skipped += 1
            continue
        
        ats_platform = detect_ats_platform(careers_url)
        company_id = slugify_company_id(company_info["company_name"])
        company_name = company_info["company_name"]
        
        batch.append({
            "id": company_id,
            "name": company_name,
            "ats": ats_platform,
            "careers_url": careers_url,
        })
    
    print(f"Prepared {len(batch)} companies for migration ({skipped} skipped - no careers URL)")
    
    # Batch upsert companies (100 at a time)
    inserted = 0
    for i in range(0, len(batch), 100):
        chunk = batch[i:i+100]
        try:
            result = supabase.table("companies").upsert(
                chunk,
                on_conflict="id",
            ).execute()
            
            inserted += len(chunk)
            print(f"  ✓ Inserted batch {i//100 + 1} ({len(chunk)} companies)")
        
        except Exception as e:
            print(f"  ✗ Error inserting batch {i//100 + 1}: {e}")
            # Try individual inserts for this batch
            for company in chunk:
                try:
                    supabase.table("companies").upsert(
                        company,
                        on_conflict="id",
                    ).execute()
                    inserted += 1
                except Exception as e2:
                    print(f"    ✗ Failed to insert {company.get('id')}: {e2}")
    
    print(f"\n✅ Migration complete! Inserted/updated {inserted} companies.")


if __name__ == "__main__":
    main()
