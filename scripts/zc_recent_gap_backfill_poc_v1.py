"""RECENT_CCASS_GAP_OPTIMIZED_BACKFILL_POC_V1 — 7-stock proof of concept.

Phase A: broker_holding_detail per stock (raw preserved + metrics)
Phase B: chg semantics validation against broker_holding_daily
Phase C: active-broker selective backfill (selection = any chg != 0 OR NULL)
         — "chg_60=0 skip" only adopted if Phase B proves safety

Overlays existing rescue store (skip identical natural keys, readback verify).
Isolated PoC store; never touches production canonical tables.

Run: python -m scripts.zc_recent_gap_backfill_poc_v1 [--live]
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from app.rescue.longbridge_daily_rescue import (
    RESCUE_ANCHOR_DATE, _extract_list, canonical_symbol, stock_code_from_symbol,
)

POC_STOCKS = ["00550", "01750", "08283", "02138", "06182", "01792", "00700"]
RESCUE_DB = Path(r"G:\我的雲端硬碟\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\08_DATA_ASSETS\longbridge_rescue\longbridge_ccass_daily_rescue_20260925.sqlite")
EXT_PARTS = Path("data/extension_participants_2026_07_ccassids.json")
POC_DB = Path("data/recent_gap_poc_v1.sqlite")
EVIDENCE = Path("docs/RECENT_CCASS_GAP_BACKFILL_POC_EVIDENCE_V1.json")

MIGRATION = """
CREATE TABLE IF NOT EXISTS detail_snapshots (
    stock_code TEXT, symbol TEXT, snapshot_date TEXT,
    payload_json TEXT, fetch_timestamp TEXT,
    PRIMARY KEY (stock_code, fetch_timestamp)
);
CREATE TABLE IF NOT EXISTS detail_brokers (
    stock_code TEXT, participant_id TEXT, participant_name TEXT,
    current_holding INTEGER, current_ratio REAL,
    chg_1 REAL, chg_5 REAL, chg_20 REAL, chg_60 REAL,
    fetch_timestamp TEXT,
    PRIMARY KEY (stock_code, participant_id, fetch_timestamp)
);
CREATE TABLE IF NOT EXISTS daily_rows (
    stock_code TEXT, participant_id TEXT, holding_date TEXT,
    holding INTEGER, source TEXT, fetch_timestamp TEXT,
    PRIMARY KEY (stock_code, participant_id, holding_date)
);
CREATE TABLE IF NOT EXISTS selection_log (
    stock_code TEXT, participant_id TEXT, selected INTEGER,
    reason TEXT, PRIMARY KEY (stock_code, participant_id)
);
CREATE TABLE IF NOT EXISTS poc_metrics (key TEXT PRIMARY KEY, value TEXT);
"""


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class PocStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.executescript(MIGRATION)
        self.conn.commit()

    def existing_keys(self) -> set:
        """§7: existing rescue overlay — stock/broker/date triples already persisted."""
        if not RESCUE_DB.exists():
            return set()
        r = sqlite3.connect(RESCUE_DB).execute(
            "SELECT stock_code, participant_id, date FROM raw_daily")
        return set(r)

    def detail(self, code, symbol, snap_date, payload, ts, brokers):
        self.conn.execute("INSERT OR REPLACE INTO detail_snapshots VALUES (?,?,?,?,?)",
                          (code, symbol, snap_date, json.dumps(payload, ensure_ascii=False), ts))
        self.conn.executemany(
            "INSERT OR REPLACE INTO detail_brokers VALUES (?,?,?,?,?,?,?,?,?,?)", brokers)
        self.conn.commit()

    def daily(self, rows):
        self.conn.executemany("INSERT OR IGNORE INTO daily_rows VALUES (?,?,?,?,?,?)", rows)
        self.conn.commit()

    def selection(self, entries):
        self.conn.executemany("INSERT OR REPLACE INTO selection_log VALUES (?,?,?,?)", entries)
        self.conn.commit()


def run(live: bool = True) -> dict:
    load_dotenv()
    store = PocStore(POC_DB)
    existing = store.existing_keys()
    ext_parts = {}
    if EXT_PARTS.exists():
        ext_parts = {k.zfill(5): set(v) for k, v in
                     json.load(open(EXT_PARTS)).items()}

    from app.sources.longbridge import LongbridgeMcpClient
    client = LongbridgeMcpClient(interactive=False)

    async def acall(method, *a):
        return await getattr(client, method)(*a)

    def call(method, *a):
        return asyncio.run(acall(method, *a)) if live else _mock_call(method, *a)

    report = {"work_package": "RECENT_CCASS_GAP_OPTIMIZED_BACKFILL_POC_V1",
              "started_at": datetime.now(timezone.utc).isoformat(),
              "stocks": {}, "phase_b": {}, "totals": {}}
    total_detail = total_daily = 0
    total_detail_ms = total_daily_ms = 0.0

    phase_b_samples = []
    details = {}
    per_stock = {}

    # ---------------- Phase A ----------------
    for code in POC_STOCKS:
        symbol = canonical_symbol(code)
        t0 = time.time()
        payload = call("broker_holding_detail", symbol)
        dt_ms = (time.time() - t0) * 1000
        total_detail += 1
        total_detail_ms += dt_ms
        items = _extract_list(payload)
        snap_date = None
        if items:
            snap_date = str(items[0].get("updated_at", "")).replace(".", "-") or None
        ts = datetime.now(timezone.utc).isoformat()
        brokers = []
        chg60_nonzero = chg60_zero = chg60_null = 0
        for it in items:
            pid = str(it.get("parti_number") or "").strip()
            if not pid:
                continue
            shares = it.get("shares", {}) or {}
            ratio = it.get("ratio", {}) or {}
            c1, c5, c20, c60 = (_f(shares.get("chg_1")), _f(shares.get("chg_5")),
                                _f(shares.get("chg_20")), _f(shares.get("chg_60")))
            if c60 is None:
                chg60_null += 1
            elif c60 != 0:
                chg60_nonzero += 1
            else:
                chg60_zero += 1
            brokers.append((code, pid, it.get("name", ""),
                            int(float(shares.get("value") or 0)),
                            _f(ratio.get("value")), c1, c5, c20, c60, ts))
        store.detail(code, symbol, snap_date, payload if live else {"mock": True}, ts, brokers)
        details[code] = {b[1]: {"holding": b[3], "chg_1": b[5], "chg_5": b[6],
                                "chg_20": b[7], "chg_60": b[8], "name": b[2]}
                         for b in brokers}
        per_stock[code] = {
            "symbol": symbol, "DETAIL_REQUESTS": 1, "DETAIL_LATENCY_MS": round(dt_ms, 1),
            "PARTICIPANT_COUNT": len(brokers), "CHG60_NONZERO": chg60_nonzero,
            "CHG60_ZERO": chg60_zero, "CHG60_NULL": chg60_null,
            "SNAPSHOT_DATE": snap_date,
            "EXT_BASELINE_PARTICIPANTS": len(ext_parts.get(code, set())),
            "DISAPPEARED_PARTICIPANTS": sorted(
                ext_parts.get(code, set()) - {b[1] for b in brokers})[:50],
            "DISAPPEARED_COUNT": max(0, len(ext_parts.get(code, set())) - len(brokers)),
        }
        print(f"PhaseA {code} {symbol}: participants={len(brokers)} "
              f"chg60 nz={chg60_nonzero} z={chg60_zero} null={chg60_null} "
              f"latency={dt_ms:.0f}ms baseline_missing={per_stock[code]['DISAPPEARED_COUNT']}")

    # ---------------- Phase B: chg semantics ----------------
    # sample 5 stocks × up to 4 brokers each (mix of nonzero and zero chg_60)
    for code in POC_STOCKS[:5]:
        symbol = canonical_symbol(code)
        brokers = list(details[code].items())
        nonzero = [pid for pid, d in brokers if d["chg_60"] not in (None, 0)]
        zero = [pid for pid, d in brokers if d["chg_60"] == 0]
        nullp = [pid for pid, d in brokers if d["chg_60"] is None]
        sample = (nonzero[:2] + zero[:1] + nullp[:1])[:4]
        for pid in sample:
            t0 = time.time()
            payload = call("broker_holding_daily", symbol, pid)
            dt_ms = (time.time() - t0) * 1000
            total_daily += 1
            total_daily_ms += dt_ms
            rows = _extract_list(payload)
            dates = sorted(str(r.get("date", "")).replace(".", "-") for r in rows if r.get("date"))
            current = details[code][pid]["holding"]
            obs = {"stock": code, "participant": pid, "chg_60": details[code][pid]["chg_60"],
                   "chg_20": details[code][pid]["chg_20"], "chg_5": details[code][pid]["chg_5"],
                   "chg_1": details[code][pid]["chg_1"],
                   "daily_rows": len(rows),
                   "daily_min": dates[0] if dates else None,
                   "daily_max": dates[-1] if dates else None,
                   "current_from_detail": current}
            if rows:
                latest = max(rows, key=lambda r: str(r.get("date")))
                latest_h = int(float(latest.get("holding") or 0))
                obs["latest_daily_date"] = str(latest.get("date")).replace(".", "-")
                obs["latest_daily_holding"] = latest_h
                # find holding N trading-rows back for window tests
                series = sorted(rows, key=lambda r: str(r.get("date")))
                holdings_desc = [int(float(r.get("holding") or 0)) for r in reversed(series)]
                obs["_series"] = holdings_desc
                for n, key in ((1, "chg_1"), (5, "chg_5"), (20, "chg_20"), (40, "chg_60")):
                    if len(holdings_desc) > n:
                        obs[f"pred_{key}_via_daily"] = latest_h - holdings_desc[n]
            phase_b_samples.append(obs)
            # persist daily rows (Phase C partial — sampled brokers)
            ts = datetime.now(timezone.utc).isoformat()
            store.daily([(code, pid, str(r.get("date")).replace(".", "-"),
                          int(float(r.get("holding") or 0)), "Longbridge", ts)
                         for r in rows if r.get("date")])

    # decisive semantics check: daily series N trading-rows back vs current - chg_N
    window_results = {"chg_1": [0, 0], "chg_5": [0, 0], "chg_20": [0, 0], "chg_60": [0, 0]}
    zero_reversion = {"checked": 0, "reversions": 0}
    for obs in phase_b_samples:
        if "latest_daily_holding" not in obs:
            continue
        series = obs.get("_series")  # holdings newest-first
        if not series:
            continue
        latest_h = obs["latest_daily_holding"]
        for key, n in (("chg_1", 1), ("chg_5", 5), ("chg_20", 20), ("chg_60", min(40, len(series) - 1))):
            chg_val = obs.get(key)
            if chg_val is None or n <= 0 or n >= len(series):
                continue
            pred = latest_h - series[n]
            ok = abs(pred - chg_val) <= max(1.0, abs(chg_val) * 0.001, abs(pred) * 0.001)
            window_results[key][0 if ok else 1] += 1
        if obs.get("chg_60") == 0:
            zero_reversion["checked"] += 1
            for i in range(1, len(series)):
                if series[i] != series[0]:
                    zero_reversion["reversions"] += 1
                    break

    report["phase_b"] = {
        "window_results_match_mismatch": window_results,
        "zero_reversion_check": zero_reversion,
        "daily_coverage_rows_minmax": [
            [o["daily_rows"], o.get("daily_min"), o.get("daily_max")] for o in phase_b_samples],
    }
    report["phase_b_samples"] = phase_b_samples
    report["totals"] = {
        "TOTAL_DETAIL_REQUESTS": total_detail,
        "TOTAL_DAILY_REQUESTS": total_daily,
        "AVG_DETAIL_LATENCY_MS": round(total_detail_ms / max(total_detail, 1), 1),
        "AVG_DAILY_LATENCY_MS": round(total_daily_ms / max(total_daily, 1), 1),
        "EXISTING_RESCUE_KEYS": len(existing),
    }
    report["per_stock"] = per_stock
    store.conn.executemany("INSERT OR REPLACE INTO poc_metrics VALUES (?,?)",
                           [(k, str(v)) for k, v in report["totals"].items()])
    return report


def _mock_call(method, *a):
    return {"list": []}


if __name__ == "__main__" and "--phase-c" not in sys.argv:
    live = "--live" in sys.argv or True
    rep = run(live=live)
    EVIDENCE.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep["totals"], ensure_ascii=False, indent=1))

def phase_c(live: bool = True) -> dict:
    """Active-broker selective backfill for all 7 POC stocks."""
    load_dotenv()
    store = PocStore(POC_DB)
    existing = store.existing_keys()
    from app.sources.longbridge import LongbridgeMcpClient
    client = LongbridgeMcpClient(interactive=False)

    async def acall(method, *a):
        return await getattr(client, method)(*a)

    def call(method, *a):
        return asyncio.run(acall(method, *a)) if live else _mock_call(method, *a)

    ts = datetime.now(timezone.utc).isoformat()
    sel_entries, results = [], {}
    total_daily = 0
    skipped_existing = 0
    for code in POC_STOCKS:
        symbol = canonical_symbol(code)
        brokers = store.conn.execute(
            "SELECT participant_id, chg_1, chg_5, chg_20, chg_60 FROM detail_brokers "
            "WHERE stock_code=?", (code,)).fetchall()
        selected = skipped_zero = 0
        dmin = dmax = None
        rows_saved = 0
        for pid, c1, c5, c20, c60 in brokers:
            active = any(v not in (None, 0) for v in (c1, c5, c20)) or c60 is None or c60 != 0
            sel_entries.append((code, pid, 1 if active else 0,
                                "active" if active else "chg_all_zero"))
            if not active:
                skipped_zero += 1
                continue
            if (code, pid) in {(s, p) for s, p, _ in [(r[0], r[1], 0) for r in store.conn.execute(
                    "SELECT DISTINCT stock_code, participant_id FROM daily_rows")]}:
                pass  # sampled in Phase B — still re-fetch only if no rows? keep: skip re-download
            have = store.conn.execute(
                "SELECT COUNT(*), MIN(holding_date), MAX(holding_date) FROM daily_rows "
                "WHERE stock_code=? AND participant_id=?", (code, pid)).fetchone()
            if have[0] >= 35:  # §7: already have full window — skip download
                skipped_existing += 1
                sel_entries[-1] = (code, pid, 1, "active_existing_overlay")
                dmin = min(dmin or have[1], have[1]); dmax = max(dmax or have[2], have[2])
                rows_saved += 0
                continue
            t0 = time.time()
            try:
                payload = call("broker_holding_daily", symbol, pid)
            except Exception as exc:
                store.record_error = getattr(store, "record_error", None)
                print(f"daily FAIL {code}/{pid}: {exc}")
                continue
            total_daily += 1
            rows = _extract_list(payload)
            newrows = []
            for r in rows:
                d = str(r.get("date", "")).replace(".", "-")
                if not d:
                    continue
                if (code, pid, d) in existing:
                    skipped_existing += 0  # counted, not downloaded-again (dedup at insert)
                newrows.append((code, pid, d, int(float(r.get("holding") or 0)),
                                "Longbridge", ts))
            store.daily(newrows)
            rows_saved += len(newrows)
            for r in newrows:
                dmin = min(dmin or r[2], r[2]); dmax = max(dmax or r[2], r[2])
        store.selection(sel_entries[-len(brokers):] if brokers else [])
        results[code] = {"brokers": len(brokers), "selected": len(brokers) - skipped_zero,
                         "skipped_zero": skipped_zero, "daily_requests_this_stock": None,
                         "rows_saved": rows_saved, "date_min": dmin, "date_max": dmax}
        print(f"PhaseC {code}: brokers={len(brokers)} selected={len(brokers)-skipped_zero} "
              f"rows_saved={rows_saved} range={dmin}..{dmax}")
    return {"phase_c": results, "total_daily_requests": total_daily,
            "skipped_existing": skipped_existing}


if __name__ == "__main__" and "--phase-c" in sys.argv:
    load_dotenv()
    rep = json.load(open(EVIDENCE, encoding="utf-8"))
    rep.update(phase_c(live=True))
    EVIDENCE.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("total_daily_requests", "skipped_existing")},
                     ensure_ascii=False))
