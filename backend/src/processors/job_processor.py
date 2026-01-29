"""
Job posting processor that applies classification and normalization.
"""

from datetime import datetime
from typing import Any, Optional

from backend.src.processors.classifier import classify_job_function, classify_job_level
from backend.src.logging_config import get_logger

logger = get_logger()


def process_job_posting(job: dict[str, Any]) -> dict[str, Any]:
    """
    Process a raw job posting by applying classification and normalization.
    
    Args:
        job: Raw job posting dictionary from scraper
        
    Returns:
        Processed job posting ready for database storage
    """
    title = job.get("title", "")
    
    # Apply classification
    function = classify_job_function(title)
    level = classify_job_level(title)
    
    # Parse location if available
    location_raw = job.get("location_raw", "")
    location_city = None
    location_state = None
    
    if location_raw:
        # Simple parsing - can be enhanced later
        parts = location_raw.split(",")
        if len(parts) >= 2:
            location_city = parts[0].strip()
            location_state = parts[-1].strip()[:2]  # State abbreviation
        elif len(parts) == 1:
            location_city = parts[0].strip()
    
    # Ensure required fields
    processed = {
        "source_job_id": job.get("source_job_id", ""),
        "company_id": job.get("company_id", ""),
        "title": title,
        "url": job.get("url", ""),
        "first_seen": job.get("first_seen", datetime.utcnow().isoformat()),
        "function": function,
        "level": level,
        "location_city": location_city,
        "location_state": location_state,
        "is_remote": job.get("is_remote", False),
        "source_url": job.get("source_url", ""),
        "scraped_at": job.get("scraped_at", datetime.utcnow().isoformat()),
    }
    
    return processed
