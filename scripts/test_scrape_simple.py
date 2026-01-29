#!/usr/bin/env python3
"""
Simple test script to scrape a few companies and verify the pipeline works.
Uses direct imports without backend package structure.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

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


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def scrape_ashby_jobs(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """Scrape Ashby jobs."""
    jobs = []
    
    if "jobs.ashbyhq.com" not in careers_url:
        print(f"  ⚠ Invalid Ashby URL: {careers_url}")
        return jobs
    
    company_slug = careers_url.split("jobs.ashbyhq.com/")[-1].split("/")[0].split("?")[0]
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql"
    
    # Ashby uses a different API structure - try the public jobs endpoint
    # Many Ashby sites expose jobs at: https://jobs.ashbyhq.com/{slug}/api/non-user/board
    api_url = f"https://jobs.ashbyhq.com/{company_slug}/api/non-user/board"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "RecruiterMarketBrief/1.0",
        "Origin": f"https://jobs.ashbyhq.com/{company_slug}",
        "Referer": careers_url,
    }
    
    try:
        # Try the board API endpoint (REST, not GraphQL)
        response = requests.get(api_url, headers={"User-Agent": "RecruiterMarketBrief/1.0"}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response structures
        job_postings = []
        if isinstance(data, list):
            job_postings = data
        elif isinstance(data, dict):
            job_postings = data.get("jobPostings", data.get("jobs", data.get("results", [])))
        
        for job in job_postings:
            published_at = job.get("publishedAt") or job.get("published_at") or job.get("createdAt")
            if published_at:
                try:
                    if isinstance(published_at, (int, float)):
                        first_seen = datetime.fromtimestamp(published_at / 1000 if published_at > 1e10 else published_at)
                    else:
                        first_seen = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
                except Exception:
                    first_seen = datetime.utcnow()
            else:
                first_seen = datetime.utcnow()
            
            job_id = job.get("id") or job.get("_id") or job.get("jobId")
            job_url = job.get("url") or job.get("jobUrl") or job.get("applicationUrl") or f"{careers_url}/{job_id}"
            if not job_url.startswith("http"):
                job_url = f"https://jobs.ashbyhq.com/{company_slug}/{job_id}"
            
            location_raw = job.get("locationName") or job.get("location_name") or job.get("location") or ", ".join(job.get("locations", [])) or ""
            is_remote = job.get("isRemote", False) or job.get("is_remote", False) or "remote" in location_raw.lower()
            
            jobs.append({
                "source_job_id": str(job_id) if job_id else "",
                "company_id": company_id,
                "title": job.get("title") or job.get("name") or "",
                "url": job_url,
                "first_seen": first_seen.isoformat(),
                "location_city": None,
                "location_state": None,
                "is_remote": is_remote,
                "source_url": careers_url,
                "scraped_at": datetime.utcnow().isoformat(),
                "function": classify_job_function(job.get("title") or job.get("name") or ""),
                "level": classify_job_level(job.get("title") or job.get("name") or ""),
            })
        
        print(f"  ✓ Found {len(jobs)} jobs")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    return jobs


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def scrape_greenhouse_jobs(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """Scrape Greenhouse jobs."""
    jobs = []
    
    if "greenhouse.io" not in careers_url:
        print(f"  ⚠ Invalid Greenhouse URL: {careers_url}")
        return jobs
    
    company_slug = None
    if "boards.greenhouse.io" in careers_url:
        company_slug = careers_url.split("boards.greenhouse.io/")[-1].split("/")[0].split("?")[0]
    elif "job-boards.greenhouse.io" in careers_url:
        company_slug = careers_url.split("job-boards.greenhouse.io/")[-1].split("/")[0].split("?")[0]
    
    if not company_slug:
        print(f"  ⚠ Could not extract Greenhouse slug from: {careers_url}")
        return jobs
    
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    
    try:
        response = requests.get(api_url, headers={"User-Agent": "RecruiterMarketBrief/1.0"}, timeout=30)
        response.raise_for_status()
        job_listings = response.json().get("jobs", [])
        
        for job in job_listings:
            updated_at = job.get("updated_at")
            if updated_at:
                try:
                    first_seen = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                except Exception:
                    first_seen = datetime.utcnow()
            else:
                first_seen = datetime.utcnow()
            
            job_id = job.get("id")
            job_url = job.get("absolute_url") or f"{careers_url}/jobs/{job_id}"
            
            locations = job.get("locations", [])
            location_raw = ", ".join([loc.get("name", "") for loc in locations]) if locations else ""
            
            jobs.append({
                "source_job_id": str(job_id),
                "company_id": company_id,
                "title": job.get("title", ""),
                "url": job_url,
                "first_seen": first_seen.isoformat(),
                "location_city": None,
                "location_state": None,
                "is_remote": any("remote" in loc.get("name", "").lower() for loc in locations),
                "source_url": careers_url,
                "scraped_at": datetime.utcnow().isoformat(),
                "function": classify_job_function(job.get("title", "")),
                "level": classify_job_level(job.get("title", "")),
            })
        
        print(f"  ✓ Found {len(jobs)} jobs")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    return jobs


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def scrape_lever_jobs(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """Scrape Lever jobs."""
    jobs = []
    
    if "lever.co" not in careers_url:
        print(f"  ⚠ Invalid Lever URL: {careers_url}")
        return jobs
    
    company_slug = None
    if "jobs.lever.co" in careers_url:
        company_slug = careers_url.split("jobs.lever.co/")[-1].split("/")[0].split("?")[0]
    elif "lever.co" in careers_url and "jobs" not in careers_url:
        company_slug = careers_url.split("lever.co/")[-1].split("/")[0].split("?")[0]
    
    if not company_slug:
        print(f"  ⚠ Could not extract Lever slug from: {careers_url}")
        return jobs
    
    api_url = f"https://api.lever.co/v0/postings/{company_slug}"
    
    try:
        response = requests.get(api_url, headers={"User-Agent": "RecruiterMarketBrief/1.0"}, timeout=30)
        response.raise_for_status()
        job_listings = response.json()
        
        for job in job_listings:
            created_at = job.get("createdAt")
            if created_at:
                try:
                    if isinstance(created_at, int):
                        first_seen = datetime.fromtimestamp(created_at / 1000)
                    else:
                        first_seen = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                except Exception:
                    first_seen = datetime.utcnow()
            else:
                first_seen = datetime.utcnow()
            
            job_id = job.get("id")
            job_url = job.get("hostedUrl") or f"https://jobs.lever.co/{company_slug}/{job_id}"
            
            locations = job.get("categories", {}).get("location", [])
            location_raw = ", ".join(locations) if locations else ""
            
            jobs.append({
                "source_job_id": job_id,
                "company_id": company_id,
                "title": job.get("text", ""),
                "url": job_url,
                "first_seen": first_seen.isoformat(),
                "location_city": None,
                "location_state": None,
                "is_remote": any("remote" in loc.lower() for loc in locations),
                "source_url": careers_url,
                "scraped_at": datetime.utcnow().isoformat(),
                "function": classify_job_function(job.get("text", "")),
                "level": classify_job_level(job.get("text", "")),
            })
        
        print(f"  ✓ Found {len(jobs)} jobs")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    return jobs


def main():
    """Test scraping."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials in .env")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get one test company from each ATS
    print("Finding test companies...\n")
    test_companies = []
    
    for ats in ["ashby", "greenhouse", "lever"]:
        result = supabase.table("companies").select("id,name,ats,careers_url").eq("ats", ats).limit(1).execute()
        if result.data:
            company = result.data[0]
            test_companies.append(company)
            print(f"✓ {ats.upper()}: {company['id']} - {company['name']}")
    
    if not test_companies:
        print("No test companies found!")
        return
    
    print(f"\nScraping {len(test_companies)} companies...\n")
    
    total_inserted = 0
    for company in test_companies:
        company_id = company["id"]
        careers_url = company["careers_url"]
        ats = company["ats"]
        
        print(f"Scraping {company_id} ({ats})...")
        
        if ats == "ashby":
            jobs = scrape_ashby_jobs(careers_url, company_id)
        elif ats == "greenhouse":
            jobs = scrape_greenhouse_jobs(careers_url, company_id)
        elif ats == "lever":
            jobs = scrape_lever_jobs(careers_url, company_id)
        else:
            print(f"  ⚠ {ats} scraper not implemented yet, skipping")
            continue
        
        if jobs:
            # Upsert to database
            try:
                result = supabase.table("job_postings").upsert(
                    jobs,
                    on_conflict="source_job_id,company_id",
                ).execute()
                inserted = len(jobs)
                total_inserted += inserted
                print(f"  ✓ Inserted {inserted} jobs\n")
            except Exception as e:
                print(f"  ✗ Failed to insert: {e}\n")
        else:
            print(f"  ⚠ No jobs found\n")
    
    print(f"✅ Test complete! Total jobs inserted: {total_inserted}")


if __name__ == "__main__":
    main()
