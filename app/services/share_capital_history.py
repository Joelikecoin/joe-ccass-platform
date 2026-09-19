from __future__ import annotations

from datetime import date
from functools import lru_cache

from app.config import get_settings
from app.models import ShareCapitalHistoryResponse
from app.sources.share_capital_history import HKEXShareCapitalHistorySource
from app.storage.history import NormalizedSnapshotRepository
from app.storage.share_capital_history import ShareCapitalHistoryRepository


class ShareCapitalHistoryService:
    def __init__(self, source: HKEXShareCapitalHistorySource | None = None, repository=None) -> None:
        self.source = source or HKEXShareCapitalHistorySource()
        self.repository = repository

    async def get_share_capital_history(self, code: str | int, *, start_date: date | None = None, end_date: date | None = None) -> ShareCapitalHistoryResponse:
        response = await self.source.get_share_capital_history(code, start_date=start_date, end_date=end_date)
        if self.repository is not None and response.rows:
            self.repository.save(response)
        return response

    async def get_persisted_share_capital_history(self, code: str | int, *, start_date: date | None = None, end_date: date | None = None) -> ShareCapitalHistoryResponse | None:
        if self.repository is None:
            return None
        return self.repository.load(str(code), start_date=start_date, end_date=end_date)


@lru_cache
def get_share_capital_history_service() -> ShareCapitalHistoryService:
    settings = get_settings()
    return ShareCapitalHistoryService(repository=ShareCapitalHistoryRepository(NormalizedSnapshotRepository(settings.ccass_sqlite_path)))
