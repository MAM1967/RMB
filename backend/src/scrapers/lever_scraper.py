"""
Lever ATS scraper.

Lever careers pages are typically at: https://jobs.lever.co/{company_slug}
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
def scrape_lever_jobs(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """
    Scrape job postings from a Lever careers page.
    
    Args:
        careers_url: Full URL to the Lever careers page
        company_id: Company ID for linking
        
    Returns:
        List of job posting dictionaries with normalized fields
    """
    jobs = []
    
    # Extract company slug from URL
    if "lever.co" not in careers_url:
        logger.warning("invalid_lever_url", url=careers_url, company_id=company_id)
        return jobs
    
    # Try different URL patterns
    company_slug = None
    if "jobs.lever.co" in careers_url:
        company_slug = careers_url.split("jobs.lever.co/")[-1].split("/")[0].split("?")[0]
    elif "lever.co" in careers_url:
        # Extract from various Lever URL patterns
        parts = careers_url.split("lever.co/")
        if len(parts) > 1:
            company_slug = parts[-1].split("/")[0].split("?")[0]
            # Handle case where URL is just "https://www.lever.co/" (Lever's own site)
            if company_slug in ["", "www", "www.lever.co"]:
                company_slug = "lever"  # Lever's own company slug
    
    if not company_slug or company_slug in ["", "www"]:
        logger.warning("could_not_extract_lever_slug", url=careers_url, company_id=company_id)
        return jobs
    
    # Lever API endpoint
    api_url = f"https://api.lever.co/v0/postings/{company_slug}"
    
    headers = {
        "User-Agent": "RecruiterMarketBrief/1.0",
        "Accept": "application/json",
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        job_listings = response.json()
        
        for job in job_listings:
            # Parse createdAt date
            created_at = job.get("createdAt")
            if created_at:
                try:
                    # Lever uses milliseconds timestamp
                    if isinstance(created_at, int):
                        first_seen = datetime.fromtimestamp(created_at / 1000)
                    else:
                        first_seen = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                except Exception:
                    first_seen = datetime.utcnow()
            else:
                first_seen = datetime.utcnow()
            
            # Build job URL
            job_id = job.get("id")
            job_url = job.get("hostedUrl") or f"https://jobs.lever.co/{company_slug}/{job_id}"
            
            # Extract location
            locations = job.get("categories", {}).get("location", [])
            location_raw = ", ".join(locations) if locations else ""
            
            jobs.append({
                "source_job_id": job_id,
                "company_id": company_id,
                "title": job.get("text", ""),
                "url": job_url,
                "first_seen": first_seen.isoformat(),
                "location_raw": location_raw,
                "is_remote": any("remote" in loc.lower() for loc in locations),
                "source_url": careers_url,
                "scraped_at": datetime.utcnow().isoformat(),
            })
        
        logger.info(
            "lever_scrape_success",
            company_id=company_id,
            jobs_found=len(jobs),
        )
    
    except requests.exceptions.RequestException as e:
        logger.error("lever_scrape_error", company_id=company_id, error=str(e))
    except Exception as e:
        logger.error("lever_scrape_unexpected_error", company_id=company_id, error=str(e))
    
    return jobs
