from functools import lru_cache
from typing import Protocol

from app.config import Settings, get_settings
from app.errors import PlatformError
from app.models import CcassResponse
from app.sources.google_drive_csv import GoogleDriveCsvSource
from app.sources.webbsite import WebbsiteClient
from ccass_core.normalize import normalize_stock_code


class HoldingsSource(Protocol):
    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse: ...


class MirrorWithCsvFallback:
    def __init__(self, settings: Settings) -> None:
        self.mirror = WebbsiteClient(settings)
        self.csv = GoogleDriveCsvSource(settings) if settings.ccass_csv_url.strip() else None

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        try:
            return await self.mirror.get_holdings(code, limit=limit)
        except PlatformError as mirror_error:
            if self.csv is None:
                raise
            error_code = getattr(mirror_error, "code", type(mirror_error).__name__)
            try:
                response = await self.csv.get_holdings(code, limit=limit)
            except PlatformError as csv_error:
                raise PlatformError(
                    csv_error.code,
                    f"Primary mirror failed ({error_code}); configured CSV fallback also failed "
                    f"({csv_error.code}).",
                    retry_recommended=(
                        mirror_error.retry_recommended or csv_error.retry_recommended
                    ),
                    retry_after_seconds=(
                        csv_error.retry_after_seconds or mirror_error.retry_after_seconds
                    ),
                    status_code=csv_error.status_code,
                ) from csv_error
            response.data_quality_warnings.append(
                f"Primary mirror failed ({error_code}); using the configured CSV snapshot fallback."
            )
            return response


class CcassService:
    def __init__(
        self,
        client: HoldingsSource | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if client is not None:
            self.source = client
        elif self.settings.data_source == "google_drive_csv":
            self.source = GoogleDriveCsvSource(self.settings)
        elif self.settings.data_source == "auto":
            self.source = MirrorWithCsvFallback(self.settings)
        else:
            self.source = WebbsiteClient(self.settings)
        self.client = self.source

    async def get_stock_data(self, code: str | int, holdings_limit: int = 15) -> CcassResponse:
        normalized = normalize_stock_code(code)
        return await self.source.get_holdings(normalized, limit=holdings_limit)


@lru_cache
def get_ccass_service() -> CcassService:
    return CcassService()
