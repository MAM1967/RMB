"""
Job posting storage utilities for Supabase.
"""

from typing import Any, Sequence

from supabase import Client

from backend.src.logging_config import get_logger

logger = get_logger()


def upsert_job_postings(supabase: Client, jobs: Sequence[dict[str, Any]]) -> int:
    """
    Batch upsert job postings to Supabase.
    
    Uses ON CONFLICT to handle duplicates based on (source_job_id, company_id).
    
    Args:
        supabase: Supabase client instance
        jobs: List of processed job posting dictionaries
        
    Returns:
        Number of jobs successfully upserted
    """
    if not jobs:
        return 0
    
    inserted = 0
    
    # Batch into chunks of 100
    for i in range(0, len(jobs), 100):
        batch = jobs[i:i+100]
        
        try:
            result = supabase.table("job_postings").upsert(
                batch,
                on_conflict="source_job_id,company_id",
            ).execute()
            
            inserted += len(batch)
            logger.info(
                "job_postings_batch_upserted",
                batch_start=i,
                batch_size=len(batch),
                total_inserted=inserted,
            )
        
        except Exception as e:
            logger.error(
                "job_postings_batch_error",
                batch_start=i,
                error=str(e),
            )
            # Try individual inserts for this batch
            for job in batch:
                try:
                    supabase.table("job_postings").upsert(
                        job,
                        on_conflict="source_job_id,company_id",
                    ).execute()
                    inserted += 1
                except Exception as e2:
                    logger.error(
                        "job_posting_upsert_error",
                        company_id=job.get("company_id"),
                        source_job_id=job.get("source_job_id"),
                        error=str(e2),
                    )
    
    return inserted
