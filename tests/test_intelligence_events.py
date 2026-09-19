from datetime import date, datetime, UTC
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.models import DisclosureInterestRow, DocumentEntityRow, IntelligenceEventRow, IntelligenceEventsMetadata, IntelligenceEventsResponse
from app.services.intelligence_events import IntelligenceEventsService
from app.storage.intelligence_events import IntelligenceEventRepository
from app.storage.history import NormalizedSnapshotRepository
from app.portal_8504 import app as portal_app
from app.services.intelligence_events import get_intelligence_events_service


def _di_row():
    return DisclosureInterestRow(
        filing_id="CS20260908E00043",
        stock_code="02318",
        event_date=date(2026, 9, 3),
        filer="BlackRock, Inc.",
        classification="substantial_shareholder",
        shares_involved=726000,
        present_balance=1065871110,
        percentage=4.99,
        average_price=276.25,
        source_url="https://di.hkex.com.hk/di/NSForm2.aspx?fn=CS20260908E00043",
        retrieved_at=datetime(2026, 9, 19, tzinfo=UTC),
    )


def _entity_row():
    return DocumentEntityRow(
        stock_code="02318",
        document_id="2026081300797",
        document_type="general offer document",
        entity_type="offeror",
        entity_name="Ping An Insurance (Group) Company Limited",
        direct_source_fact="The Offeror Ping An Insurance (Group) Company Limited made the offers.",
        source_url="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0813/2026081300797.pdf",
        announcement_date=date(2026, 8, 13),
        retrieved_at=datetime(2026, 9, 19, tzinfo=UTC),
    )


class _FakeDisclosureRepo:
    def load_rows(self, stock_code, *, start_date, end_date):
        return [_di_row()]


class _FakeEntityRepo:
    def load_rows(self, stock_code, *, start_date, end_date):
        return [_entity_row()]


def _service(tmp_path: Path, disclosure=True, entities=True):
    event_repo = IntelligenceEventRepository(NormalizedSnapshotRepository(tmp_path / "events.sqlite"))
    return IntelligenceEventsService(
        disclosure_repository=_FakeDisclosureRepo() if disclosure else None,
        entity_repository=_FakeEntityRepo() if entities else None,
        event_repository=event_repo,
    ), event_repo


@pytest.mark.asyncio
async def test_event_layer_derives_official_and_extracted_events(tmp_path: Path):
    service, event_repo = _service(tmp_path)
    response = await service.get_events("02318", start_date=date(2024, 9, 19), end_date=date(2026, 9, 19))
    print("DBG path:", event_repo.repository.path, event_repo.repository.path.exists())
    import sqlite3
    conn = sqlite3.connect(str(event_repo.repository.path))
    print("DBG db rows:", conn.execute("SELECT COUNT(*) FROM intelligence_events").fetchone())
    conn.close()
    print("DBG served:", response.metadata.event_count, len(response.events), response.data_quality_warnings)

    assert response.metadata.event_count == 2
    di_events = [e for e in response.events if e.event_type == "disclosure_of_interest"]
    assert len(di_events) == 1
    assert di_events[0].confidence == "official"
    assert di_events[0].counterparty == "BlackRock, Inc."
    assert di_events[0].shares_after == 1065871110
    ca_events = [e for e in response.events if e.event_type == "corporate_action:offeror"]
    assert len(ca_events) == 1
    assert ca_events[0].confidence == "extracted"
    assert ca_events[0].entity_name == "Ping An Insurance (Group) Company Limited"


@pytest.mark.asyncio
async def test_event_layer_repository_roundtrip_is_idempotent(tmp_path: Path):
    service, event_repo = _service(tmp_path)
    first = await service.get_events("02318", start_date=date(2024, 9, 19), end_date=date(2026, 9, 19))
    second = await service.get_events("02318", start_date=date(2024, 9, 19), end_date=date(2026, 9, 19))

    assert len(second.events) == len(first.events) == 2
    loaded = event_repo.load("02318")
    assert len(loaded) == 2


def test_intelligence_events_route_serves_from_overridden_service():
    events = IntelligenceEventsResponse(
        metadata=IntelligenceEventsMetadata(code="02318", fetched_at=datetime.now(UTC), source_status="ready", event_count=1),
        events=[
            IntelligenceEventRow(
                stock_code="02318",
                event_type="disclosure_of_interest",
                announce_date=date(2026, 9, 3),
                counterparty="BlackRock, Inc.",
                source_document="CS1",
                source_url="https://di.hkex.com.hk/x",
                confidence="official",
                extraction_method="test",
                retrieved_at=datetime.now(UTC),
            )
        ],
    )

    class _Service:
        async def get_events(self, code, *, start_date=None, end_date=None):
            return events

    portal_app.dependency_overrides[get_intelligence_events_service] = lambda: _Service()
    try:
        response = TestClient(portal_app).get("/api/v1/stocks/02318/intelligence-events")
    finally:
        portal_app.dependency_overrides.pop(get_intelligence_events_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["event_count"] == 1
    assert body["events"][0]["confidence"] == "official"
