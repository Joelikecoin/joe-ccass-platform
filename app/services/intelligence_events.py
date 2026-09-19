from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from functools import lru_cache

from app.config import get_settings
from app.models import IntelligenceEventRow, IntelligenceEventsMetadata, IntelligenceEventsResponse
from app.storage.disclosure_interests import DisclosureInterestRepository
from app.storage.document_entities import DocumentEntityRepository
from app.storage.history import NormalizedSnapshotRepository
from app.storage.intelligence_events import IntelligenceEventRepository
from ccass_core.normalize import normalize_stock_code

DEFAULT_LOOKBACK_DAYS = 5 * 365


class IntelligenceEventsService:
    """Phase-1 unified event layer v0: derives corporate-intelligence events
    from the persisted DI (official) and document-entity (extracted) stores,
    upserts them idempotently into the permanent evidence cache, and serves
    the persisted layer."""

    def __init__(self, disclosure_repository=None, entity_repository=None, event_repository=None):
        self.disclosure_repository = disclosure_repository
        self.entity_repository = entity_repository
        self.event_repository = event_repository

    async def get_events(self, code: str | int, *, start_date: date | None = None, end_date: date | None = None) -> IntelligenceEventsResponse:
        normalized = normalize_stock_code(code)
        end = end_date or datetime.now(UTC).date()
        start = start_date or end - timedelta(days=DEFAULT_LOOKBACK_DAYS)
        response = await self.build_events(normalized, start_date=start, end_date=end)
        if self.event_repository is not None and response.events:
            self.event_repository.save(response)
            persisted = self.event_repository.load(normalized, start_date=start, end_date=end)
            response = IntelligenceEventsResponse(
                metadata=IntelligenceEventsMetadata(
                    code=normalized,
                    fetched_at=response.metadata.fetched_at,
                    source_status=response.metadata.source_status,
                    event_count=len(persisted),
                    coverage_start=start,
                    coverage_end=end,
                ),
                events=persisted,
                data_quality_warnings=response.data_quality_warnings,
            )
        return response

    async def build_events(self, code: str | int, *, start_date: date, end_date: date) -> IntelligenceEventsResponse:
        normalized = normalize_stock_code(code)
        now = datetime.now(UTC)
        warnings: list[str] = []
        events: list[IntelligenceEventRow] = []

        if self.disclosure_repository is not None:
            try:
                for row in self.disclosure_repository.load_rows(normalized, start_date=start_date, end_date=end_date):
                    events.append(IntelligenceEventRow(
                        stock_code=normalized,
                        event_type="disclosure_of_interest",
                        announce_date=row.event_date,
                        shares_after=row.present_balance,
                        price=row.average_price,
                        counterparty=row.filer,
                        source_document=row.filing_id,
                        source_url=row.source_url,
                        confidence="official",
                        extraction_method="dion-official-table",
                        retrieved_at=row.retrieved_at,
                        provenance=row.provenance,
                    ))
            except Exception as exc:
                warnings.append(f"DI_SOURCE_READ_FAILED:{type(exc).__name__}")

        if self.entity_repository is not None:
            try:
                for row in self.entity_repository.load_rows(normalized, start_date=start_date, end_date=end_date):
                    retrieved = row.retrieved_at
                    if isinstance(retrieved, str):
                        retrieved = datetime.fromisoformat(retrieved)
                    events.append(IntelligenceEventRow(
                        stock_code=normalized,
                        event_type=f"corporate_action:{row.entity_type}",
                        announce_date=row.announcement_date,
                        counterparty=row.entity_name,
                        entity_name=row.entity_name,
                        source_document=row.document_id,
                        source_url=row.source_url,
                        confidence="extracted",
                        extraction_method=f"pdf-label-extraction:{row.document_type}",
                        retrieved_at=retrieved,
                        provenance=row.provenance,
                    ))
            except Exception as exc:
                warnings.append(f"ENTITY_SOURCE_READ_FAILED:{type(exc).__name__}")

        unique: dict[tuple, IntelligenceEventRow] = {}
        for event in events:
            key = (event.event_type, event.announce_date, event.source_document, event.counterparty, event.entity_name)
            unique[key] = event
        ordered = sorted(unique.values(), key=lambda e: (e.announce_date, e.event_type, str(e.counterparty)), reverse=True)

        return IntelligenceEventsResponse(
            metadata=IntelligenceEventsMetadata(
                code=normalized,
                fetched_at=now,
                source_status="ready" if ordered else ("partial" if warnings else "unavailable"),
                event_count=len(ordered),
                coverage_start=start_date,
                coverage_end=end_date,
            ),
            events=ordered,
            data_quality_warnings=warnings,
        )


@lru_cache
def get_intelligence_events_service() -> IntelligenceEventsService:
    settings = get_settings()
    normalized_repository = NormalizedSnapshotRepository(settings.ccass_sqlite_path)
    return IntelligenceEventsService(
        disclosure_repository=DisclosureInterestRepository(normalized_repository),
        entity_repository=DocumentEntityRepository(normalized_repository),
        event_repository=IntelligenceEventRepository(normalized_repository),
    )
