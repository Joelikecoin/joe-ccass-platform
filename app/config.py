from datetime import date
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str = ""
    data_source: Literal["auto", "webbsite", "google_drive_csv"] = "auto"
    ccass_csv_url: str = ""
    ccass_csv_max_bytes: int = 5_000_000
    google_drive_csv_enabled: bool = True
    google_drive_csv_audit_state: Literal["approved", "disabled", "unverified"] = "approved"
    google_drive_csv_audit_date: date | None = None
    webbsite_base_url: str = "https://webbsite.0xmd.com"
    webbsite_fallback_base_url: str = "https://webbsite.renavon.com"
    webbsite_enabled: bool = True
    webbsite_audit_state: Literal["approved", "disabled", "unverified"] = "approved"
    webbsite_audit_date: date | None = None
    webbsite_max_bytes: int = 5_000_000
    # Keep two sequential mirror attempts inside a typical 30-second gateway budget.
    request_timeout_seconds: float = 12.0
    cache_ttl_seconds: int = 900
    source_retry_attempts: int = 1
    backfill_max_dates: int = 366
    backfill_max_pages: int = 1
    backfill_request_sleep_seconds: float = 1.0
    backfill_retry_attempts: int = 2
    min_request_interval_seconds: float = 1.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )

    @model_validator(mode="after")
    def validate_operational_limits(self) -> "Settings":
        positive = {
            "ccass_csv_max_bytes": self.ccass_csv_max_bytes,
            "webbsite_max_bytes": self.webbsite_max_bytes,
            "request_timeout_seconds": self.request_timeout_seconds,
            "source_retry_attempts": self.source_retry_attempts,
            "backfill_max_dates": self.backfill_max_dates,
            "backfill_max_pages": self.backfill_max_pages,
            "backfill_retry_attempts": self.backfill_retry_attempts,
        }
        if any(value <= 0 for value in positive.values()):
            raise ValueError("source size, timeout, retry, and backfill bounds must be positive")
        if (
            self.cache_ttl_seconds < 0
            or self.min_request_interval_seconds < 0
            or self.backfill_request_sleep_seconds < 0
        ):
            raise ValueError("cache TTL and request intervals cannot be negative")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
