"""
Greenhouse ATS scraper.

Greenhouse careers pages are typically at: https://boards.greenhouse.io/{company_slug}
They expose a JSON API endpoint for job listings.
"""

import json
from datetime import datetime
from typing import Any, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.src.logging_config import get_logger

logger = get_logger()


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def scrape_greenhouse_jobs(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """
    Scrape job postings from a Greenhouse careers page.
    
    Args:
        careers_url: Full URL to the Greenhouse careers page
        company_id: Company ID for linking
        
    Returns:
        List of job posting dictionaries with normalized fields
    """
    jobs = []
    
    # Extract company slug from URL
    if "greenhouse.io" not in careers_url:
        logger.warning("invalid_greenhouse_url", url=careers_url, company_id=company_id)
        return jobs
    
    # Try different URL patterns
    company_slug = None
    if "boards.greenhouse.io" in careers_url:
        company_slug = careers_url.split("boards.greenhouse.io/")[-1].split("/")[0].split("?")[0]
    elif "job-boards.greenhouse.io" in careers_url:
        company_slug = careers_url.split("job-boards.greenhouse.io/")[-1].split("/")[0].split("?")[0]
    
    if not company_slug:
        logger.warning("could_not_extract_greenhouse_slug", url=careers_url, company_id=company_id)
        return jobs
    
    # Greenhouse API endpoint
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    
    headers = {
        "User-Agent": "RecruiterMarketBrief/1.0",
        "Accept": "application/json",
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        job_listings = data.get("jobs", [])
        
        for job in job_listings:
            # Parse updated date (Greenhouse uses updated_at)
            updated_at = job.get("updated_at")
            if updated_at:
                try:
                    first_seen = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                except Exception:
                    first_seen = datetime.utcnow()
            else:
                first_seen = datetime.utcnow()
            
            # Build job URL
            job_id = job.get("id")
            job_url = job.get("absolute_url") or f"{careers_url}/jobs/{job_id}"
            
            # Extract location
            locations = job.get("locations", [])
            location_raw = ", ".join([loc.get("name", "") for loc in locations]) if locations else ""
            
            jobs.append({
                "source_job_id": str(job_id),
                "company_id": company_id,
                "title": job.get("title", ""),
                "url": job_url,
                "first_seen": first_seen.isoformat(),
                "location_raw": location_raw,
                "is_remote": any("remote" in loc.get("name", "").lower() for loc in locations),
                "source_url": careers_url,
                "scraped_at": datetime.utcnow().isoformat(),
            })
        
        logger.info(
            "greenhouse_scrape_success",
            company_id=company_id,
            jobs_found=len(jobs),
        )
    
    except requests.exceptions.RequestException as e:
        logger.error("greenhouse_scrape_error", company_id=company_id, error=str(e))
    except Exception as e:
        logger.error("greenhouse_scrape_unexpected_error", company_id=company_id, error=str(e))
    
    return jobs
