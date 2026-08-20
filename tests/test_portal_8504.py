from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace

from app.friend_clone_app import PortalBundle
from app.portal_8504 import (
    PRICE_HISTORY_LOAD_TIMEOUT_SECONDS,
    Portal8504Bundle,
    _build_portal_8504_bundle,
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
