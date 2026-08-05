from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.data_quality import structured_warning
from app.models import StockEventsMetadata, StockEventsResponse
from ccass_core.normalize import normalize_stock_code

STOCK_EVENTS_SOURCE_PENDING_NAME = "Stock events source pending"
STOCK_EVENTS_SOURCE_PENDING_URL: str | None = None


class StockEventsSource(Protocol):
    async def get_stock_events(self, code: str | int) -> StockEventsResponse: ...


class PendingStockEventsSource:
    async def get_stock_events(self, code: str | int) -> StockEventsResponse:
        normalized = normalize_stock_code(code)
        return StockEventsResponse(
            metadata=StockEventsMetadata(
                code=normalized,
                source_name=STOCK_EVENTS_SOURCE_PENDING_NAME,
                source_url=STOCK_EVENTS_SOURCE_PENDING_URL,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                stock_events_count=0,
                source_status="pending",
            ),
            stock_events=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "STOCK_EVENTS_SOURCE_PENDING",
                    "Stock events source is pending approval; placeholder read path only.",
                )
            ],
        )
