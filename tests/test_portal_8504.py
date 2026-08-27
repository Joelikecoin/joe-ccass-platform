from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime, date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from ccass_core.compute import AnalysisResult
from app.config import Settings
from app.friend_clone_app import PortalBundle
from app.friend_clone_app import _big_changes_block
from app.friend_clone_app import _changes_block
from app.models import (
    AnnouncementRow,
    AnnouncementsMetadata,
    AnnouncementsResponse,
    CapitalInformationMetadata,
    CapitalInformationResponse,
    CapitalInformationRow,
    OfficerRow,
    OfficersMetadata,
    OfficersResponse,
    PriceHistoryMetadata,
    PriceHistoryResponse,
    PriceHistoryRow,
    StockEventRow,
    StockEventsMetadata,
    StockEventsResponse,
)
from app.streamlit_ui import PreparedReport
from app.streamlit_ui import build_download_artifacts
from app.portal_8504 import (
    PRICE_HISTORY_LOAD_TIMEOUT_SECONDS,
    app as portal_app,
    Portal8504Bundle,
    _build_portal_8504_bundle,
    _overview_block,
    _price_panel,
    _render_page,
)


def test_portal_8504_bundle_times_out_price_history_without_blocking(monkeypatch):
    async def fake_build_bundle(**kwargs):
        live_product = SimpleNamespace(
            symbol="01592.HK",
            price_history=[],
            source_notes=[],
        )
        return PortalBundle(
            requested_code="01592",
            resolved_code="01592",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
            live_product=live_product,
            prepared=None,
            live_markdown_en="",
            live_markdown_zh="",
            ccass_markdown_en="",
            ccass_markdown_zh="",
            live_artifacts=None,
            ccass_artifacts=None,
            previous_available=False,
        )

    def fake_concentration_history_rows(bundle):
        return []

    def slow_cached_price_history(symbol):
        time.sleep(0.05)
        return ({"date": "2026-08-14", "close": 1.23},)

    monkeypatch.setattr("app.portal_8504._build_bundle", fake_build_bundle)
    monkeypatch.setattr("app.portal_8504._concentration_history_rows", fake_concentration_history_rows)
    monkeypatch.setattr("app.portal_8504._cached_price_history", slow_cached_price_history)
    monkeypatch.setattr("app.portal_8504.PRICE_HISTORY_LOAD_TIMEOUT_SECONDS", 0.01)

    started = time.time()
    bundle = asyncio.run(
        _build_portal_8504_bundle(
            raw_code="01592",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
        )
    )
    elapsed = time.time() - started

    assert isinstance(bundle, Portal8504Bundle)
    assert elapsed < 0.5
    assert bundle.price_rows == []
    assert any("timed out" in note.lower() for note in bundle.base.live_product.source_notes)


def test_portal_8504_bundle_prefers_live_product_price_rows(monkeypatch):
    live_price_rows = [
        {
            "date": "2026-08-14",
            "open": 1.0,
            "high": 1.1,
            "low": 0.9,
            "close": 1.05,
            "vwap": 1.05,
            "volume": 1000,
            "turnover": 1050.0,
            "source": "Yahoo Finance",
            "source_url": "https://query1.finance.yahoo.com/v8/finance/chart/01592.HK",
        }
    ]

    async def fake_build_bundle(**kwargs):
        live_product = SimpleNamespace(
            symbol="01592.HK",
            price_history=live_price_rows,
            source_notes=[],
        )
        return PortalBundle(
            requested_code="01592",
            resolved_code="01592",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
            live_product=live_product,
            prepared=None,
            live_markdown_en="",
            live_markdown_zh="",
            ccass_markdown_en="",
            ccass_markdown_zh="",
            live_artifacts=None,
            ccass_artifacts=None,
            previous_available=False,
        )

    def fail_cached_price_history(symbol):
        raise AssertionError("cached price history should not be called when live product already has rows")

    monkeypatch.setattr("app.portal_8504._build_bundle", fake_build_bundle)
    monkeypatch.setattr("app.portal_8504._cached_price_history", fail_cached_price_history)
    monkeypatch.setattr("app.portal_8504._concentration_history_rows", lambda bundle: [])

    bundle = asyncio.run(
        _build_portal_8504_bundle(
            raw_code="01592",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
        )
    )

    assert isinstance(bundle, Portal8504Bundle)
    assert bundle.price_rows[0]["source"] == "Yahoo Finance"
    assert bundle.price_rows[0]["vwap"] == 1.05


def test_portal_8504_bundle_does_not_eagerly_generate_ccass_markdown(monkeypatch):
    async def fake_build_bundle(**kwargs):
        live_product = SimpleNamespace(
            symbol="01592.HK",
            price_history=[],
            source_notes=[],
        )
        prepared = SimpleNamespace(
            response=SimpleNamespace(
                metadata=SimpleNamespace(code="01592", data_as_of=date(2026, 8, 14)),
                data_quality_warnings=[],
            ),
            source_trace=None,
        )
        return PortalBundle(
            requested_code="01592",
            resolved_code="01592",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
            live_product=live_product,
            prepared=prepared,
            live_markdown_en="",
            live_markdown_zh="",
            ccass_markdown_en="",
            ccass_markdown_zh="",
            live_artifacts=None,
            ccass_artifacts=None,
            previous_available=False,
        )

    def fail_render_prepared_report(*args, **kwargs):
        raise AssertionError("CCASS markdown should be generated lazily")

    monkeypatch.setattr("app.portal_8504._build_bundle", fake_build_bundle)
    monkeypatch.setattr("app.friend_clone_app.render_prepared_report", fail_render_prepared_report)
    monkeypatch.setattr("app.portal_8504._concentration_history_rows", lambda bundle: [])
    monkeypatch.setattr("app.portal_8504._cached_price_history", lambda symbol: ())

    bundle = asyncio.run(
        _build_portal_8504_bundle(
            raw_code="01592",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
        )
    )

    assert isinstance(bundle, Portal8504Bundle)
    assert bundle.base.ccass_markdown_en == ""


def test_portal_8504_bundle_defers_zh_markdown_generation(monkeypatch):
    calls = {"live": [], "ccass": []}

    fake_response = SimpleNamespace(metadata=SimpleNamespace(code="01592"))
    fake_prepared = SimpleNamespace(
        response=fake_response,
        source_trace=[],
        analysis=SimpleNamespace(changes=[], big_changes=[], concentration={}, previous_available=False),
        fetch_error=None,
        filename="01592.md",
    )
    fake_live_product = SimpleNamespace(
        code="01592",
        symbol="01592.HK",
        response=fake_response,
        company={},
        latest_price={},
        price_history=[],
        announcements=[],
        corporate_events=[],
        share_capital_changes=[],
        officers=[],
        source_notes=[],
    )
    fake_live_artifacts = SimpleNamespace(
        combined_csv_bytes=b"",
        combined_csv_filename="01592_live.csv",
        workbook_bytes=b"",
        workbook_filename="01592_live.xlsx",
        json_bytes=b"{}",
        json_filename="01592_live.json",
    )
    fake_ccass_artifacts = SimpleNamespace(
        combined_csv_bytes=b"",
        combined_csv_filename="01592_ccass.csv",
        workbook_bytes=b"",
        workbook_filename="01592_ccass.xlsx",
    )

    async def fake_prepare_report(*args, **kwargs):
        return fake_prepared

    async def fake_build_live_product_from_surfaces(response, *, code, source_trace):
        return fake_live_product

    def fake_render_live_markdown(live_product, *, locale="en"):
        calls["live"].append(locale)
        return "ZH LIVE" if locale == "zh_HK" else "EN LIVE"

    def fake_render_prepared_report(prepared, *, locale="en"):
        calls["ccass"].append(locale)
        return ("ZH CCASS" if locale == "zh_HK" else "EN CCASS", {})

    def fake_build_live_download_artifacts(live_product):
        return fake_live_artifacts

    def fake_build_download_artifacts(response):
        return fake_ccass_artifacts

    monkeypatch.setattr("app.friend_clone_app.prepare_report", fake_prepare_report)
    monkeypatch.setattr("app.friend_clone_app.build_live_product_from_response_with_surfaces", fake_build_live_product_from_surfaces)
    monkeypatch.setattr("app.friend_clone_app.render_live_markdown", fake_render_live_markdown)
    monkeypatch.setattr("app.friend_clone_app.render_prepared_report", fake_render_prepared_report)
    monkeypatch.setattr("app.friend_clone_app.build_live_download_artifacts", fake_build_live_download_artifacts)
    monkeypatch.setattr("app.friend_clone_app.build_download_artifacts", fake_build_download_artifacts)
    monkeypatch.setattr("app.friend_clone_app._resolve_requested_code", lambda raw_code, input_type: "01592")

    bundle = asyncio.run(
        _build_portal_8504_bundle(
            raw_code="01592",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=False,
        )
    )

    assert isinstance(bundle, Portal8504Bundle)
    assert bundle.base.live_markdown_zh == ""
    assert bundle.base.ccass_markdown_zh == ""
    assert calls["live"] == ["en"]
    assert calls["ccass"] == []


def test_portal_8504_download_route_lazy_generates_zh_markdown(monkeypatch, tmp_path):
    calls = {"live": [], "ccass": []}

    def fake_model_dump_json(indent=2):
        return json.dumps({"metadata": {"code": "01592"}}, indent=indent)

    fake_response = SimpleNamespace(
        metadata=SimpleNamespace(
            code="01592",
            issue_id=1592,
            name="01592 Corp",
            holdings_date=date(2026, 8, 14),
            fetched_at=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
            source_name="HKEX SDW",
            source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
            cached=True,
            data_as_of=date(2026, 8, 14),
        ),
        data_quality_warnings=[],
        holdings=[],
        holdings_date=date(2026, 8, 14),
        holdings_summary=SimpleNamespace(
            participant_count=0,
            total_in_ccass_shares=0,
            issued_shares=0,
            top5_pct_of_issued=0.0,
            top10_pct_of_issued=0.0,
            top5_pct_of_ccass=0.0,
            top10_pct_of_ccass=0.0,
        ),
        model_dump_json=fake_model_dump_json,
    )
    fake_prepared = SimpleNamespace(
        response=fake_response,
        source_trace=[],
        analysis=SimpleNamespace(changes=[], big_changes=[], concentration={}, previous_available=False),
        fetch_error=None,
        filename="01592.md",
    )
    fake_live_product = SimpleNamespace(
        code="01592",
        symbol="01592.HK",
        response=fake_response,
        company={},
        latest_price={},
        price_history=[],
        announcements=[],
        corporate_events=[],
        share_capital_changes=[],
        officers=[],
        source_notes=[],
    )
    fake_base = PortalBundle(
        requested_code="01592",
        resolved_code="01592",
        input_type="Stock Code",
        source_mode="auto",
        top_n=20,
        big_change_threshold=1_000_000,
        use_local_history=True,
        live_product=fake_live_product,
        prepared=fake_prepared,
        live_markdown_en="EN LIVE",
        live_markdown_zh="",
        ccass_markdown_en="EN CCASS",
        ccass_markdown_zh="",
        live_artifacts=SimpleNamespace(
            combined_csv_bytes=b"",
            combined_csv_filename="01592_live.csv",
            workbook_bytes=b"",
            workbook_filename="01592_live.xlsx",
            json_bytes=b"{}",
            json_filename="01592_live.json",
        ),
        ccass_artifacts=SimpleNamespace(
            combined_csv_bytes=b"",
            combined_csv_filename="01592_ccass.csv",
            workbook_bytes=b"",
            workbook_filename="01592_ccass.xlsx",
            raw_preview_summary_bytes=b"summary-csv",
            raw_preview_summary_filename="summary.csv",
            raw_preview_holdings_bytes=b"holdings-csv",
            raw_preview_holdings_filename="holdings.csv",
            raw_preview_json_bytes=b'{"tables": []}',
            raw_preview_json_filename="01592_raw_tables.json",
        ),
        previous_available=False,
    )
    fake_bundle = Portal8504Bundle(base=fake_base, price_rows=[], concentration_rows=[])

    async def fake_build_portal_8504_bundle(**kwargs):
        return fake_bundle

    def fake_render_live_markdown(live_product, *, locale="en"):
        calls["live"].append(locale)
        return "ZH LIVE" if locale == "zh_HK" else "EN LIVE"

    def fake_render_prepared_report(prepared, *, locale="en"):
        calls["ccass"].append(locale)
        return ("ZH CCASS" if locale == "zh_HK" else "EN CCASS", {})

    monkeypatch.setattr("app.portal_8504._build_portal_8504_bundle", fake_build_portal_8504_bundle)
    monkeypatch.setattr("app.friend_clone_app.render_live_markdown", fake_render_live_markdown)
    monkeypatch.setattr("app.friend_clone_app.render_prepared_report", fake_render_prepared_report)
    sqlite_path = tmp_path / "sqlite-backup.db"
    sqlite_path.write_bytes(b"sqlite-bytes")
    monkeypatch.setattr("app.friend_clone_app.get_settings", lambda: Settings(ccass_sqlite_path=sqlite_path))

    client = TestClient(portal_app)
    live_response = client.get(
        "/download/live/md",
        params={"code": "01592", "locale": "zh_HK"},
    )
    ccass_response = client.get(
        "/download/ccass/md",
        params={"code": "01592", "locale": "zh_HK"},
    )
    raw_tables_response = client.get(
        "/download/raw_previews/json",
        params={"code": "01592", "locale": "zh_HK"},
    )

    assert live_response.status_code == 200
    assert live_response.text == "ZH LIVE"
    assert ccass_response.status_code == 200
    assert ccass_response.text == "ZH CCASS"
    assert raw_tables_response.status_code == 200
    assert raw_tables_response.json() == {"tables": []}
    assert "Download SQLite Backup" in client.get("/", params={"code": "01592"}).text
    assert "Download Raw Preview Summary CSV" in client.get("/", params={"code": "01592"}).text
    assert "Download Raw Preview Holdings CSV" in client.get("/", params={"code": "01592"}).text
    assert calls["live"] == ["zh_HK"]
    assert calls["ccass"] == ["zh_HK"]


def test_portal_8504_renders_ccass_json_download_button(monkeypatch):
    fake_response = SimpleNamespace(
        metadata=SimpleNamespace(
            code="01592",
            issue_id=1592,
            name="01592 Corp",
            holdings_date=date(2026, 8, 14),
            fetched_at=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
            source_name="HKEX SDW",
            source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
            cached=True,
            data_as_of=date(2026, 8, 14),
        ),
        data_quality_warnings=[],
        holdings=[],
        holdings_summary=SimpleNamespace(
            participant_count=0,
            total_in_ccass_shares=0,
            issued_shares=0,
            top5_pct_of_issued=0.0,
            top10_pct_of_issued=0.0,
            top5_pct_of_ccass=0.0,
            top10_pct_of_ccass=0.0,
        ),
        announcements=[],
        stock_events=[],
        capital_information=[],
        officers=[],
        price_history=SimpleNamespace(metadata=SimpleNamespace(source_name="HKEX SDW", source_url="")),
        model_dump_json=lambda indent=2: json.dumps({"metadata": {"code": "01592"}}, indent=indent),
    )
    fake_prepared = SimpleNamespace(
        response=fake_response,
        source_trace=[],
        analysis=SimpleNamespace(changes=[], big_changes=[], concentration={}, previous_available=False),
        fetch_error=None,
        filename="01592.md",
    )
    fake_base = PortalBundle(
        requested_code="01592",
        resolved_code="01592",
        input_type="Stock Code",
        source_mode="auto",
        top_n=20,
        big_change_threshold=1_000_000,
        use_local_history=True,
        live_product=None,
        prepared=fake_prepared,
        live_markdown_en="",
        live_markdown_zh="",
        ccass_markdown_en="",
        ccass_markdown_zh="",
        live_artifacts=None,
        ccass_artifacts=SimpleNamespace(
            combined_csv_bytes=b"",
            combined_csv_filename="01592_ccass.csv",
            workbook_bytes=b"",
            workbook_filename="01592_ccass.xlsx",
        ),
        previous_available=False,
    )
    fake_bundle = Portal8504Bundle(base=fake_base, price_rows=[], concentration_rows=[])

    async def fake_build_portal_8504_bundle(**kwargs):
        return fake_bundle

    monkeypatch.setattr("app.portal_8504._build_portal_8504_bundle", fake_build_portal_8504_bundle)

    client = TestClient(portal_app)
    response = client.get("/", params={"code": "01592"})

    assert response.status_code == 200
    assert "Download CCASS JSON" in response.text
    assert "/download/ccass/json" in response.text
    assert "Download Raw Tables JSON" in response.text
    assert "/download/raw_previews/json" in response.text
    assert "Download This Stock" in response.text
    assert "Download SQLite Backup" in response.text
    assert "/download/ccass/sqlite" in response.text
    assert "Download All Data CSV" in response.text
    assert "/download/ccass/csv" in response.text
    assert "Download Excel" in response.text
    assert "/download/ccass/xlsx" in response.text
    assert "Download Markdown Report" in response.text
    assert "/download/ccass/md" in response.text
    assert "Download Holdings CSV" in response.text
    assert "/download/holdings/csv" in response.text
    assert "Download Changes CSV" in response.text
    assert "/download/changes/csv" in response.text
    assert "Download Big Changes CSV" in response.text
    assert "/download/big_changes/csv" in response.text
    assert "Download Concentration CSV" in response.text
    assert "/download/concentration/csv" in response.text
    assert "Download Announcements CSV" in response.text
    assert "/download/announcements/csv" in response.text
    assert "Download Price CSV" in response.text
    assert "/download/price_history/csv" in response.text
    assert "Download Rainbow CSV" in response.text
    assert "/download/rainbow/csv" in response.text
    assert "Download Rainbow JSON" in response.text
    assert "/download/rainbow/json" in response.text
    assert "Download Raw Preview Summary CSV" in response.text
    assert "/download/raw_previews/summary_csv" in response.text
    assert "Download Raw Preview Holdings CSV" in response.text
    assert "/download/raw_previews/holdings_csv" in response.text
    assert "Source diagnostics" in response.text


def test_portal_8504_does_not_render_dt_rainbow_section(monkeypatch):
    fake_response = SimpleNamespace(
        metadata=SimpleNamespace(
            code="01592",
            issue_id=1592,
            name="01592 Corp",
            holdings_date=date(2026, 8, 14),
            fetched_at=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
            source_name="HKEX SDW",
            source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
            cached=True,
            data_as_of=date(2026, 8, 14),
        ),
        data_quality_warnings=[],
        holdings=[],
        holdings_summary=SimpleNamespace(
            participant_count=0,
            total_in_ccass_shares=0,
            issued_shares=0,
            top5_pct_of_issued=0.0,
            top10_pct_of_issued=0.0,
            top5_pct_of_ccass=0.0,
            top10_pct_of_ccass=0.0,
        ),
        announcements=[],
        stock_events=[],
        capital_information=[],
        officers=[],
        price_history=SimpleNamespace(metadata=SimpleNamespace(source_name="HKEX SDW", source_url="")),
        model_dump_json=lambda indent=2: json.dumps({"metadata": {"code": "01592"}}, indent=indent),
    )
    fake_prepared = SimpleNamespace(
        response=fake_response,
        source_trace=[],
        analysis=SimpleNamespace(changes=[], big_changes=[], concentration={}, previous_available=False),
        fetch_error=None,
        filename="01592.md",
    )
    fake_base = PortalBundle(
        requested_code="01592",
        resolved_code="01592",
        input_type="Stock Code",
        source_mode="auto",
        top_n=20,
        big_change_threshold=1_000_000,
        use_local_history=True,
        live_product=None,
        prepared=fake_prepared,
        live_markdown_en="",
        live_markdown_zh="",
        ccass_markdown_en="",
        ccass_markdown_zh="",
        live_artifacts=None,
        ccass_artifacts=SimpleNamespace(
            combined_csv_bytes=b"",
            combined_csv_filename="01592_ccass.csv",
            workbook_bytes=b"",
            workbook_filename="01592_ccass.xlsx",
        ),
        previous_available=False,
    )
    fake_bundle = Portal8504Bundle(base=fake_base, price_rows=[], concentration_rows=[])

    async def fake_build_portal_8504_bundle(**kwargs):
        return fake_bundle

    monkeypatch.setattr("app.portal_8504._build_portal_8504_bundle", fake_build_portal_8504_bundle)

    client = TestClient(portal_app)
    response = client.get("/", params={"code": "01592"})

    assert response.status_code == 200
    assert 'id="dt-rainbow"' not in response.text
    assert "DT Rainbow" not in response.text


def test_portal_8504_download_route_allows_ccass_markdown_without_artifacts(monkeypatch):
    calls = {"ccass": []}
    fake_response = SimpleNamespace(metadata=SimpleNamespace(code="00700"))
    fake_prepared = SimpleNamespace(
        response=fake_response,
        source_trace=[],
        analysis=SimpleNamespace(changes=[], big_changes=[], concentration={}, previous_available=False),
        fetch_error=None,
        filename="00700.md",
    )
    fake_base = PortalBundle(
        requested_code="00700",
        resolved_code="00700",
        input_type="Stock Code",
        source_mode="auto",
        top_n=20,
        big_change_threshold=1_000_000,
        use_local_history=True,
        live_product=None,
        prepared=fake_prepared,
        live_markdown_en="",
        live_markdown_zh="",
        ccass_markdown_en="",
        ccass_markdown_zh="",
        live_artifacts=None,
        ccass_artifacts=None,
        previous_available=False,
    )
    fake_bundle = Portal8504Bundle(base=fake_base, price_rows=[], concentration_rows=[])

    async def fake_build_portal_8504_bundle(**kwargs):
        return fake_bundle

    def fake_render_prepared_report(prepared, *, locale="en"):
        calls["ccass"].append(locale)
        return ("CCASS MARKDOWN" if locale == "en" else "ZH CCASS MARKDOWN", {})

    monkeypatch.setattr("app.portal_8504._build_portal_8504_bundle", fake_build_portal_8504_bundle)
    monkeypatch.setattr("app.friend_clone_app.render_prepared_report", fake_render_prepared_report)

    client = TestClient(portal_app)
    response = client.get(
        "/download/ccass/md",
        params={"code": "00700", "locale": "en"},
    )

    assert response.status_code == 200
    assert response.text == "CCASS MARKDOWN"
    assert calls["ccass"] == ["en"]


def test_portal_8504_download_route_supports_section_specific_artifacts(monkeypatch, current_response):
    download_artifacts = build_download_artifacts(current_response)
    fake_response = SimpleNamespace(metadata=current_response.metadata, model_dump_json=current_response.model_dump_json)
    fake_prepared = SimpleNamespace(
        response=current_response,
        source_trace=[],
        analysis=SimpleNamespace(changes=[], big_changes=[], concentration={}, previous_available=False),
        fetch_error=None,
        filename="01592.md",
    )
    fake_base = PortalBundle(
        requested_code="01592",
        resolved_code="01592",
        input_type="Stock Code",
        source_mode="auto",
        top_n=20,
        big_change_threshold=1_000_000,
        use_local_history=True,
        live_product=SimpleNamespace(response=fake_response, source_notes=[], price_history=[]),
        prepared=fake_prepared,
        live_markdown_en="",
        live_markdown_zh="",
        ccass_markdown_en="",
        ccass_markdown_zh="",
        live_artifacts=None,
        ccass_artifacts=download_artifacts,
        previous_available=True,
    )
    fake_bundle = Portal8504Bundle(base=fake_base, price_rows=[], concentration_rows=[])

    async def fake_build_portal_8504_bundle(**kwargs):
        return fake_bundle

    monkeypatch.setattr("app.portal_8504._build_portal_8504_bundle", fake_build_portal_8504_bundle)
    monkeypatch.setattr(
        "app.portal_8504._rainbow_download_payload",
        lambda code: {
            "status": "ok",
            "stock_code": code,
            "available": True,
            "snapshot_count": 1,
            "earliest_snapshot_date": "2026-08-14",
            "latest_snapshot_date": "2026-08-14",
            "top_ids": ["B00001"],
            "snapshots": [
                {
                    "date": "2026-08-14",
                    "stacks": [
                        {"participant_id": "B00001", "participant": "TEST FIXTURE BROKER ONE", "pct": 60.08},
                        {"participant_id": "others", "participant": "Others", "pct": 39.92},
                    ],
                    "participant_count": 3,
                    "source_name": "HKEX SDW",
                }
            ],
            "warnings": [],
        },
    )

    client = TestClient(portal_app)

    holdings_csv = client.get("/download/holdings/csv", params={"code": "01592", "locale": "en"})
    changes_csv = client.get("/download/changes/csv", params={"code": "01592", "locale": "en"})
    big_changes_csv = client.get("/download/big_changes/csv", params={"code": "01592", "locale": "en"})
    concentration_csv = client.get("/download/concentration/csv", params={"code": "01592", "locale": "en"})
    announcements_csv = client.get("/download/announcements/csv", params={"code": "01592", "locale": "en"})
    price_history_csv = client.get("/download/price_history/csv", params={"code": "01592", "locale": "en"})
    raw_summary_csv = client.get("/download/raw_previews/summary_csv", params={"code": "01592", "locale": "en"})
    raw_holdings_csv = client.get("/download/raw_previews/holdings_csv", params={"code": "01592", "locale": "en"})
    rainbow_json = client.get("/download/rainbow/json", params={"code": "01592", "locale": "en"})
    rainbow_csv = client.get("/download/rainbow/csv", params={"code": "01592", "locale": "en"})

    assert holdings_csv.status_code == 200
    assert "TEST FIXTURE BROKER ONE" in holdings_csv.text
    assert changes_csv.status_code == 200
    assert "participant_id" in changes_csv.text.lower()
    assert big_changes_csv.status_code == 200
    assert "participant_id" in big_changes_csv.text.lower()
    assert concentration_csv.status_code == 200
    assert "participant_id" in concentration_csv.text.lower()
    assert announcements_csv.status_code == 200
    assert "announcement" in announcements_csv.text.lower()
    assert price_history_csv.status_code == 200
    assert "date" in price_history_csv.text.lower()
    assert raw_summary_csv.status_code == 200
    assert "stock name" in raw_summary_csv.text.lower()
    assert raw_holdings_csv.status_code == 200
    assert "participant" in raw_holdings_csv.text.lower()
    assert rainbow_json.status_code == 200
    assert rainbow_json.json()["available"] is True
    assert rainbow_csv.status_code == 200
    assert "TEST FIXTURE BROKER ONE" in rainbow_csv.text


def test_portal_8504_download_route_returns_not_found_for_missing_live_artifacts(monkeypatch):
    fake_bundle = PortalBundle(
        requested_code="00700",
        resolved_code="00700",
        input_type="Stock Code",
        source_mode="auto",
        top_n=20,
        big_change_threshold=1_000_000,
        use_local_history=True,
        live_product=None,
        prepared=None,
        live_markdown_en="",
        live_markdown_zh="",
        ccass_markdown_en="",
        ccass_markdown_zh="",
        live_artifacts=None,
        ccass_artifacts=None,
        previous_available=False,
    )
    fake_portal_bundle = Portal8504Bundle(base=fake_bundle, price_rows=[], concentration_rows=[])

    async def fake_build_portal_8504_bundle(**kwargs):
        return fake_portal_bundle

    monkeypatch.setattr("app.portal_8504._build_portal_8504_bundle", fake_build_portal_8504_bundle)

    client = TestClient(portal_app)
    response = client.get(
        "/download/live/md",
        params={"code": "00700", "locale": "en"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"
    assert "Live product artifacts are unavailable." in response.json()["message"]


def test_portal_8504_render_uses_price_history_response_metadata(monkeypatch):
    fake_price_history_response = SimpleNamespace(
        metadata=SimpleNamespace(
            source_name="Yahoo Finance",
            source_url="https://query1.finance.yahoo.com/v8/finance/chart/01592.HK",
        )
    )
    fake_response = SimpleNamespace(
        metadata=SimpleNamespace(
            code="01592",
            issue_id=1592,
            name="01592 Corp",
            holdings_date=date(2026, 8, 14),
            fetched_at=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
            source_name="HKEX SDW",
            source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
            cached=True,
            data_as_of=date(2026, 8, 14),
        ),
        holdings_summary=SimpleNamespace(
            participant_count=116,
            top5_pct_of_issued=60.0772,
            top10_pct_of_issued=70.6893,
            top5_pct_of_ccass=72.5,
            top10_pct_of_ccass=81.2,
        ),
        holdings=[],
        announcements=[],
        stock_events=[],
        capital_information=[],
        officers=[],
        data_quality_warnings=["Stale LKG fallback used."],
        price_history=fake_price_history_response,
    )
    fake_live_product = SimpleNamespace(
        code="01592",
        symbol="01592.HK",
        company={
            "company_name": "01592 Corp",
            "short_name": "01592",
            "exchange": "HKEX",
            "currency": "HKD",
            "fetched_at": "2026-08-14 09:00:00+00:00",
            "data_as_of": "2026-08-14",
            "source_name": "HKEX SDW",
            "source_url": "https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
            "issue_id": 1592,
        },
        latest_price={"price_display": "1.05", "change_display": "+0.01 (+0.96%)", "market_state": "Yahoo Finance", "market_time": "2026-08-14"},
        price_history=[
            {
                "date": "2026-08-14",
                "open": 1.0,
                "high": 1.1,
                "low": 0.9,
                "close": 1.05,
                "vwap": 1.02,
                "adjusted_close": 1.05,
                "volume": 1000,
                "turnover": 1050.0,
                "price_source": "Yahoo Finance",
                "turnover_est": False,
                "vwap_est": False,
                "source": "Yahoo Finance",
                "source_url": "https://query1.finance.yahoo.com/v8/finance/chart/01592.HK",
            }
        ],
        announcements=[],
        corporate_events=[],
        share_capital_changes=[],
        officers=[],
        source_notes=["Persisted snapshot recovered."],
        diagnostics=[],
        fetched_at=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
        response=fake_response,
        source_trace=None,
    )
    fake_base = PortalBundle(
        requested_code="01592",
        resolved_code="01592",
        input_type="Stock Code",
        source_mode="auto",
        top_n=20,
        big_change_threshold=1_000_000,
        use_local_history=True,
        live_product=fake_live_product,
        prepared=SimpleNamespace(
            response=fake_response,
            source_trace=[],
            analysis=SimpleNamespace(changes=[], big_changes=[], concentration={}, previous_available=True),
            fetch_error=None,
            filename="01592_ccass_report.md",
        ),
        live_markdown_en="",
        live_markdown_zh="",
        ccass_markdown_en="",
        ccass_markdown_zh="",
        live_artifacts=None,
        ccass_artifacts=None,
        previous_available=True,
    )
    fake_bundle = Portal8504Bundle(
        base=fake_base,
        price_rows=fake_live_product.price_history,
        concentration_rows=[],
    )

    overview_html = _overview_block(fake_bundle.base, fake_bundle.price_rows, fake_bundle.concentration_rows)
    price_html = _price_panel(fake_bundle.base, fake_bundle.price_rows)

    assert "list.metadata" not in overview_html
    assert "list.metadata" not in price_html
    assert "Yahoo Finance" in overview_html
    assert "Yahoo Finance" in price_html
    assert "Stale LKG fallback used." in overview_html


def test_portal_8504_bundle_recovers_auxiliary_surfaces_without_ccass(monkeypatch):
    async def fake_prepare_report(*args, **kwargs):
            return PreparedReport(
                code="03321",
                markdown="",
                chatgpt_payload="",
                filename="03321_report.md",
                response=None,
                previous_response=None,
                source_trace=None,
                analysis=None,
                announcements=None,
                stock_events=None,
                capital_information=None,
                officers=None,
                price_history=None,
                workflow=None,
                research_context_entry=None,
                fetch_error=None,
            )

    class _FakeClient:
        async def resolve_issue_id(self, code):
            return 27882, "Test Co"

    class _PriceService:
        async def get_price_history(self, code):
            return PriceHistoryResponse(
                metadata=PriceHistoryMetadata(
                    code="03321",
                    name="Test Co",
                    ticker="03321.HK",
                    price_date_from=date(2026, 8, 14),
                    price_date_to=date(2026, 8, 14),
                    source_name="Yahoo Finance",
                    source_url="https://query1.finance.yahoo.com/v8/finance/chart/03321.HK",
                    fetched_at=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
                    currency="HKD",
                ),
                prices=[
                    PriceHistoryRow(
                        price_date=date(2026, 8, 14),
                        open=1.0,
                        high=1.1,
                        low=0.9,
                        close=1.05,
                        vwap=1.02,
                        adjusted_close=1.05,
                        volume=1000,
                        turnover=1050.0,
                        price_source="Yahoo Finance",
                    )
                ],
            )

    class _AnnouncementsService:
        async def get_announcements(self, code, start_date=None, end_date=None):
            return AnnouncementsResponse(
                metadata=AnnouncementsMetadata(
                    code="03321",
                    name="Test Co",
                    source_name="HKEXnews",
                    source_url="https://www1.hkexnews.hk",
                    fetched_at=datetime(2026, 8, 14, 9, 5, tzinfo=UTC),
                    earliest_announcement_date=date(2026, 8, 1),
                    latest_announcement_date=date(2026, 8, 14),
                    announcement_count=1,
                ),
                announcements=[
                    AnnouncementRow(
                        announcement_date=date(2026, 8, 14),
                        title="Sample announcement",
                        source="HKEXnews",
                        link="https://www1.hkexnews.hk/listedco/listconews/sehk/20260814/03321_20260814.pdf",
                    )
                ],
            )

    class _StockEventsService:
        async def get_stock_events(self, code):
            return StockEventsResponse(
                metadata=StockEventsMetadata(
                    code="03321",
                    name="Test Co",
                    source_name="Webb-site Events",
                    source_url="https://webbsite.0xmd.com/dbpub/events.asp",
                    fetched_at=datetime(2026, 8, 14, 9, 10, tzinfo=UTC),
                    data_as_of=date(2026, 8, 13),
                    stock_events_count=1,
                    source_status="ready",
                ),
                stock_events=[
                    StockEventRow(
                        event_date=date(2026, 8, 13),
                        title="Dividend",
                        event_type="dividend",
                        source="Webb-site Events",
                        link="https://webbsite.0xmd.com/dbpub/events.asp?i=27882",
                        details="Cash dividend",
                    )
                ],
            )

    class _CapitalService:
        async def get_capital_information(self, code):
            return CapitalInformationResponse(
                metadata=CapitalInformationMetadata(
                    code="03321",
                    name="Test Co",
                    source_name="10jqka F10",
                    source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK03321/",
                    fetched_at=datetime(2026, 8, 14, 9, 15, tzinfo=UTC),
                    data_as_of=date(2026, 8, 14),
                    capital_information_count=1,
                    source_status="ready",
                ),
                capital_information=[
                    CapitalInformationRow(
                        label="Issued shares",
                        value="1,000,000,000",
                        unit="shares",
                        as_of=date(2026, 8, 14),
                        source="10jqka F10",
                        note="Sample capital row",
                        link="https://stockpage.10jqka.com.cn/basicweb/176/HK03321/",
                    )
                ],
            )

    class _OfficersService:
        async def get_officers(self, code):
            return OfficersResponse(
                metadata=OfficersMetadata(
                    code="03321",
                    name="Test Co",
                    source_name="同花順 F10 managers",
                    source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK03321/manager.html",
                    fetched_at=datetime(2026, 8, 14, 9, 20, tzinfo=UTC),
                    data_as_of=date(2026, 8, 14),
                    officers_count=1,
                    source_status="ready",
                ),
                officers=[
                    OfficerRow(
                        name="Sample Officer",
                        positions=["Director"],
                        tenure_from=date(2020, 1, 1),
                        tenure_to=None,
                        is_current=True,
                        age=45,
                        salary="—",
                    )
                ],
            )

    monkeypatch.setattr("app.friend_clone_app.prepare_report", fake_prepare_report)
    monkeypatch.setattr("app.live_product.WebbsiteClient", lambda: _FakeClient())
    monkeypatch.setattr("app.live_product.get_price_history_service", lambda: _PriceService())
    monkeypatch.setattr("app.live_product.get_announcements_service", lambda: _AnnouncementsService())
    monkeypatch.setattr("app.live_product.get_stock_events_service", lambda: _StockEventsService())
    monkeypatch.setattr("app.live_product.get_capital_information_service", lambda: _CapitalService())
    monkeypatch.setattr("app.live_product.get_officers_service", lambda: _OfficersService())
    monkeypatch.setattr("app.portal_8504._concentration_history_rows", lambda bundle: [])

    bundle = asyncio.run(
        _build_portal_8504_bundle(
            raw_code="03321",
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
        )
    )

    assert isinstance(bundle, Portal8504Bundle)
    assert bundle.base.live_product is not None
    assert bundle.base.live_product.price_history
    assert bundle.base.live_product.announcements
    assert bundle.base.live_product.corporate_events
    assert bundle.base.live_product.share_capital_changes
    assert bundle.base.live_product.officers
    assert bundle.price_rows

    html = _render_page(bundle)
    assert "HKEX Announcements" in html
    assert "Corporate Events" in html
    assert "Share Capital Changes" in html
    assert "Officers / Managers" in html


def test_portal_8504_big_changes_block_uses_response_big_changes():
    fake_response = SimpleNamespace(
        big_changes=SimpleNamespace(
            big_changes=[
                SimpleNamespace(
                    participant_id="B01922",
                    participant="TEST FIXTURE BROKER ONE",
                    shares_before=0,
                    shares_after=554387582,
                    shares_change=554387582,
                    status="new",
                )
            ]
        )
    )
    bundle = SimpleNamespace(
        top_n=20,
        prepared=SimpleNamespace(
            response=fake_response,
            analysis=AnalysisResult(big_changes=[]),
        ),
    )

    html = _big_changes_block(bundle)

    assert "No big changes at the current threshold." not in html
    assert "B01922" in html
    assert "TEST FIXTURE BROKER ONE" in html
    assert "554,387,582" in html


def test_portal_8504_changes_block_big_changes_metric_uses_response_big_changes():
    fake_response = SimpleNamespace(
        big_changes=SimpleNamespace(
            big_changes=[
                SimpleNamespace(
                    participant_id="B01922",
                    participant="TEST FIXTURE BROKER ONE",
                    shares_before=0,
                    shares_after=554387582,
                    shares_change=554387582,
                    status="new",
                ),
                SimpleNamespace(
                    participant_id="B01565",
                    participant="TEST FIXTURE BROKER TWO",
                    shares_before=0,
                    shares_after=114366170,
                    shares_change=114366170,
                    status="new",
                ),
                SimpleNamespace(
                    participant_id="B01955",
                    participant="TEST FIXTURE BROKER THREE",
                    shares_before=0,
                    shares_after=79561930,
                    shares_change=79561930,
                    status="new",
                ),
            ]
        )
    )
    fake_analysis = AnalysisResult(
        changes=[
            SimpleNamespace(
                participant_id="B01922",
                participant="TEST FIXTURE BROKER ONE",
                previous_shares=0,
                current_shares=554387582,
                share_change=554387582,
                previous_pct_of_issued=0.0,
                current_pct_of_issued=38.2923,
                pct_point_change=38.2923,
                status="new",
            ),
            SimpleNamespace(
                participant_id="B01565",
                participant="TEST FIXTURE BROKER TWO",
                previous_shares=0,
                current_shares=114366170,
                share_change=114366170,
                previous_pct_of_issued=0.0,
                current_pct_of_issued=7.8994,
                pct_point_change=7.8994,
                status="new",
            ),
        ],
        big_changes=[],
        previous_available=True,
    )
    bundle = SimpleNamespace(
        top_n=20,
        prepared=SimpleNamespace(
            response=fake_response,
            analysis=fake_analysis,
        ),
    )

    html = _changes_block(bundle, "en")

    assert 'data-i18n-en="Big changes" data-i18n-zh="大變動">Big changes</span></div><div class="metric-value">3</div>' in html
