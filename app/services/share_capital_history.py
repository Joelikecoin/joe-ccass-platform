from __future__ import annotations

from datetime import date
from functools import lru_cache

from app.models import ShareCapitalHistoryResponse
from app.sources.share_capital_history import HKEXShareCapitalHistorySource


class ShareCapitalHistoryService:
    def __init__(self, source: HKEXShareCapitalHistorySource | None = None) -> None:
        self.source = source or HKEXShareCapitalHistorySource()

    async def get_share_capital_history(self, code: str | int, *, start_date: date | None = None, end_date: date | None = None) -> ShareCapitalHistoryResponse:
        return await self.source.get_share_capital_history(code, start_date=start_date, end_date=end_date)


@lru_cache
def get_share_capital_history_service() -> ShareCapitalHistoryService:
    return ShareCapitalHistoryService()
