from __future__ import annotations

from functools import lru_cache

from app.models import OfficersResponse
from app.sources.officers import OfficersSource, PendingOfficersSource


class OfficersService:
    def __init__(self, source: OfficersSource | None = None) -> None:
        self.source = source or PendingOfficersSource()

    async def get_officers(self, code: str | int) -> OfficersResponse:
        return await self.source.get_officers(code)


@lru_cache
def get_officers_service() -> OfficersService:
    return OfficersService()
