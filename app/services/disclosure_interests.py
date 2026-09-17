from __future__ import annotations

from datetime import date
from functools import lru_cache

from app.config import get_settings
from app.models import DisclosureInterestsResponse
from app.sources.disclosure_interests import HKEXDisclosureInterestsSource
from app.storage.history import NormalizedSnapshotRepository
from app.storage.disclosure_interests import DisclosureInterestRepository


class DisclosureInterestsService:
    def __init__(self, source=None, repository=None):
        self.source = source or HKEXDisclosureInterestsSource()
        self.repository = repository

    async def get_disclosures(self, code: str | int, *, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        response = await self.source.get_disclosures(code, start_date=start_date, end_date=end_date)
        if self.repository is not None:
            self.repository.save(response)
        return response


@lru_cache
def get_disclosure_interests_service() -> DisclosureInterestsService:
    settings = get_settings()
    return DisclosureInterestsService(HKEXDisclosureInterestsSource(settings), DisclosureInterestRepository(NormalizedSnapshotRepository(settings.ccass_sqlite_path)))
