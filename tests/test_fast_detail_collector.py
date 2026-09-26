"""Tests for RESTORE_MD_DEFINED_FAST_CCASS_ARCHITECTURE_V1 (fast detail path)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rescue.fast_detail_collector import (
    ANCHOR_WINDOWS, CoverageGranularity, FastDetailStore,
    collect_stock_detail, disappeared_participant_cases,
)


class MockDetailClient:
    def broker_holding_detail(self, symbol):
        return {"updated_at": "2026.09.25", "list": [
            {"name": "A", "parti_number": "A00003",
             "shares": {"value": "1000", "chg_1": "100", "chg_5": "200",
                        "chg_20": "300", "chg_60": "400"},
             "ratio": {"value": "0.01"}},
            {"name": "B", "parti_number": "B00001",
             "shares": {"value": "500", "chg_1": None, "chg_5": "0",
                        "chg_20": "-50", "chg_60": None},
             "ratio": {"value": "0.005"}},
        ]}


@pytest.fixture()
def store(tmp_path):
    return FastDetailStore(tmp_path / "fast.sqlite")


def test_one_stock_one_detail_call(store):
    r = collect_stock_detail(MockDetailClient(), store, "00550")
    assert r.participants == 2
    assert r.snapshot_date == "2026-09-25"
    rows = store.conn.execute("SELECT COUNT(*) FROM detail_snapshot_rows").fetchone()[0]
    assert rows == 2


def test_anchor_semantics_null_is_not_zero(store):
    collect_stock_detail(MockDetailClient(), store, "00550")
    # NULL chg -> UNKNOWN_NO_BASELINE with holding NULL (never 0)
    rows = store.conn.execute(
        "SELECT holding, semantics_status FROM anchor_observations "
        "WHERE participant_id='B00001' AND anchor_label IN ('T-1','T-60')").fetchall()
    assert all(h is None and s == "UNKNOWN_NO_BASELINE" for h, s in rows)
    n = store.conn.execute(
        "SELECT COUNT(*) FROM anchor_observations WHERE holding=0 "
        "AND semantics_status='UNKNOWN_NO_BASELINE'").fetchone()[0]
    assert n == 0


def test_anchor_derivation_matches_current_minus_chg(store):
    collect_stock_detail(MockDetailClient(), store, "00550")
    a = store.conn.execute(
        "SELECT anchor_label, holding FROM anchor_observations "
        "WHERE participant_id='A00003' ORDER BY anchor_label").fetchall()
    d = dict(a)
    assert d["T0"] == 1000 and d["T-1"] == 900 and d["T-5"] == 800
    assert d["T-20"] == 700 and d["T-60"] == 600


def test_zero_chg_still_yields_derived_anchor(store):
    """chg_5=0 -> T-5 anchor equals current (a FACT-level derivation, not skipped)."""
    collect_stock_detail(MockDetailClient(), store, "00550")
    h = store.conn.execute(
        "SELECT holding, semantics_status FROM anchor_observations "
        "WHERE participant_id='B00001' AND anchor_label='T-5'").fetchone()
    assert h == (500, "DERIVED_ANCHOR")


def test_absence_is_not_zero_disappeared_cases(store):
    baseline = {"A00003", "B00001", "C00009"}
    cases = disappeared_participant_cases(baseline, {"A00003", "B00001"}, set())
    assert len(cases) == 1
    assert cases[0]["participant_id"] == "C00009"
    assert cases[0]["DISAPPEARED_PARTICIPANT"] == "YES"
    assert cases[0]["zero_holding_inferred"] == "NEVER"
    assert cases[0]["resolution_path"] == "TARGETED_SDW_CANDIDATE"


def test_disappeared_covered_by_rescue_history():
    cases = disappeared_participant_cases({"X00001"}, set(), {"X00001"})
    assert cases[0]["resolution_path"] == "EXISTING_RESCUE_HISTORY"


def test_coverage_granularity_registry(store):
    collect_stock_detail(MockDetailClient(), store, "00550")
    store.mark_daily_reconstructed("00006", 11204)
    cov = dict(store.conn.execute(
        "SELECT stock_code, coverage_granularity FROM coverage_registry").fetchall())
    assert cov["00550"] == CoverageGranularity.DAILY_SNAPSHOT.value
    assert cov["00006"] == CoverageGranularity.FULL_DAILY_RECONSTRUCTION.value


def test_anchor_windows_frozen():
    assert ANCHOR_WINDOWS == {"T-1": "chg_1", "T-5": "chg_5",
                              "T-20": "chg_20", "T-60": "chg_60"}


def test_seven_stock_proof_no_daily_brute_force():
    import json
    p = Path(__file__).parent.parent / "docs" / "MD_FAST_ARCHITECTURE_7_STOCK_PROOF.json"
    if not p.exists():
        pytest.skip("proof not run yet")
    d = json.load(open(p, encoding="utf-8"))
    assert d["DETAIL_REQUESTS_TOTAL"] == 7
    assert d["DAILY_REQUESTS_TOTAL"] == 0  # NO brute-force by default
    assert len(d["poc_stocks"]) == 7
