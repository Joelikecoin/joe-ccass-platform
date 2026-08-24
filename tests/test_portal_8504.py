from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.friend_clone_app import PortalBundle
from app.portal_8504 import (
    PRICE_HISTORY_LOAD_TIMEOUT_SECONDS,
    app as portal_app,
    Portal8504Bundle,
    _build_portal_8504_bundle,
    _overview_block,
    _price_panel,
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
        company={},
        latest_price={},
        price_history=[],
        announcements=[],
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

    def fake_build_live_product_from_response(response, *, source_trace):
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
    monkeypatch.setattr("app.friend_clone_app.build_live_product_from_response", fake_build_live_product_from_response)
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
    assert calls["ccass"] == ["en"]


def test_portal_8504_download_route_lazy_generates_zh_markdown(monkeypatch):
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
        company={},
        latest_price={},
        price_history=[],
        announcements=[],
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

    client = TestClient(portal_app)
    live_response = client.get(
        "/download/live/md",
        params={"code": "01592", "locale": "zh_HK"},
    )
    ccass_response = client.get(
        "/download/ccass/md",
        params={"code": "01592", "locale": "zh_HK"},
    )

    assert live_response.status_code == 200
    assert live_response.text == "ZH LIVE"
    assert ccass_response.status_code == 200
    assert ccass_response.text == "ZH CCASS"
    assert calls["live"] == ["zh_HK"]
    assert calls["ccass"] == ["zh_HK"]


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
