from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.data_quality import structured_warning
from app.models import OfficersMetadata, OfficersResponse
from ccass_core.normalize import normalize_stock_code

OFFICERS_SOURCE_PENDING_NAME = "Officers source pending"
OFFICERS_SOURCE_PENDING_URL: str | None = None


class OfficersSource(Protocol):
    async def get_officers(self, code: str | int) -> OfficersResponse: ...


class PendingOfficersSource:
    async def get_officers(self, code: str | int) -> OfficersResponse:
        normalized = normalize_stock_code(code)
        return OfficersResponse(
            metadata=OfficersMetadata(
                code=normalized,
                source_name=OFFICERS_SOURCE_PENDING_NAME,
                source_url=OFFICERS_SOURCE_PENDING_URL,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                officers_count=0,
                source_status="pending",
            ),
            officers=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "OFFICERS_SOURCE_PENDING",
                    "Officers source is pending approval; placeholder read path only.",
                )
            ],
        )
