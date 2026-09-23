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
from app.config import get_settings
from app.storage.cross_source import CrossSourceRepository, adapt_stock_events_response
from app.storage.history import NormalizedSnapshotRepository
import asyncio


class StockEventsService:
    def __init__(self, source: StockEventsSource | None = None) -> None:
        self.source = source or WebbsiteStockEventsSource()

    async def get_stock_events(self, code: str | int) -> StockEventsResponse:
        response = await self.source.get_stock_events(code)
        response = normalize_stock_events_response(response)
        response = validate_stock_events_response(response)
        await asyncio.to_thread(
            CrossSourceRepository(NormalizedSnapshotRepository(get_settings().ccass_sqlite_path)).put_many,
            adapt_stock_events_response(response),
        )
        return response


@lru_cache
def get_stock_events_service() -> StockEventsService:
    return StockEventsService()
