from functools import lru_cache
from typing import Protocol

from app.config import Settings, get_settings
from app.core.normalizers import normalize_stock_code
from app.models import CcassResponse
from app.sources.google_drive_csv import GoogleDriveCsvSource
from app.sources.webbsite import WebbsiteClient


class HoldingsSource(Protocol):
    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse: ...


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
        else:
            self.source = WebbsiteClient(self.settings)
        self.client = self.source

    async def get_stock_data(self, code: str | int, holdings_limit: int = 15) -> CcassResponse:
        normalized = normalize_stock_code(code)
        return await self.source.get_holdings(normalized, limit=holdings_limit)


@lru_cache
def get_ccass_service() -> CcassService:
    return CcassService()
