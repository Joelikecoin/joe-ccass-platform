from datetime import date, datetime, UTC
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.portal_8504 import app as portal_app
from app.storage.history import NormalizedSnapshotRepository
from app.storage.share_capital_history import ShareCapitalHistoryRepository


def _response(code="02020"):
    from app.models import ShareCapitalHistoryMetadata, ShareCapitalHistoryRow, ShareCapitalHistoryResponse

    rows = [
        ShareCapitalHistoryRow(announce_date=date(2026, 8, 19), shares_million=10295.0, shares_approx="10,295M", reason="interim results", reason_tags=["results"], source="HKEXnews", source_url="https://www1.hkexnews.hk/a.pdf"),
        ShareCapitalHistoryRow(announce_date=date(2025, 3, 26), shares_million=10180.0, reason="annual results", source="HKEXnews", source_url="https://www1.hkexnews.hk/b.pdf"),
    ]
    return ShareCapitalHistoryResponse(metadata=ShareCapitalHistoryMetadata(code=code, source_name="test", fetched_at=datetime.now(UTC), source_status="ready"), rows=rows)


def test_share_capital_repository_roundtrip_is_idempotent(tmp_path: Path):
    repo = ShareCapitalHistoryRepository(NormalizedSnapshotRepository(tmp_path / "sc.sqlite"))
    response = _response()
    repo.save(response)
    repo.save(response)
    loaded = repo.load("02020")
    assert loaded is not None and len(loaded.rows) == 2
    filtered = repo.load("02020", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    assert filtered is not None and len(filtered.rows) == 1
    assert filtered.rows[0].shares_million == 10295.0


@pytest.mark.asyncio
async def test_share_capital_events_derived_into_intelligence_layer(tmp_path: Path):
    from app.services.intelligence_events import IntelligenceEventsService
    from app.storage.intelligence_events import IntelligenceEventRepository

    repo = ShareCapitalHistoryRepository(NormalizedSnapshotRepository(tmp_path / "sc.sqlite"))
    repo.save(_response())
    service = IntelligenceEventsService(share_capital_repository=repo, event_repository=IntelligenceEventRepository(NormalizedSnapshotRepository(tmp_path / "ev.sqlite")))
    response = await service.get_events("02020", start_date=date(2024, 9, 19), end_date=date(2026, 9, 19))
    sc = [e for e in response.events if e.event_type == "share_capital_change"]
    assert len(sc) == 2
    assert sc[0].shares_after == 10295.0
    assert sc[0].confidence == "extracted"


def test_share_capital_job_routes_require_auth(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr("app.portal_8504.get_settings", lambda: SimpleNamespace(api_key="configured", request_timeout_seconds=90.0))
    client = TestClient(portal_app)
    assert client.post("/admin/share-capital/job?stock_code=02020").status_code == 401
    assert client.get("/admin/share-capital/job/nope?key=configured").status_code == 404
