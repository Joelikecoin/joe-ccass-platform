import json

from fastapi.testclient import TestClient

from app.api import app, get_settings, get_snapshot_repository
from app.config import Settings
from app.domain.history import HistoricalSnapshot
from app.sources.registry import (
    GOOGLE_DRIVE_CSV_SOURCE_ID,
    HKEX_SDW_SOURCE_ID,
    WEBBSITE_SOURCE_ID,
)


def test_source_status_api_exposes_safe_registry_diagnostics():
    client = TestClient(app)

    response = client.get("/api/v1/sources/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["source_count"] == 3
    assert [item["source_id"] for item in body["sources"]] == [
        WEBBSITE_SOURCE_ID,
        GOOGLE_DRIVE_CSV_SOURCE_ID,
        HKEX_SDW_SOURCE_ID,
    ]
    webbsite = body["sources"][0]
    google = body["sources"][1]
    hkex = body["sources"][2]
    assert webbsite["availability"]["status"] == "active"
    assert google["availability"]["status"] in {"active", "fallback", "unavailable", "disabled", "unverified"}
    assert hkex["safe_hostname"] == "www3.hkexnews.hk"
    assert webbsite["provenance"]["parser_id"]
    assert "authorization" not in json.dumps(body).lower()


def test_source_status_api_redacts_sensitive_settings():
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="must-not-appear",
        ccass_csv_url=(
            "https://drive.google.com/file/d/registry-fixture/view"
            "?usp=sharing&resourcekey=private-resource-key"
        ),
    )
    try:
        client = TestClient(app)
        response = client.get("/api/v1/sources/status", headers={"X-API-Key": "must-not-appear"})
        assert response.status_code == 200
        rendered = response.text.lower()
        for forbidden in (
            "must-not-appear",
            "registry-fixture",
            "private-resource-key",
            "authorization",
            "cookie",
            "c:\\users\\",
        ):
            assert forbidden.lower() not in rendered
    finally:
        app.dependency_overrides.clear()


def test_stock_rainbow_api_surfaces_local_snapshot_history(current_response, previous_response):
    snapshots = [
        HistoricalSnapshot.from_response(previous_response, source_id="webbsite"),
        HistoricalSnapshot.from_response(current_response, source_id="webbsite"),
    ]

    class FakeRepository:
        def available_dates(self, code: str, *, source_id: str | None = None, include_partial: bool = True):
            return tuple(snapshot.snapshot_date for snapshot in snapshots)

        def date_range(
            self,
            code: str,
            *,
            date_from,
            date_to,
            source_id: str | None = None,
            include_partial: bool = True,
        ):
            return snapshots

    app.dependency_overrides[get_snapshot_repository] = lambda: FakeRepository()
    try:
        client = TestClient(app)
        response = client.get("/api/v1/stocks/01592/rainbow")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["stock_code"] == "01592"
        assert body["available"] is True
        assert body["snapshot_count"] == 2
        assert body["earliest_snapshot_date"] == snapshots[0].snapshot_date.isoformat()
        assert body["latest_snapshot_date"] == snapshots[-1].snapshot_date.isoformat()
        assert body["top_ids"]
        assert len(body["snapshots"]) == 2
        assert body["snapshots"][0]["date"] == snapshots[0].snapshot_date.isoformat()
        assert body["snapshots"][1]["participant_count"] == snapshots[1].participant_count
    finally:
        app.dependency_overrides.clear()


def test_stock_summary_alias_is_present_in_openapi():
    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    assert "/api/v1/stocks/{stock_code}" in schema["paths"]
    assert "/api/v1/sources/status" in schema["paths"]
    assert "/api/v1/stocks/{stock_code}/rainbow" in schema["paths"]
