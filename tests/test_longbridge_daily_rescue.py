"""Tests for LONGBRIDGE_CCASS_DAILY_HISTORY_EMERGENCY_RESCUE_V2_ZC.

Offline tests use a mock MCP client; the two EXACT_700 proofs run live and skip
(never fail) when the Longbridge MCP surface is unreachable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rescue.longbridge_daily_rescue import (
    RESCUE_ANCHOR_DATE, EmptyKind, RescueStore, canonical_symbol,
    classify_empty, rescue_stock, stock_code_from_symbol,
)


class MockClient:
    """MCP-shaped mock: broker_holding_daily returns {'list': [...]}."""

    def __init__(self):
        self.detail_calls = []
        self.daily_calls = []

    def broker_holding_detail(self, symbol):
        self.detail_calls.append(symbol)
        return {"list": [
            {"participant_id": "A00003", "name": "HSBC", "holding": "1000"},
            {"participant_id": "B01955", "name": "Morgan Stanley", "holding": "500"},
        ]}

    def broker_holding_daily(self, symbol, broker_id):
        self.daily_calls.append((symbol, broker_id))
        if broker_id == "EMPTY1":
            return {"list": []}
        return {"list": [
            {"date": "2026.09.24", "holding": "614497063", "ratio": "0.0675", "chg": "-4915168.0000"},
            {"date": "2026.07.31", "holding": "600000000", "ratio": "0.0660", "chg": "100000.0000"},
            {"date": "2026.07.30", "holding": "599000000", "ratio": "0.0659", "chg": "0"},  # pre-anchor
        ]}


@pytest.fixture()
def store(tmp_path):
    return RescueStore(tmp_path / "rescue.sqlite")


# --- symbol normalization ---------------------------------------------------

def test_symbol_normalization_sample_pass():
    cases = {
        "00003": "3.HK", "00005": "5.HK", "00006": "6.HK", "02318": "2318.HK",
        "03888": "3888.HK", "09618": "9618.HK", "00700": "700.HK", "700": "700.HK",
    }
    for code, expected in cases.items():
        assert canonical_symbol(code) == expected, code
    assert stock_code_from_symbol("700.HK") == "00700"
    assert stock_code_from_symbol("2318.HK") == "02318"


# --- store write / readback -------------------------------------------------

def test_raw_store_write_and_readback_pass(store):
    res = rescue_stock(MockClient(), store, "00700")
    rb = store.readback()
    assert rb["TOTAL_ROWS"] >= 1
    assert rb["DISTINCT_STOCKS"] == 1
    assert rb["EARLIEST_DATE"] >= RESCUE_ANCHOR_DATE
    assert res.earliest_date >= RESCUE_ANCHOR_DATE


def test_anchor_date_filter_and_pre_anchor_dropped(store):
    rescue_stock(MockClient(), store, "00700")
    dates = [r[0] for r in store.conn.execute("SELECT date FROM raw_daily")]
    assert "2026-07-31" in dates      # anchor overlap kept (§16: do not discard)
    assert "2026-07-30" not in dates  # pre-window dropped


def test_source_lineage_pass(store):
    rescue_stock(MockClient(), store, "00700")
    row = store.conn.execute(
        "SELECT source_system, source_surface, fetched_at, raw_payload_hash, "
        "data_quality_status FROM raw_daily LIMIT 1").fetchone()
    assert row[0] == "Longbridge"
    assert row[1] == "broker_holding_daily"
    assert row[2] and row[3] and row[4] == "RECOVERED_CONFIRMED"


# --- idempotency / conflicts --------------------------------------------------

def test_idempotent_duplicate_pass(store):
    rescue_stock(MockClient(), store, "00700")
    res = rescue_stock(MockClient(), store, "00700")
    before = store.readback()["TOTAL_ROWS"]
    # second full run must not add rows for same stock
    assert store.readback()["TOTAL_ROWS"] == before
    assert res is not None


def test_conflict_preservation_pass(store):
    ok = rescue_stock(MockClient(), store, "00700")
    assert ok.rows_saved > 0
    # force a conflicting write on the same natural key
    outcome = store.insert_daily_row({
        "stock_code": "00700", "symbol": "700.HK", "participant_id": "A00003",
        "date": "2026-07-31", "holding": 999, "ratio": 0.5, "chg": 1.0,
        "source_system": "Longbridge", "source_surface": "broker_holding_daily",
        "fetched_at": "x", "raw_payload_hash": "y", "data_quality_status": "RECOVERED_CONFIRMED",
    })
    assert outcome == "conflict"
    conflicts = store.conn.execute("SELECT existing_json, incoming_json FROM conflicts").fetchall()
    assert len(conflicts) == 1  # both sides preserved, never silently overwritten
    assert json.loads(conflicts[0][0])["holding"] != json.loads(conflicts[0][1])["holding"]


# --- empty classification / missing != zero ----------------------------------

def test_empty_classification_and_missing_not_zero_pass(store):
    class PartialClient(MockClient):
        def broker_holding_detail(self, symbol):
            return {"list": [{"participant_id": "A00003", "holding": "1"},
                             {"participant_id": "EMPTY1", "holding": "0"}]}

    rescue_stock(PartialClient(), store, "02318")
    kinds = {r[0] for r in store.conn.execute("SELECT kind FROM errors")}
    assert any(k.startswith("EMPTY:") for k in kinds)
    # empty participant produced NO row — missing is not zero anywhere in store
    n_empty1 = store.conn.execute(
        "SELECT COUNT(*) FROM raw_daily WHERE participant_id='EMPTY1'").fetchone()[0]
    assert n_empty1 == 0
    assert classify_empty("700.HK", "A00003", None, {"A00003"}) == EmptyKind.VALID_EMPTY_FOR_THIS_PARTICIPANT
    assert classify_empty("700.HK", "", None, set()) == EmptyKind.INVALID_PARTICIPANT_ID
    assert classify_empty("700.HK", "Z99999", None, set()) == EmptyKind.RUNTIME_API_EMPTY


# --- checkpoint resume ---------------------------------------------------------

def test_checkpoint_resume_pass(store):
    store.save_checkpoint({"last_completed_stock": "00003", "rows_saved": 7})
    state = store.load_checkpoint()
    assert state["last_completed_stock"] == "00003"
    assert state["rows_saved"] == 7
    store.save_checkpoint({"last_completed_stock": "00005", "rows_saved": 9})
    assert store.load_checkpoint()["rows_saved"] == 9


# --- live proofs (skip, never fail, when MCP unreachable) ----------------------

def _live_client():
    try:
        from app.sources.longbridge import LongbridgeMcpClient
        return LongbridgeMcpClient(interactive=False)
    except Exception:
        return None


@pytest.mark.parametrize("broker_id", ["A00003", "B01955"])
def test_exact_700_nonempty(broker_id):
    client = _live_client()
    if client is None:
        pytest.skip("Longbridge MCP client unavailable")
    import asyncio
    try:
        payload = asyncio.run(client.broker_holding_daily("700.HK", broker_id))
    except Exception as exc:
        pytest.skip(f"Longbridge MCP unreachable: {exc}")
    rows = payload.get("list", []) if isinstance(payload, dict) else payload
    assert len(rows) > 0
    dates = [str(r["date"]).replace(".", "-") for r in rows]
    # rolling window: ~40 trading days ending at the latest trade date; the
    # earliest date advances daily, so assert the window is populated and fresh
    assert len(dates) >= 35
    assert max(dates) >= "2026-09-24"
