from __future__ import annotations

from functools import lru_cache

from app.models import StockEventsResponse
from app.sources.stock_events import PendingStockEventsSource, StockEventsSource


class StockEventsService:
    def __init__(self, source: StockEventsSource | None = None) -> None:
        self.source = source or PendingStockEventsSource()

    async def get_stock_events(self, code: str | int) -> StockEventsResponse:
        return await self.source.get_stock_events(code)


@lru_cache
def get_stock_events_service() -> StockEventsService:
    return StockEventsService()
