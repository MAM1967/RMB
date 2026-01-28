 import pytest

 from backend.src.processors.classifier import classify_job_function, classify_job_level


 def test_classify_job_function_operations_keyword_returns_operations() -> None:
    """Should classify 'Director of Operations' as operations function."""
    result = classify_job_function("Director of Operations")
    assert result == "operations"


 def test_classify_job_function_ambiguous_title_returns_none() -> None:
    """Should return None for titles without clear function keywords."""
    result = classify_job_function("VP of Strategy")
    assert result is None


 def test_classify_job_level_director_returns_director() -> None:
    """Should classify titles containing 'Director' as director level."""
    result = classify_job_level("Director of Operations")
    assert result == "director"


 def test_classify_job_level_unknown_returns_none() -> None:
    """Should return None when no known level keywords are present."""
    result = classify_job_level("Software Engineer")
    assert result is None

