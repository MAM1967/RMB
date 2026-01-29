#!/usr/bin/env python3
"""
Scrape all Ashby companies using GraphQL API.
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from supabase import create_client

# Load environment
base_dir = Path(__file__).parent.parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=str(env_path), override=True)


def classify_job_function(title: str) -> Optional[str]:
    """Classify job function."""
    normalized = title.lower()
    if any(kw in normalized for kw in ["operations", "supply chain", "logistics", "program manager", "process", " ops"]):
        return "operations"
    if any(kw in normalized for kw in ["finance", "accounting", "treasury", "fp&a", "controller", "audit"]):
        return "finance"
    if any(kw in normalized for kw in ["sales", "revenue", "gtm", "growth", "business development", "account exec", "partnerships", "customer success"]):
        return "gtm"
    if any(kw in normalized for kw in ["product", "pm", "product manager"]):
        return "product"
    if any(kw in normalized for kw in ["people", "hr", "human resources", "talent", "recruiting"]):
        return "people"
    if any(kw in normalized for kw in ["engineer", "software", "technical", "infrastructure", "developer", "devops"]):
        return "engineering"
    if any(kw in normalized for kw in ["marketing", "brand", "communications", "content"]):
        return "marketing"
    return None


def classify_job_level(title: str) -> Optional[str]:
    """Classify job level."""
    normalized = title.lower()
    if any(kw in normalized for kw in ["chief", "ceo", "cfo", "coo", "cto", "cmo", "c-level", "c suite"]):
        return "c-level"
    if any(kw in normalized for kw in ["senior vice president", "svp", "sr vp"]):
        return "svp"
    if any(kw in normalized for kw in ["vice president", "vp", "v.p."]):
        return "vp"
    if any(kw in normalized for kw in ["director", "dir.", "head of"]):
        return "director"
    return None


def scrape_ashby_company(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """Scrape Ashby jobs using GraphQL API."""
    jobs = []
    
    if "jobs.ashbyhq.com" not in careers_url:
        return jobs
    
    company_slug = careers_url.split("jobs.ashbyhq.com/")[-1].split("/")[0].split("?")[0]
    
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql"
    graphql_query = {
        "query": """
        query GetJobBoard($organizationHostedJobsPageName: String!) {
          jobBoardWithTeams(organizationHostedJobsPageName: $organizationHostedJobsPageName) {
            jobPostings {
              id
              title
              locationName
              locationAddress
              workplaceType
            }
          }
        }
        """,
        "variables": {"organizationHostedJobsPageName": company_slug},
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "RecruiterMarketBrief/1.0",
        "Origin": "https://jobs.ashbyhq.com",
        "Referer": careers_url,
    }
    
    try:
        response = requests.post(api_url, json=graphql_query, headers=headers, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 429:
            time.sleep(2)  # Wait and retry once
            response = requests.post(api_url, json=graphql_query, headers=headers, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        
        # Handle rate limit error in response
        if "error" in data and "rate limit" in data["error"].lower():
            return jobs
        
        if "errors" in data:
            return jobs
        
        data_obj = data.get("data")
        if not data_obj:
            return jobs
        
        job_board = data_obj.get("jobBoardWithTeams")
        if job_board is None:
            # Company might not have public job board or slug is wrong
            return jobs
        
        job_postings = job_board.get("jobPostings", [])
        
        for job in job_postings:
            job_id = job.get("id", "")
            if not job_id:
                continue
            
            job_url = f"{careers_url}/{job_id}"
            location_raw = job.get("locationName") or job.get("locationAddress") or ""
            workplace_type = job.get("workplaceType", "").lower() if job.get("workplaceType") else ""
            is_remote = workplace_type in ["remote", "hybrid"] or "remote" in location_raw.lower()
            title = job.get("title", "")
            
            jobs.append({
                "source_job_id": str(job_id),
                "company_id": company_id,
                "title": title,
                "url": job_url,
                "first_seen": datetime.utcnow().isoformat(),
                "location_city": None,
                "location_state": None,
                "is_remote": is_remote,
                "source_url": careers_url,
                "scraped_at": datetime.utcnow().isoformat(),
                "function": classify_job_function(title),
                "level": classify_job_level(title),
            })
    
    except Exception:
        pass
    
    return jobs


def scrape_company(company: dict, supabase: Any) -> tuple[str, int]:
    """Scrape a single company."""
    company_id = company["id"]
    careers_url = company["careers_url"]
    
    print(f"Scraping {company_id}...", end=" ", flush=True)
    
    jobs = scrape_ashby_company(careers_url, company_id)
    
    if not jobs:
        print("0 jobs")
        return company_id, 0
    
    try:
        supabase.table("job_postings").upsert(
            jobs,
            on_conflict="source_job_id,company_id",
        ).execute()
        print(f"✓ {len(jobs)} jobs")
        return company_id, len(jobs)
    except Exception as e:
        print(f"✗ Error: {e}")
        return company_id, 0


def main():
    """Main scraping function."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all Ashby companies
    result = supabase.table("companies").select("id,name,careers_url").eq("ats", "ashby").not_.is_("careers_url", "null").execute()
    
    companies = result.data
    print(f"Found {len(companies)} Ashby companies to scrape\n")
    
    if not companies:
        print("No companies found!")
        return
    
    # Scrape with limited parallelism (max 3 concurrent to avoid rate limits) and delays
    total_jobs = 0
    successful = 0
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scrape_company, company, supabase): company for company in companies}
        
        for i, future in enumerate(as_completed(futures)):
            company_id, jobs_inserted = future.result()
            if jobs_inserted > 0:
                successful += 1
            total_jobs += jobs_inserted
            
            # Add delay between requests to avoid rate limiting (every 5 requests)
            if (i + 1) % 5 == 0:
                time.sleep(1)
    
    print(f"\n✅ Scraping complete!")
    print(f"   Companies processed: {len(companies)}")
    print(f"   Companies with jobs: {successful}")
    print(f"   Total jobs inserted: {total_jobs}")


if __name__ == "__main__":
    main()
