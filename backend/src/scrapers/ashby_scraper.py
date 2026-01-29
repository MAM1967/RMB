"""
Ashby ATS scraper.

Ashby careers pages are typically at: https://jobs.ashbyhq.com/{company_slug}
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
def scrape_ashby_jobs(careers_url: str, company_id: str) -> list[dict[str, Any]]:
    """
    Scrape job postings from an Ashby careers page.
    
    Uses the public Ashby API endpoint: https://api.ashbyhq.com/posting-api/job-board/{clientname}
    
    Args:
        careers_url: Full URL to the Ashby careers page
        company_id: Company ID for linking
        
    Returns:
        List of job posting dictionaries with normalized fields
    """
    jobs = []
    
    # Extract company slug from URL (e.g., jobs.ashbyhq.com/bankofamerica -> bankofamerica)
    if "jobs.ashbyhq.com" not in careers_url:
        logger.warning("invalid_ashby_url", url=careers_url, company_id=company_id)
        return jobs
    
    # Extract company slug (organizationHostedJobsPageName)
    company_slug = careers_url.split("jobs.ashbyhq.com/")[-1].split("/")[0].split("?")[0]
    
    # Use Ashby's GraphQL API
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "RecruiterMarketBrief/1.0",
        "Origin": "https://jobs.ashbyhq.com",
        "Referer": careers_url,
    }
    
    # GraphQL query to get all job postings
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
              employmentType
            }
          }
        }
        """,
        "variables": {"organizationHostedJobsPageName": company_slug},
    }
    
    try:
        response = requests.post(api_url, json=graphql_query, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            logger.error("ashby_graphql_errors", company_id=company_id, errors=data["errors"])
            return jobs
        
        job_board = data.get("data", {}).get("jobBoardWithTeams", {})
        job_postings = job_board.get("jobPostings", [])
        
        if not job_postings:
            logger.info("ashby_no_jobs", company_id=company_id)
            return jobs
    
    try:
        
        for job in job_postings:
            job_id = job.get("id", "")
            if not job_id:
                continue
            
            # Use current time as first_seen (GraphQL brief doesn't include published date)
            first_seen = datetime.utcnow()
            
            # Build job URL - Ashby pattern: jobs.ashbyhq.com/{slug}/{job_id}
            job_url = f"{careers_url}/{job_id}"
            
            # Extract location
            location_raw = job.get("locationName") or job.get("locationAddress") or ""
            
            # Check if remote based on workplaceType
            workplace_type = job.get("workplaceType", "").lower() if job.get("workplaceType") else ""
            is_remote = workplace_type in ["remote", "hybrid"] or "remote" in location_raw.lower()
            
            jobs.append({
                "source_job_id": str(job_id),
                "company_id": company_id,
                "title": job.get("title", ""),
                "url": job_url,
                "first_seen": first_seen.isoformat(),
                "location_raw": location_raw,
                "is_remote": is_remote,
                "source_url": careers_url,
                "scraped_at": datetime.utcnow().isoformat(),
            })
        
        logger.info(
            "ashby_scrape_success",
            company_id=company_id,
            jobs_found=len(jobs),
        )
    
    except requests.exceptions.RequestException as e:
        logger.error("ashby_scrape_error", company_id=company_id, error=str(e))
    except Exception as e:
        logger.error("ashby_scrape_unexpected_error", company_id=company_id, error=str(e))
    
    return jobs
