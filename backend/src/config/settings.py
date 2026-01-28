 """
 Settings and configuration models for RMB backend.
 """

 from pathlib import Path
 from typing import Any

 from dotenv import load_dotenv
 from pydantic import BaseModel, BaseSettings, HttpUrl

 # Load .env early for local development
 load_dotenv()


 class SupabaseSettings(BaseModel):
    """Supabase connection details."""

    url: HttpUrl
    anon_key: str
    service_role_key: str | None = None


 class ApifySettings(BaseModel):
    """Apify credentials."""

    token: str


 class Settings(BaseSettings):
    """
    Application-level settings loaded from environment variables.
    """

    environment: str = "local"
    log_level: str = "INFO"

    supabase_url: HttpUrl
    supabase_key: str
    supabase_service_role_key: str | None = None

    apify_token: str

    class Config:
        env_prefix = ""
        env_file = ".env"
        case_sensitive = False

    @property
    def supabase(self) -> SupabaseSettings:
        """Return structured Supabase settings."""
        return SupabaseSettings(
            url=self.supabase_url,
            anon_key=self.supabase_key,
            service_role_key=self.supabase_service_role_key,
        )

    @property
    def apify(self) -> ApifySettings:
        """Return structured Apify settings."""
        return ApifySettings(token=self.apify_token)


 def get_settings(**overrides: Any) -> Settings:
    """
    Return Settings instance.

    Allows overrides for testing.
    """

    return Settings(**overrides)


 BASE_DIR = Path(__file__).resolve().parents[3]
 CONFIG_DIR = BASE_DIR / "config"

