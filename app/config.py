from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str = ""
    data_source: Literal["webbsite", "google_drive_csv"] = "webbsite"
    ccass_csv_url: str = ""
    ccass_csv_max_bytes: int = 5_000_000
    webbsite_base_url: str = "https://webbsite.0xmd.com"
    webbsite_fallback_base_url: str = "https://webbsite.renavon.com"
    # Keep two sequential mirror attempts inside a typical 30-second gateway budget.
    request_timeout_seconds: float = 12.0
    cache_ttl_seconds: int = 900
    min_request_interval_seconds: float = 1.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
