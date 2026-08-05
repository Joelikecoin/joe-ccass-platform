from __future__ import annotations

from functools import lru_cache

from app.models import CapitalInformationResponse
from app.sources.capital_information import (
    CapitalInformationSource,
    PendingCapitalInformationSource,
    ThsF10CapitalInformationSource,
)


class CapitalInformationService:
    def __init__(self, source: CapitalInformationSource | None = None) -> None:
        self.source = source or ThsF10CapitalInformationSource()

    async def get_capital_information(self, code: str | int) -> CapitalInformationResponse:
        return await self.source.get_capital_information(code)


@lru_cache
def get_capital_information_service() -> CapitalInformationService:
    return CapitalInformationService()
