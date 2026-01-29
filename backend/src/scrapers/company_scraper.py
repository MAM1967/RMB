"""
Company scraping entrypoints for ATS platforms.

Supports Ashby, Greenhouse, and Lever platforms.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Sequence

from backend.src.config.settings import Settings, get_settings
from backend.src.db.client import get_supabase_client
from backend.src.db.job_storage import upsert_job_postings
from backend.src.logging_config import get_logger
from backend.src.processors.job_processor import process_job_posting
from backend.src.scrapers.ashby_scraper import scrape_ashby_jobs
from backend.src.scrapers.greenhouse_scraper import scrape_greenhouse_jobs
from backend.src.scrapers.lever_scraper import scrape_lever_jobs

logger = get_logger()


def scrape_company(company_id: str, settings: Settings | None = None) -> int:
    """
    Scrape a single company's job postings and store them in Supabase.

    Args:
        company_id: Company ID to scrape
        settings: Optional settings instance
        
    Returns:
        Number of job postings scraped and stored
    """
    cfg = settings or get_settings()
    supabase = get_supabase_client(cfg)
    
    logger.info("scrape_started", company_id=company_id)
    
    # Get company info from database
    try:
        company_result = supabase.table("companies").select("id,name,ats,careers_url").eq("id", company_id).execute()
        
        if not company_result.data:
            logger.warning("company_not_found", company_id=company_id)
            return 0
        
        company = company_result.data[0]
        ats_platform = company.get("ats", "unknown")
        careers_url = company.get("careers_url")
        
        if not careers_url:
            logger.warning("no_careers_url", company_id=company_id)
            return 0
        
        # Scrape based on ATS platform
        raw_jobs = []
        if ats_platform == "ashby":
            raw_jobs = scrape_ashby_jobs(careers_url, company_id)
        elif ats_platform == "greenhouse":
            raw_jobs = scrape_greenhouse_jobs(careers_url, company_id)
        elif ats_platform == "lever":
            raw_jobs = scrape_lever_jobs(careers_url, company_id)
        else:
            logger.warning("unsupported_ats", company_id=company_id, ats=ats_platform)
            return 0
        
        if not raw_jobs:
            logger.info("no_jobs_found", company_id=company_id)
            return 0
        
        # Process jobs (apply classification)
        processed_jobs = [process_job_posting(job) for job in raw_jobs]
        
        # Store in database
        inserted = upsert_job_postings(supabase, processed_jobs)
        
        logger.info(
            "scrape_completed",
            company_id=company_id,
            jobs_scraped=len(raw_jobs),
            jobs_inserted=inserted,
        )
        
        return inserted
    
    except Exception as e:
        logger.error("scrape_company_error", company_id=company_id, error=str(e))
        return 0


 def scrape_companies(
    company_ids: Sequence[str],
    max_workers: int = 5,
    settings: Settings | None = None,
) -> dict[str, int]:
    """
    Scrape multiple companies with limited parallelism.

    This follows the guideline of max 5 concurrent workers.
    
    Args:
        company_ids: List of company IDs to scrape
        max_workers: Maximum concurrent workers (capped at 5)
        settings: Optional settings instance
        
    Returns:
        Dictionary with summary stats: {total_scraped, total_inserted, companies_processed}
    """
    cfg = settings or get_settings()
    effective_workers = min(max_workers, 5, len(company_ids) or 1)

    def _task(cid: str) -> int:
        return scrape_company(cid, cfg)

    total_inserted = 0
    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        results = list(executor.map(_task, company_ids))
        total_inserted = sum(results)
    
    return {
        "total_inserted": total_inserted,
        "companies_processed": len(company_ids),
    }

