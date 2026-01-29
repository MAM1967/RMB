 """
 Simple job classification utilities.

 These functions will be expanded over time, but provide
 a minimal, testable starting point for Phase 1.
 """

 from __future__ import annotations

 from typing import Optional


 def classify_job_function(title: str) -> Optional[str]:
    """
    Classify a job title into a broad function bucket.

    Args:
        title: Raw job title string.

    Returns:
        A function name such as \"operations\", \"finance\", \"gtm\", \"product\", \"people\", \"engineering\", \"marketing\", or None if unknown.
    """
    normalized = title.lower()
    
    # Function keywords from PRD
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
    """
    Classify a job title into a seniority level.

    Args:
        title: Raw job title string.

    Returns:
        A level such as \"c-level\", \"svp\", \"vp\", or \"director\", or None if unknown.
    """
    normalized = title.lower()
    
    # Check in order of seniority (most senior first)
    if any(kw in normalized for kw in ["chief", "ceo", "cfo", "coo", "cto", "cmo", "c-level", "c suite"]):
        return "c-level"
    if any(kw in normalized for kw in ["senior vice president", "svp", "sr vp"]):
        return "svp"
    if any(kw in normalized for kw in ["vice president", "vp", "v.p."]):
        return "vp"
    if any(kw in normalized for kw in ["director", "dir.", "head of"]):
        return "director"
    
    return None

