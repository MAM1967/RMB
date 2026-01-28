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
        A function name such as \"operations\" or \"finance\", or None if unknown.
    """

    normalized = title.lower()
    if "operations" in normalized:
        return "operations"
    if "finance" in normalized:
        return "finance"
    if "marketing" in normalized:
        return "marketing"
    return None


 def classify_job_level(title: str) -> Optional[str]:
    """
    Classify a job title into a seniority level.

    Args:
        title: Raw job title string.

    Returns:
        A level such as \"director\" or \"vp\", or None if unknown.
    """

    normalized = title.lower()
    if "director" in normalized:
        return "director"
    if "vp" in normalized or "vice president" in normalized:
        return "vp"
    if "head of" in normalized:
        return "head"
    return None

