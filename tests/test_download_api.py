from __future__ import annotations

import asyncio
import json
from base64 import b64decode
from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import app
from app import mcp_server


def _make_bundle() -> SimpleNamespace:
    prepared_response = SimpleNamespace(
        metadata=SimpleNamespace(code="01592"),
        holdings=[
            {
                "rank": 1,
                "participant_id": "P1",
                "participant": "Alpha Holdings",
                "shares": 1234,
                "last_change": "2026-08-14",
                "pct_of_issued": 1.2345,
                "pct_of_ccass": 2.3456,
                "cumulative_pct_of_issued": 1.2345,
                "participant_category": "Nominee",
            }
        ],
        changes=SimpleNamespace(
            changes=[
                {
                    "participant_id": "P1",
                    "participant": "Alpha Holdings",
                    "shares_before": 1000,
                    "shares_after": 1234,
                    "shares_change": 234,
                    "percent_before": 1.0,
                    "percent_after": 1.2345,
                    "percent_change": 0.2345,
                    "relative_change_percent": 23.45,
                    "new_participant": False,
                    "removed_participant": False,
                    "status": "increased",
                }
            ]
        ),
        big_changes=SimpleNamespace(
            big_changes=[
                {
                    "participant_id": "P1",
                    "participant": "Alpha Holdings",
                    "shares_before": 1000,
                    "shares_after": 1234,
                    "shares_change": 234,
                    "percent_before": 1.0,
                    "percent_after": 1.2345,
                    "percent_change": 0.2345,
                    "relative_change_percent": 23.45,
                    "new_participant": False,
                    "removed_participant": False,
                    "status": "increased",
                }
            ]
        ),
        concentration=SimpleNamespace(
            participant_ranking=[
                {
                    "rank": 1,
                    "participant_id": "P1",
                    "participant": "Alpha Holdings",
                    "shares": 1234,
                    "last_change": "2026-08-14",
                    "pct_of_issued": 1.2345,
                    "pct_of_ccass": 2.3456,
                    "cumulative_pct_of_issued": 1.2345,
                    "participant_category": "Nominee",
                }
            ]
        ),
        announcements=SimpleNamespace(
            announcements=[
                {
                    "announcement_date": "2026-08-14",
                    "title": "Sample HKEX announcement",
                    "source": "HKEXnews",
                    "link": "https://example.invalid/announcement.pdf",
                }
            ]
        ),
        price_history=SimpleNamespace(
            prices=[
                {
                    "price_date": "2026-08-14",
                    "open": 1.0,
                    "high": 2.0,
                    "low": 0.5,
                    "close": 1.5,
                    "vwap": 1.25,
                    "adjusted_close": 1.5,
                    "volume": 1000,
                    "turnover": 1500.0,
                    "price_source": "HKEX",
                    "turnover_est": 1500.0,
                    "vwap_est": 1.25,
                }
            ]
        ),
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
        raw_preview_summary_bytes=b"summary-csv",
        raw_preview_summary_filename="summary.csv",
        raw_preview_holdings_bytes=b"holdings-csv",
        raw_preview_holdings_filename="holdings.csv",
        raw_preview_json_bytes=json.dumps(
            {
                "stock_code": "01592",
                "metadata": {
                    "code": "01592",
                    "name": None,
                    "issue_id": None,
                    "holdings_date": None,
                    "data_as_of": None,
                    "fetched_at": None,
                    "source_url": None,
                    "source_name": None,
                    "cached": False,
                    "settlement_note": None,
                    "attribution": None,
                },
                "warnings": [],
                "tables": [{"kind": "raw"}],
            }
        ).encode("utf-8"),
        raw_preview_json_filename="raw.json",
    )
    return SimpleNamespace(
        live_artifacts=live_artifacts,
        ccass_artifacts=ccass_artifacts,
        prepared=prepared,
        resolved_code="01592",
        live_product=object(),
    )


def test_canonical_download_api_routes_stream_expected_artifacts(monkeypatch, tmp_path):
    bundle = _make_bundle()
    sqlite_path = tmp_path / "sqlite-backup.db"
    sqlite_path.write_bytes(b"sqlite-bytes")
    rainbow_payload = {
        "status": "ok",
        "stock_code": "01592",
        "available": True,
        "snapshot_count": 1,
        "earliest_snapshot_date": "2026-08-14",
        "latest_snapshot_date": "2026-08-14",
        "top_ids": ["P1"],
        "snapshots": [
            {
                "date": "2026-08-14",
                "participant_count": 1,
                "source_name": "HKEX SDW",
                "stacks": [
                    {"participant_id": "P1", "participant": "Alpha Holdings", "pct": 12.34},
                    {"participant_id": "others", "participant": "Others", "pct": 87.66},
                ],
            }
        ],
        "warnings": [],
    }

    async def fake_build_bundle(**_: object) -> SimpleNamespace:
        return bundle

    async def fake_get_stock_rainbow(stock_code, repository=None):  # type: ignore[unused-argument]
        return rainbow_payload

    monkeypatch.setattr("app.api._build_bundle", fake_build_bundle)
    monkeypatch.setattr("app.api._bundle_markdown", lambda bundle, section, locale: f"{section}:{locale}")
    monkeypatch.setattr("app.api.get_settings", lambda: SimpleNamespace(ccass_sqlite_path=sqlite_path))
    monkeypatch.setattr("app.api.get_stock_rainbow", fake_get_stock_rainbow)

    client = TestClient(app)

    live_md = client.get("/api/v1/stocks/01592/download/live/md")
    ccass_json = client.get("/api/v1/stocks/01592/download/ccass/json")
    raw_json = client.get("/api/v1/stocks/01592/download/raw_previews/json")
    raw_summary_csv = client.get("/api/v1/stocks/01592/download/raw_previews/summary_csv")
    raw_holdings_csv = client.get("/api/v1/stocks/01592/download/raw_previews/holdings_csv")
    holdings_csv = client.get("/api/v1/stocks/01592/download/holdings/csv")
    changes_csv = client.get("/api/v1/stocks/01592/download/changes/csv")
    big_changes_csv = client.get("/api/v1/stocks/01592/download/big_changes/csv")
    concentration_csv = client.get("/api/v1/stocks/01592/download/concentration/csv")
    announcements_csv = client.get("/api/v1/stocks/01592/download/announcements/csv")
    price_history_csv = client.get("/api/v1/stocks/01592/download/price_history/csv")
    rainbow_json = client.get("/api/v1/stocks/01592/download/rainbow/json")
    rainbow_csv = client.get("/api/v1/stocks/01592/download/rainbow/csv")
    ccass_sqlite = client.get("/api/v1/stocks/01592/download/ccass/sqlite")
    raw_previews = client.get("/api/v1/stocks/01592/raw-previews")

    assert live_md.status_code == 200
    assert live_md.headers["content-disposition"] == 'attachment; filename="01592_live_markdown.md"'
    assert live_md.text == "live:en"

    assert ccass_json.status_code == 200
    assert ccass_json.headers["content-disposition"] == 'attachment; filename="01592_ccass.json"'
    assert ccass_json.text == "{\n  \"code\": \"01592\"\n}"

    assert raw_json.status_code == 200
    assert raw_json.headers["content-disposition"] == 'attachment; filename="raw.json"'
    assert raw_json.json() == {
        "stock_code": "01592",
        "metadata": {
            "code": "01592",
            "name": None,
            "issue_id": None,
            "holdings_date": None,
            "data_as_of": None,
            "fetched_at": None,
            "source_url": None,
            "source_name": None,
            "cached": False,
            "settlement_note": None,
            "attribution": None,
        },
        "warnings": [],
        "tables": [{"kind": "raw"}],
    }

    assert raw_summary_csv.status_code == 200
    assert raw_summary_csv.headers["content-disposition"] == 'attachment; filename="summary.csv"'
    assert raw_summary_csv.text == "summary-csv"

    assert raw_holdings_csv.status_code == 200
    assert raw_holdings_csv.headers["content-disposition"] == 'attachment; filename="holdings.csv"'
    assert raw_holdings_csv.text == "holdings-csv"

    assert holdings_csv.status_code == 200
    assert holdings_csv.headers["content-disposition"] == 'attachment; filename="01592_holdings.csv"'
    assert "Alpha Holdings" in holdings_csv.text

    assert changes_csv.status_code == 200
    assert changes_csv.headers["content-disposition"] == 'attachment; filename="01592_changes.csv"'
    assert "shares_before" in changes_csv.text

    assert big_changes_csv.status_code == 200
    assert big_changes_csv.headers["content-disposition"] == 'attachment; filename="01592_big_changes.csv"'
    assert "shares_after" in big_changes_csv.text

    assert concentration_csv.status_code == 200
    assert concentration_csv.headers["content-disposition"] == 'attachment; filename="01592_concentration.csv"'
    assert "Alpha Holdings" in concentration_csv.text

    assert announcements_csv.status_code == 200
    assert announcements_csv.headers["content-disposition"] == 'attachment; filename="01592_announcements.csv"'
    assert "Sample HKEX announcement" in announcements_csv.text

    assert price_history_csv.status_code == 200
    assert price_history_csv.headers["content-disposition"] == 'attachment; filename="01592_price_history.csv"'
    assert "price_date" in price_history_csv.text

    assert rainbow_json.status_code == 200
    assert rainbow_json.headers["content-disposition"] == 'attachment; filename="01592_rainbow.json"'
    assert rainbow_json.json()["available"] is True

    assert rainbow_csv.status_code == 200
    assert rainbow_csv.headers["content-disposition"] == 'attachment; filename="01592_rainbow.csv"'
    assert "Alpha Holdings" in rainbow_csv.text

    assert ccass_sqlite.status_code == 200
    assert ccass_sqlite.headers["content-disposition"] == 'attachment; filename="sqlite-backup.db"'
    assert ccass_sqlite.content == b"sqlite-bytes"

    assert raw_previews.status_code == 200
    assert raw_previews.json() == {
        "stock_code": "01592",
        "locale": "en",
        "metadata": {
            "code": "01592",
            "name": None,
            "issue_id": None,
            "holdings_date": None,
            "data_as_of": None,
            "fetched_at": None,
            "source_url": None,
            "source_name": None,
            "cached": False,
            "settlement_note": None,
            "attribution": None,
        },
        "warnings": [],
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


def test_mcp_download_artifact_matches_canonical_api_shapes(monkeypatch, tmp_path):
    bundle = _make_bundle()
    sqlite_path = tmp_path / "sqlite-backup.db"
    sqlite_path.write_bytes(b"sqlite-bytes")
    rainbow_payload = {
        "status": "ok",
        "stock_code": "01592",
        "available": True,
        "snapshot_count": 1,
        "earliest_snapshot_date": "2026-08-14",
        "latest_snapshot_date": "2026-08-14",
        "top_ids": ["P1"],
        "snapshots": [
            {
                "date": "2026-08-14",
                "participant_count": 1,
                "source_name": "HKEX SDW",
                "stacks": [
                    {"participant_id": "P1", "participant": "Alpha Holdings", "pct": 12.34},
                    {"participant_id": "others", "participant": "Others", "pct": 87.66},
                ],
            }
        ],
        "warnings": [],
    }

    async def fake_build_bundle(**_: object) -> SimpleNamespace:
        return bundle

    async def fake_get_rainbow_data(code: str):  # type: ignore[unused-argument]
        return rainbow_payload

    monkeypatch.setattr("app.mcp_server._build_bundle", fake_build_bundle)
    monkeypatch.setattr("app.mcp_server._bundle_markdown", lambda bundle, section, locale: f"{section}:{locale}")
    monkeypatch.setattr("app.mcp_server.get_settings", lambda: SimpleNamespace(ccass_sqlite_path=sqlite_path))
    monkeypatch.setattr("app.mcp_server.get_rainbow_data", fake_get_rainbow_data)

    result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="raw_previews",
            kind="summary_csv",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )

    assert result["section"] == "raw_previews"
    assert result["kind"] == "summary_csv"
    assert result["filename"] == "summary.csv"
    assert result["media_type"] == "text/csv"
    assert b64decode(result["content_b64"]).decode("utf-8") == "summary-csv"

    holdings_csv_result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="holdings",
            kind="csv",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )
    assert holdings_csv_result["section"] == "holdings"
    assert holdings_csv_result["kind"] == "csv"
    assert holdings_csv_result["filename"] == "01592_holdings.csv"
    assert holdings_csv_result["media_type"] == "text/csv"
    assert "Alpha Holdings" in b64decode(holdings_csv_result["content_b64"]).decode("utf-8-sig")

    price_history_csv_result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="price_history",
            kind="csv",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )
    assert price_history_csv_result["section"] == "price_history"
    assert price_history_csv_result["kind"] == "csv"
    assert price_history_csv_result["filename"] == "01592_price_history.csv"
    assert price_history_csv_result["media_type"] == "text/csv"
    assert "price_date" in b64decode(price_history_csv_result["content_b64"]).decode("utf-8-sig")

    rainbow_json_result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="rainbow",
            kind="json",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )
    assert rainbow_json_result["section"] == "rainbow"
    assert rainbow_json_result["kind"] == "json"
    assert rainbow_json_result["filename"] == "01592_rainbow.json"
    assert rainbow_json_result["media_type"] == "application/json"
    assert json.loads(b64decode(rainbow_json_result["content_b64"]).decode("utf-8"))["available"] is True

    rainbow_csv_result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="rainbow",
            kind="csv",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )
    assert rainbow_csv_result["section"] == "rainbow"
    assert rainbow_csv_result["kind"] == "csv"
    assert rainbow_csv_result["filename"] == "01592_rainbow.csv"
    assert rainbow_csv_result["media_type"] == "text/csv"
    assert "Alpha Holdings" in b64decode(rainbow_csv_result["content_b64"]).decode("utf-8-sig")

    announcements_csv_result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="announcements",
            kind="csv",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )
    assert announcements_csv_result["section"] == "announcements"
    assert announcements_csv_result["kind"] == "csv"
    assert announcements_csv_result["filename"] == "01592_announcements.csv"
    assert announcements_csv_result["media_type"] == "text/csv"
    assert "Sample HKEX announcement" in b64decode(announcements_csv_result["content_b64"]).decode("utf-8-sig")

    holdings_result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="raw_previews",
            kind="holdings_csv",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )
    assert holdings_result["section"] == "raw_previews"
    assert holdings_result["kind"] == "holdings_csv"
    assert holdings_result["filename"] == "holdings.csv"
    assert holdings_result["media_type"] == "text/csv"
    assert b64decode(holdings_result["content_b64"]).decode("utf-8") == "holdings-csv"

    sqlite_result = asyncio.run(
        mcp_server.get_download_artifact.fn(
            "01592",
            section="ccass",
            kind="sqlite",
            locale="zh_HK",
            holdings_limit=25,
            big_change_threshold=500,
        )
    )
    assert sqlite_result["section"] == "ccass"
    assert sqlite_result["kind"] == "sqlite"
    assert sqlite_result["filename"] == "sqlite-backup.db"
    assert sqlite_result["media_type"] == "application/x-sqlite3"
    assert b64decode(sqlite_result["content_b64"]) == b"sqlite-bytes"


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
        "metadata": {
            "code": "01592",
            "name": None,
            "issue_id": None,
            "holdings_date": None,
            "data_as_of": None,
            "fetched_at": None,
            "source_url": None,
            "source_name": None,
            "cached": False,
            "settlement_note": None,
            "attribution": None,
        },
        "warnings": [],
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
