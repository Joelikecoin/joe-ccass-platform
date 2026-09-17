from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.models import FundamentalsResponse
from app.sources.fundamentals import HKEXFundamentalsSource
from app.storage.fundamentals import FundamentalsRepository
from app.storage.history import NormalizedSnapshotRepository


class FundamentalsService:
    def __init__(self, source=None, repository=None):
        self.source = source or HKEXFundamentalsSource()
        self.repository = repository

    async def get_fundamentals(self, code: str | int) -> FundamentalsResponse:
        response = await self.source.get_fundamentals(code)
        if self.repository is not None and response.rows:
            self.repository.save(response)
        return response


@lru_cache
def get_fundamentals_service() -> FundamentalsService:
    settings = get_settings()
    return FundamentalsService(HKEXFundamentalsSource(), FundamentalsRepository(NormalizedSnapshotRepository(settings.ccass_sqlite_path)))
