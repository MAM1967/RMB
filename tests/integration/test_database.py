 import os

 import pytest

 from backend.src.config.settings import get_settings


 @pytest.mark.skipif(
    not os.getenv("SUPABASE_URL"),
    reason="Integration test requires Supabase credentials",
 )
 def test_supabase_settings_load() -> None:
    """Basic smoke test that Supabase settings load from environment."""
    settings = get_settings()
    assert "supabase.co" in str(settings.supabase.url)

