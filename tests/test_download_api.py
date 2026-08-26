from __future__ import annotations

import asyncio
from base64 import b64decode
from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import app
from app import mcp_server


def _make_bundle() -> SimpleNamespace:
    prepared_response = SimpleNamespace(
        metadata=SimpleNamespace(code="01592"),
        model_dump_json=lambda indent=2: "{\n  \"code\": \"01592\"\n}",
    )
    prepared = SimpleNamespace(filename="01592_ccass.md", response=prepared_response)
    live_artifacts = SimpleNamespace(
        combined_csv_bytes=b"live-csv",
        combined_csv_filename="live.csv",
        workbook_bytes=b"live-xlsx",
        workbook_filename="live.xlsx",
        json_bytes=b'{"kind":"live"}',
        json_filename="live.json",
    )
    ccass_artifacts = SimpleNamespace(
        combined_csv_bytes=b"ccass-csv",
        combined_csv_filename="ccass.csv",
        workbook_bytes=b"ccass-xlsx",
        workbook_filename="ccass.xlsx",
        raw_preview_json_bytes=b'[{"kind":"raw"}]',
        raw_preview_json_filename="raw.json",
    )
    return SimpleNamespace(
        live_artifacts=live_artifacts,
        ccass_artifacts=ccass_artifacts,
        prepared=prepared,
        resolved_code="01592",
        live_product=object(),
    )


def test_canonical_download_api_routes_stream_expected_artifacts(monkeypatch):
    bundle = _make_bundle()

    async def fake_build_bundle(**_: object) -> SimpleNamespace:
        return bundle

    monkeypatch.setattr("app.api._build_bundle", fake_build_bundle)
    monkeypatch.setattr("app.api._bundle_markdown", lambda bundle, section, locale: f"{section}:{locale}")

    client = TestClient(app)

    live_md = client.get("/api/v1/stocks/01592/download/live/md")
    ccass_json = client.get("/api/v1/stocks/01592/download/ccass/json")
    raw_json = client.get("/api/v1/stocks/01592/download/raw_previews/json")
    raw_previews = client.get("/api/v1/stocks/01592/raw-previews")

    assert live_md.status_code == 200
    assert live_md.headers["content-disposition"] == 'attachment; filename="01592_live_markdown.md"'
    assert live_md.text == "live:en"

    assert ccass_json.status_code == 200
    assert ccass_json.headers["content-disposition"] == 'attachment; filename="01592_ccass.json"'
    assert ccass_json.text == "{\n  \"code\": \"01592\"\n}"

    assert raw_json.status_code == 200
    assert raw_json.headers["content-disposition"] == 'attachment; filename="raw.json"'
    assert raw_json.text == '[{"kind":"raw"}]'

    assert raw_previews.status_code == 200
    assert raw_previews.json() == {
        "stock_code": "01592",
        "locale": "en",
        "tables": [{"kind": "raw"}],
    }


def test_canonical_download_api_rejects_unknown_section(monkeypatch):
    bundle = _make_bundle()

    async def fake_build_bundle(**_: object) -> SimpleNamespace:
        return bundle

    monkeypatch.setattr("app.api._build_bundle", fake_build_bundle)
    client = TestClient(app)

    response = client.get("/api/v1/stocks/01592/download/unknown/json")
    assert response.status_code == 404


def test_mcp_download_artifact_matches_canonical_api_shapes(monkeypatch):
    bundle = _make_bundle()

    async def fake_build_bundle(**_: object) -> SimpleNamespace:
        return bundle

    monkeypatch.setattr("app.mcp_server._build_bundle", fake_build_bundle)
    monkeypatch.setattr("app.mcp_server._bundle_markdown", lambda bundle, section, locale: f"{section}:{locale}")

    result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="raw_previews",
            kind="json",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )

    assert result["section"] == "raw_previews"
    assert result["kind"] == "json"
    assert result["filename"] == "raw.json"
    assert result["media_type"] == "application/json"
    assert b64decode(result["content_b64"]).decode("utf-8") == '[{"kind":"raw"}]'


def test_mcp_raw_previews_matches_canonical_api_shapes(monkeypatch):
    bundle = _make_bundle()

    async def fake_build_bundle(**_: object) -> SimpleNamespace:
        return bundle

    monkeypatch.setattr("app.mcp_server._build_bundle", fake_build_bundle)

    result = asyncio.run(
        mcp_server.get_raw_previews.fn(
            "01592",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )

    assert result == {
        "stock_code": "01592",
        "locale": "zh_HK",
        "tables": [{"kind": "raw"}],
    }


def test_mcp_changes_big_changes_and_concentration_delegate_to_services(monkeypatch):
    class _FixtureChangesService:
        def get_changes(self, code, *, snapshot_date, compare_date):
            return SimpleNamespace(
                model_dump=lambda mode="json": {
                    "kind": "changes",
                    "code": code,
                    "snapshot_date": snapshot_date.isoformat(),
                    "compare_date": compare_date.isoformat(),
                }
            )

    class _FixtureBigChangesService:
        def get_big_changes(self, code, *, snapshot_date, compare_date, threshold_shares):
            return SimpleNamespace(
                model_dump=lambda mode="json": {
                    "kind": "big_changes",
                    "code": code,
                    "snapshot_date": snapshot_date.isoformat(),
                    "compare_date": compare_date.isoformat(),
                    "threshold_shares": threshold_shares,
                }
            )

    class _FixtureConcentrationService:
        def get_concentration(self, code, *, snapshot_date, top_holders_limit):
            return SimpleNamespace(
                model_dump=lambda mode="json": {
                    "kind": "concentration",
                    "code": code,
                    "snapshot_date": snapshot_date.isoformat(),
                    "top_holders_limit": top_holders_limit,
                }
            )

    monkeypatch.setattr("app.mcp_server.get_changes_service", lambda: _FixtureChangesService())
    monkeypatch.setattr("app.mcp_server.get_big_changes_service", lambda: _FixtureBigChangesService())
    monkeypatch.setattr("app.mcp_server.get_concentration_service", lambda: _FixtureConcentrationService())

    changes = asyncio.run(
        mcp_server.get_changes.fn(
            "01592",
            snapshot_date=date(2026, 8, 14),
            compare_date=date(2026, 8, 13),
        )
    )
    big_changes = asyncio.run(
        mcp_server.get_big_changes.fn(
            "01592",
            snapshot_date=date(2026, 8, 14),
            compare_date=date(2026, 8, 13),
            threshold_shares=123,
        )
    )
    concentration = asyncio.run(
        mcp_server.get_concentration.fn(
            "01592",
            snapshot_date=date(2026, 8, 14),
            top_holders_limit=8,
        )
    )

    assert changes["kind"] == "changes"
    assert changes["code"] == "01592"
    assert changes["snapshot_date"] == "2026-08-14"
    assert big_changes["kind"] == "big_changes"
    assert big_changes["threshold_shares"] == 123
    assert concentration["kind"] == "concentration"
    assert concentration["top_holders_limit"] == 8


def test_mcp_holdings_alias_matches_stock_summary(monkeypatch):
    class _FixtureService:
        async def get_stock_data(self, code, holdings_limit=15):
            return SimpleNamespace(
                model_dump=lambda mode="json": {
                    "code": code,
                    "holdings_limit": holdings_limit,
                    "kind": "summary",
                }
            )

    monkeypatch.setattr("app.mcp_server.get_ccass_service", lambda: _FixtureService())

    result = asyncio.run(mcp_server.get_holdings.fn("01592", holdings_limit=17))
    assert result == {"code": "01592", "holdings_limit": 17, "kind": "summary"}


def test_history_api_and_mcp_expose_snapshot_dates(monkeypatch):
    class _FixtureRepository:
        def available_dates(self, code: str, *, include_partial: bool = False):
            assert code == "01592"
            return [date(2026, 8, 13), date(2026, 8, 14)]

        def history_bounds(self, code: str):
            assert code == "01592"
            return SimpleNamespace(
                earliest_snapshot_date=date(2026, 8, 13),
                latest_snapshot_date=date(2026, 8, 14),
                snapshot_count=2,
                date_count=2,
            )

    monkeypatch.setattr("app.mcp_server.NormalizedSnapshotRepository", lambda *_args, **_kwargs: _FixtureRepository())

    client = TestClient(app)
    from app.api import get_snapshot_repository

    client.app.dependency_overrides[get_snapshot_repository] = lambda: _FixtureRepository()
    response = client.get("/api/v1/stocks/01592/history", params={"include_partial": "false"})
    assert response.status_code == 200
    assert response.json() == {
        "stock_code": "01592",
        "include_partial": False,
        "available": True,
        "snapshot_count": 2,
        "earliest_snapshot_date": "2026-08-13",
        "latest_snapshot_date": "2026-08-14",
        "history_bounds": {
            "earliest": "2026-08-13",
            "latest": "2026-08-14",
            "snapshot_count": 2,
            "date_count": 2,
        },
        "dates": ["2026-08-13", "2026-08-14"],
    }

    mcp_result = asyncio.run(mcp_server.get_snapshot_history.fn("01592", include_partial=False))
    assert mcp_result == response.json()
    client.app.dependency_overrides.clear()
