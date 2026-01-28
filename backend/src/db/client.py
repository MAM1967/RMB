 """
 Database and Supabase client helpers.
 """

 from typing import Any

 import psycopg
 from supabase import Client, create_client

 from backend.src.config.settings import Settings


 def get_supabase_client(settings: Settings) -> Client:
    """Return a Supabase client using provided settings."""
    return create_client(str(settings.supabase.url), settings.supabase.anon_key)


 def get_psycopg_connection(settings: Settings, **kwargs: Any) -> psycopg.Connection:
    """
    Return a psycopg3 connection using Supabase connection string.

    Expects SUPABASE_DB_URL-style DSN in environment if used.
    """

    dsn = kwargs.pop("dsn", None)
    if dsn is None:
        raise ValueError("A Postgres DSN must be provided for psycopg connections.")
    return psycopg.connect(dsn, **kwargs)

