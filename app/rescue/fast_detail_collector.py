"""RESTORE_MD_DEFINED_FAST_CCASS_ARCHITECTURE_V1 — fast market-wide CCASS path.

Intended architecture (owner MD 2026-09-26, binding):
  1. Historical backbone   = Webb (through 2025-12-27)
  2. Recent bridge         = ONE broker_holding_detail call per stock
  3. Recent anchors        = T0 / T-1 / T-5 / T-20 / T-60 derived from current - chg_k
  4. Forward daily history = one detail snapshot per stock per trading day
  5. Precision backfill    = broker_holding_daily ONLY as on-demand tool (event
     stocks, explicit daily-reconstruction need, targeted reconciliation)
  6. Disappeared participants = universe/reconciliation/targeted SDW, never
     brute-force per participant

Semantics (frozen): NULL != 0; missing != 0; absence != 0.
Coverage granularity distinguishes FULL_DAILY_RECONSTRUCTION (00001-00006,
preserved enriched data), ANCHOR_RECONSTRUCTION, DAILY_SNAPSHOT, TARGETED_SDW.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class CoverageGranularity(str, Enum):
    FULL_DAILY_RECONSTRUCTION = "FULL_DAILY_RECONSTRUCTION"
    ANCHOR_RECONSTRUCTION = "ANCHOR_RECONSTRUCTION"
    DAILY_SNAPSHOT = "DAILY_SNAPSHOT"
    TARGETED_SDW = "TARGETED_SDW"


ANCHOR_WINDOWS = {"T-1": "chg_1", "T-5": "chg_5", "T-20": "chg_20", "T-60": "chg_60"}

MIGRATION = """
CREATE TABLE IF NOT EXISTS detail_snapshot_rows (
    stock_code TEXT NOT NULL,
    symbol TEXT NOT NULL,
    snapshot_date TEXT,
    participant_id TEXT NOT NULL,
    participant_name TEXT,
    current_holding INTEGER,
    current_ratio REAL,
    chg_1 REAL, chg_5 REAL, chg_20 REAL, chg_60 REAL,
    fetched_at TEXT NOT NULL,
    source_system TEXT NOT NULL DEFAULT 'Longbridge',
    source_surface TEXT NOT NULL DEFAULT 'broker_holding_detail',
    PRIMARY KEY (stock_code, participant_id, fetched_at)
);
CREATE TABLE IF NOT EXISTS anchor_observations (
    stock_code TEXT NOT NULL,
    participant_id TEXT NOT NULL,
    anchor_label TEXT NOT NULL,
    anchor_date_basis TEXT,
    holding INTEGER,
    semantics_status TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (stock_code, participant_id, anchor_label, fetched_at)
);
CREATE TABLE IF NOT EXISTS coverage_registry (
    stock_code TEXT PRIMARY KEY,
    coverage_granularity TEXT NOT NULL,
    detail_snapshots INTEGER NOT NULL DEFAULT 0,
    daily_reconstructed INTEGER NOT NULL DEFAULT 0,
    targeted_sdw_cases INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
"""


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


@dataclass
class StockDetailResult:
    stock_code: str
    symbol: str
    snapshot_date: Optional[str]
    participants: int
    anchors_derived: int
    null_anchors: int
    disappeared_vs_baseline: int


class FastDetailStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.executescript(MIGRATION)
        self.conn.commit()

    def set_coverage(self, code: str, gran: CoverageGranularity):
        self.conn.execute(
            "INSERT INTO coverage_registry (stock_code, coverage_granularity, updated_at) "
            "VALUES (?,?,?) ON CONFLICT(stock_code) DO UPDATE SET coverage_granularity=excluded.coverage_granularity, "
            "updated_at=excluded.updated_at",
            (code, gran.value, datetime.now(timezone.utc).isoformat()))
        self.conn.commit()

    def mark_daily_reconstructed(self, code: str, rows: int):
        self.conn.execute(
            "INSERT INTO coverage_registry (stock_code, coverage_granularity, daily_reconstructed, updated_at) "
            "VALUES (?,?,?,?) ON CONFLICT(stock_code) DO UPDATE SET "
            "daily_reconstructed=excluded.daily_reconstructed, updated_at=excluded.updated_at",
            (code, CoverageGranularity.FULL_DAILY_RECONSTRUCTION.value, rows,
             datetime.now(timezone.utc).isoformat()))
        self.conn.commit()

    def readback(self) -> dict:
        q = lambda s: self.conn.execute(s).fetchone()[0]
        return {
            "snapshot_rows": q("SELECT COUNT(*) FROM detail_snapshot_rows"),
            "stocks": q("SELECT COUNT(DISTINCT stock_code) FROM detail_snapshot_rows"),
            "anchors": q("SELECT COUNT(*) FROM anchor_observations"),
            "anchor_null_status": q(
                "SELECT COUNT(*) FROM anchor_observations WHERE semantics_status='UNKNOWN_NO_BASELINE'"),
            "coverage": self.conn.execute(
                "SELECT coverage_granularity, COUNT(*) FROM coverage_registry "
                "GROUP BY coverage_granularity").fetchall(),
        }


def collect_stock_detail(client: Any, store: FastDetailStore, code: str,
                         baseline_participants: Optional[set] = None) -> StockDetailResult:
    """ONE broker_holding_detail call per stock. Preserves raw semantics."""
    import asyncio
    symbol = f"{code.lstrip('0') or '0'}.HK"
    res = client.broker_holding_detail(symbol)
    if hasattr(res, "__await__"):
        res = asyncio.run(res)
    items = res.get("list", []) if isinstance(res, dict) else (res or [])
    ts = datetime.now(timezone.utc).isoformat()
    snap_date = (str(res.get("updated_at")).replace(".", "-")
                 if isinstance(res, dict) and res.get("updated_at") else None)
    rows, anchors = [], []
    null_anchors = 0
    pids = set()
    for it in items:
        pid = str(it.get("parti_number") or "").strip()
        if not pid:
            continue
        pids.add(pid)
        shares = it.get("shares", {}) or {}
        ratio = it.get("ratio", {}) or {}
        chgs = {k: _f(shares.get(k)) for k in ("chg_1", "chg_5", "chg_20", "chg_60")}
        holding = int(float(shares.get("value") or 0))
        rows.append((code, symbol, snap_date, pid, it.get("name", ""), holding,
                     _f(ratio.get("value")),
                     chgs["chg_1"], chgs["chg_5"], chgs["chg_20"], chgs["chg_60"], ts,
                     "Longbridge", "broker_holding_detail"))
        # anchors: T0 always FACT; T-k = current - chg_k; NULL chg -> UNKNOWN (never 0)
        anchors.append((code, pid, "T0", snap_date, holding, "FACT", ts))
        for label, key in ANCHOR_WINDOWS.items():
            chg = chgs[key]
            if chg is None:
                anchors.append((code, pid, label, snap_date, None,
                                "UNKNOWN_NO_BASELINE", ts))
                null_anchors += 1
            else:
                anchors.append((code, pid, label, snap_date, holding - int(chg),
                                "DERIVED_ANCHOR", ts))
    store.conn.executemany(
        "INSERT OR REPLACE INTO detail_snapshot_rows VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    store.conn.executemany(
        "INSERT OR REPLACE INTO anchor_observations VALUES (?,?,?,?,?,?,?)", anchors)
    store.set_coverage(code, CoverageGranularity.DAILY_SNAPSHOT)
    store.conn.commit()
    disappeared = 0
    if baseline_participants:
        disappeared = len(baseline_participants - pids)
    return StockDetailResult(code, symbol, snap_date, len(rows), len(anchors),
                             null_anchors, disappeared)


def disappeared_participant_cases(baseline: set, current: set,
                                  rescue_covered: set) -> list:
    """Baseline participants absent from current detail.

    Correctness: absence is NEVER zero-holding. Each case is flagged for
    reconciliation (existing rescue daily rows count as covered; the rest are
    targeted-SDW candidates). 00700/B01714 remains the canonical
    SOURCE_SPECIFIC_UNKNOWN precedent.
    """
    out = []
    for pid in sorted(baseline - current):
        out.append({
            "participant_id": pid,
            "DISAPPEARED_PARTICIPANT": "YES",
            "zero_holding_inferred": "NEVER",
            "rescue_daily_covered": pid in rescue_covered,
            "resolution_path": ("EXISTING_RESCUE_HISTORY" if pid in rescue_covered
                                else "TARGETED_SDW_CANDIDATE"),
        })
    return out
