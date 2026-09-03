from __future__ import annotations

from functools import lru_cache

from app.models import OfficersResponse
from app.services.data_quality_validation import (
    normalize_officers_response,
    validate_officers_response,
)
from app.sources.officers import OfficersSource, ThsF10OfficersSource, WebbsiteOfficersSource


class OfficersService:
    def __init__(self, source: OfficersSource | None = None) -> None:
        self.source = source or ThsF10OfficersSource()

    async def get_officers(self, code: str | int) -> OfficersResponse:
        response = await self.source.get_officers(code)
        if not response.officers and not isinstance(self.source, WebbsiteOfficersSource):
            try:
                response = await WebbsiteOfficersSource().get_officers(code)
            except Exception:
                pass
        response = normalize_officers_response(response)
        return validate_officers_response(response)


@lru_cache
def get_officers_service() -> OfficersService:
    return OfficersService()
