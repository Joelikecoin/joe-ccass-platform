from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.data_quality import structured_warning
from app.models import CapitalInformationMetadata, CapitalInformationResponse
from ccass_core.normalize import normalize_stock_code

CAPITAL_INFORMATION_SOURCE_PENDING_NAME = "Capital information source pending"
CAPITAL_INFORMATION_SOURCE_PENDING_URL: str | None = None


class CapitalInformationSource(Protocol):
    async def get_capital_information(self, code: str | int) -> CapitalInformationResponse: ...


class PendingCapitalInformationSource:
    async def get_capital_information(self, code: str | int) -> CapitalInformationResponse:
        normalized = normalize_stock_code(code)
        return CapitalInformationResponse(
            metadata=CapitalInformationMetadata(
                code=normalized,
                source_name=CAPITAL_INFORMATION_SOURCE_PENDING_NAME,
                source_url=CAPITAL_INFORMATION_SOURCE_PENDING_URL,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                capital_information_count=0,
                source_status="pending",
            ),
            capital_information=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "CAPITAL_INFORMATION_SOURCE_PENDING",
                    "Capital information source is pending approval; placeholder read path only.",
                )
            ],
        )
