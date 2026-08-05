from __future__ import annotations

from functools import lru_cache

from app.models import StockEventsResponse
from app.services.data_quality_validation import (
    normalize_stock_events_response,
    validate_stock_events_response,
)
from app.sources.stock_events import (
    PendingStockEventsSource,
    StockEventsSource,
    WebbsiteStockEventsSource,
)


class StockEventsService:
    def __init__(self, source: StockEventsSource | None = None) -> None:
        self.source = source or WebbsiteStockEventsSource()

    async def get_stock_events(self, code: str | int) -> StockEventsResponse:
        response = await self.source.get_stock_events(code)
        response = normalize_stock_events_response(response)
        return validate_stock_events_response(response)


@lru_cache
def get_stock_events_service() -> StockEventsService:
    return StockEventsService()
