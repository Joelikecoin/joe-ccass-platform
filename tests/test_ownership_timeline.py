import pytest

from datetime import date, datetime, UTC

from fastapi.testclient import TestClient

from app.models import DisclosureInterestRow
from app.portal_8504 import app as portal_app
from app.services.ownership_timeline import OwnershipTimelineService, get_ownership_timeline_service


def _row(event_date, filer, prev, present, filing):
    return DisclosureInterestRow(
        filing_id=filing,
        stock_code="02318",
        event_date=event_date,
        filer=filer,
        classification="substantial_shareholder",
        shares_involved=100000,
        previous_balance=prev,
        present_balance=present,
        percentage=5.0,
        average_price=276.25,
        reason="1104 (L)",
        source_url=f"https://di.hkex.com.hk/di/{filing}",
        retrieved_at=datetime(2026, 9, 19, tzinfo=UTC),
    )


class _FakeRepo:
    def load_rows(self, stock_code, *, start_date, end_date):
        # real DION rows carry NO previous_balance — the timeline chains it
        return [
            _row(date(2026, 9, 3), "BlackRock, Inc.", None, 1_065_871_110, "CS1"),
            _row(date(2026, 8, 19), "BlackRock, Inc.", None, 1_065_000_000, "CS0"),
            _row(date(2026, 9, 1), "Lei Jun", None, 3_989_013_134, "DA1"),
        ]


@pytest.mark.asyncio
async def test_ownership_timeline_groups_movements_and_directions():
    service = OwnershipTimelineService(disclosure_repository=_FakeRepo())
    response = await service.get_timeline("02318", start_date=date(2024, 9, 19), end_date=date(2026, 9, 19))

    assert response.metadata.source_status == "ready"
    assert response.metadata.filers == 2
    assert response.metadata.movements == 3
    blackrock = next(t for t in response.timelines if t.filer == "BlackRock, Inc.")
    assert blackrock.movements_count == 2
    assert blackrock.increases == 1 and blackrock.decreases == 0  # first-ever filing counts as unknown
    assert blackrock.movements[0].filing_id == "CS1"  # newest first
    assert blackrock.movements[0].direction == "increase"
    assert blackrock.movements[0].change_shares == 871_110  # chained from CS0's balance
    assert blackrock.movements[1].direction == "unknown"  # first-ever filing: no prior balance
    assert blackrock.latest_present_balance == 1_065_871_110


@pytest.mark.asyncio
async def test_ownership_timeline_filters_by_filer():
    service = OwnershipTimelineService(disclosure_repository=_FakeRepo())
    response = await service.get_timeline("02318", filer="lei jun")
    assert response.metadata.filers == 1
    assert response.timelines[0].filer == "Lei Jun"


@pytest.mark.asyncio
async def test_ownership_timeline_reports_absence_fail_loud():
    class _EmptyRepo:
        def load_rows(self, stock_code, *, start_date, end_date):
            return []

    service = OwnershipTimelineService(disclosure_repository=_EmptyRepo())
    response = await service.get_timeline("00941")
    assert response.metadata.source_status == "unavailable"
    assert any(w.startswith("NO_OWNERSHIP_MOVEMENTS") for w in response.data_quality_warnings)


def test_ownership_timeline_route_serves_from_overridden_service():
    from app.models import OwnershipTimelineMetadata, OwnershipTimelineResponse

    response = OwnershipTimelineResponse(metadata=OwnershipTimelineMetadata(code="02318", fetched_at=datetime.now(UTC), source_status="ready", filers=1))

    class _Service:
        async def get_timeline(self, code, *, start_date=None, end_date=None, filer=None):
            return response

    portal_app.dependency_overrides[get_ownership_timeline_service] = lambda: _Service()
    try:
        http = TestClient(portal_app).get("/api/v1/stocks/02318/ownership-timeline?filer=blackrock")
    finally:
        portal_app.dependency_overrides.pop(get_ownership_timeline_service, None)

    assert http.status_code == 200
    assert http.json()["metadata"]["filers"] == 1
