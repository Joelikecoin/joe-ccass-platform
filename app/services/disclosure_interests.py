from __future__ import annotations

from datetime import UTC, date, datetime
from functools import lru_cache

from app.config import get_settings
from app.models import DisclosureInterestsMetadata, DisclosureInterestsResponse
from app.sources.disclosure_interests import HKEXDisclosureInterestsSource, SEARCH
from app.storage.history import NormalizedSnapshotRepository
from app.storage.disclosure_interests import DisclosureInterestRepository
from ccass_core.normalize import normalize_stock_code


class DisclosureInterestsService:
    def __init__(self, source=None, repository=None):
        self.source = source or HKEXDisclosureInterestsSource()
        self.repository = repository

    async def get_disclosures(self, code: str | int, *, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        response = await self.source.get_disclosures(code, start_date=start_date, end_date=end_date)
        if self.repository is not None:
            self.repository.save(response)
        return response

    async def get_persisted_disclosures(self, code: str | int, *, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        """Serve already-persisted DION rows from the store without touching DION."""
        normalized = normalize_stock_code(code)
        if self.repository is None:
            return self._persisted_unavailable(normalized, "Persisted disclosure-interests store is not configured")
        rows = self.repository.load_rows(normalized, start_date=start_date, end_date=end_date)
        if not rows:
            return self._persisted_unavailable(normalized, "NO_PERSISTED_ROWS: trigger the DI job for this code and range first")
        return DisclosureInterestsResponse(
            metadata=DisclosureInterestsMetadata(
                code=normalized,
                source_name="HKEX DION (persisted)",
                source_url=SEARCH,
                fetched_at=datetime.now(UTC),
                source_status="ready",
                filing_count=len(rows),
            ),
            filings=rows,
        )

    @staticmethod
    def _persisted_unavailable(code: str, warning: str) -> DisclosureInterestsResponse:
        return DisclosureInterestsResponse(
            metadata=DisclosureInterestsMetadata(
                code=code,
                source_name="HKEX DION (persisted)",
                source_url=SEARCH,
                fetched_at=datetime.now(UTC),
                source_status="unavailable",
                filing_count=0,
            ),
            data_quality_warnings=[warning],
        )


@lru_cache
def get_disclosure_interests_service() -> DisclosureInterestsService:
    settings = get_settings()
    return DisclosureInterestsService(HKEXDisclosureInterestsSource(settings), DisclosureInterestRepository(NormalizedSnapshotRepository(settings.ccass_sqlite_path)))
