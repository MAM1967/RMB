#!/usr/bin/env python3
"""
Scrape all Ashby companies - tries multiple approaches.
"""

import os
import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import requests
import re
import json
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


def scrape_ashby_html(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """Scrape Ashby jobs by parsing HTML page."""
    jobs = []
    
    try:
        response = requests.get(careers_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        response.raise_for_status()
        html = response.text
        
        # Look for job data in script tags - Ashby embeds job data
        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        
        for script in script_tags:
            # Try to find JSON with job data
            # Look for patterns like: {"jobPostings": [...]} or window.__INITIAL_STATE__ = {...}
            patterns = [
                r'(\{.*?"jobPostings"\s*:\s*\[.*?\].*?\})',
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.jobs\s*=\s*(\[.+?\]);',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, script, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, dict) and "jobPostings" in data:
                            job_postings = data["jobPostings"]
                        elif isinstance(data, list):
                            job_postings = data
                        else:
                            continue
                        
                        # Process jobs
                        for job in job_postings:
                            job_id = job.get("id") or job.get("_id") or job.get("jobId") or ""
                            title = job.get("title") or job.get("name") or ""
                            
                            if not job_id or not title:
                                continue
                            
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
                            
                            company_slug = careers_url.split("jobs.ashbyhq.com/")[-1].split("/")[0]
                            job_url = job.get("url") or job.get("jobUrl") or f"{careers_url}/{job_id}"
                            if not job_url.startswith("http"):
                                job_url = f"https://jobs.ashbyhq.com/{company_slug}/{job_id}"
                            
                            location_raw = job.get("locationName") or job.get("location_name") or job.get("location") or ", ".join(job.get("locations", [])) or ""
                            is_remote = job.get("isRemote", False) or job.get("is_remote", False) or "remote" in location_raw.lower()
                            
                            jobs.append({
                                "source_job_id": str(job_id),
                                "company_id": company_id,
                                "title": title,
                                "url": job_url,
                                "first_seen": first_seen.isoformat(),
                                "location_city": None,
                                "location_state": None,
                                "is_remote": is_remote,
                                "source_url": careers_url,
                                "scraped_at": datetime.utcnow().isoformat(),
                                "function": classify_job_function(title),
                                "level": classify_job_level(title),
                            })
                        
                        if jobs:
                            return jobs  # Return first successful parse
                    except Exception:
                        continue
        
        # Fallback: try to extract from page structure if no JSON found
        # Look for job listing elements
        job_links = re.findall(r'<a[^>]*href=["\']([^"\']*jobs[^"\']*)["\']', html, re.I)
        if job_links and not jobs:
            # If we found job links but no structured data, at least we know jobs exist
            print(f"  ⚠ Found job links but couldn't parse structured data")
    
    except Exception as e:
        print(f"  ✗ Error scraping HTML: {e}")
    
    return jobs


def scrape_company(company: dict, supabase: Any) -> tuple[str, int]:
    """Scrape a single company and return (company_id, jobs_inserted)."""
    company_id = company["id"]
    careers_url = company["careers_url"]
    
    print(f"Scraping {company_id}...", end=" ", flush=True)
    
    jobs = scrape_ashby_html(careers_url, company_id)
    
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
        print(f"✗ Error inserting: {e}")
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
    
    # Scrape with limited parallelism (max 5 concurrent)
    total_jobs = 0
    successful = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_company, company, supabase): company for company in companies}
        
        for future in as_completed(futures):
            company_id, jobs_inserted = future.result()
            if jobs_inserted > 0:
                successful += 1
            total_jobs += jobs_inserted
    
    print(f"\n✅ Scraping complete!")
    print(f"   Companies processed: {len(companies)}")
    print(f"   Companies with jobs: {successful}")
    print(f"   Total jobs inserted: {total_jobs}")


if __name__ == "__main__":
    main()
