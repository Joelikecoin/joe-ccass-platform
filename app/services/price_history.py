from __future__ import annotations

from datetime import date
from functools import lru_cache

from app.config import Settings, get_settings
from app.models import PriceHistoryResponse
from app.sources.price_history import YahooFinancePriceHistorySource


class PriceHistoryService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.source = YahooFinancePriceHistorySource(self.settings)

    async def get_price_history(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PriceHistoryResponse:
        return await self.source.get_price_history(
            code,
            start_date=start_date,
            end_date=end_date,
        )


@lru_cache
def get_price_history_service() -> PriceHistoryService:
    return PriceHistoryService(get_settings())

