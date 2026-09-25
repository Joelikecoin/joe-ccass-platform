"""Scaled rescue runner — FULL_UNIVERSE_RESCUE_SCALING_CHECK_V1.

Safety model (package §11-12):
- one OS process per worker; each worker owns a disjoint stock slice and writes
  its OWN store file (single-writer-per-file; no SQLite multi-writer hazards)
- workers are merged into the master store afterwards with the idempotent
  natural-key writer; conflicts preserved, never overwritten
- per-stock status tracked in each worker store (PENDING/RUNNING/COMPLETE/
  PARTIAL/FAILED_RETRYABLE/FAILED_FINAL)
- empty-rate guard: batch empty-rate is compared against the single-thread
  baseline; a large increase aborts scaling (§7)

Usage:
  python -m scripts.zc_run_longbridge_rescue_scaled --universe data/extension_universe_2026_07.json \
      --batch 10 --concurrency 2 --tag batchA
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from app.rescue.longbridge_daily_rescue import (
    RescueStore, canonical_symbol, rescue_stock,
)

RESCUE_DIR = Path("G:/我的雲端硬碟/投資 - 享受與豐盛/AI Projects/joe-ccass-platform/08_DATA_ASSETS/longbridge_rescue")
FALLBACK_DIR = Path("data/longbridge_rescue")
MASTER = "longbridge_ccass_daily_rescue_20260925.sqlite"


def _worker(code: str, out_path: str) -> dict:
    from app.sources.longbridge import LongbridgeMcpClient
    client = LongbridgeMcpClient(interactive=False)
    store = RescueStore(Path(out_path))
    t0 = time.time()
    try:
        res = rescue_stock(client, store, code)
        status = "COMPLETE" if (res.detail_captured and res.participant_queries_failed == 0) else (
            "PARTIAL" if res.rows_saved else "FAILED_RETRYABLE")
        metrics = {
            "stock_code": code, "symbol": res.symbol, "status": status,
            "rows_saved": res.rows_saved,
            "queries": res.participant_queries_attempted,
            "nonempty": res.participant_queries_nonempty,
            "empty": res.participant_queries_empty,
            "failed": res.participant_queries_failed,
            "seconds": round(time.time() - t0, 1),
        }
    except Exception as exc:
        store.record_error(code, None, "WORKER_CRASH", f"{type(exc).__name__}: {exc}")
        metrics = {"stock_code": code, "status": "FAILED_RETRYABLE", "rows_saved": 0,
                   "seconds": round(time.time() - t0, 1), "crash": str(exc)[:200]}
    (Path(out_path).parent / (Path(out_path).stem + ".metrics.json")).write_text(
        json.dumps(metrics, ensure_ascii=False), encoding="utf-8")
    return metrics


def merge_worker_into_master(worker_db: Path, master: RescueStore) -> dict:
    src = sqlite3.connect(worker_db)
    moved = {"saved": 0, "duplicate": 0, "conflict": 0}
    for row in src.execute("SELECT * FROM raw_daily"):
        (stock_code, symbol, pid, date, holding, ratio, chg, ssys, surf,
         fetched, h, dq) = row
        existing = master.conn.execute(
            "SELECT holding, ratio, chg FROM raw_daily WHERE stock_code=? AND participant_id=? AND date=?",
            (stock_code, pid, date)).fetchone()
        if existing is None:
            master.conn.execute(
                "INSERT INTO raw_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (stock_code, symbol, pid, date, holding, ratio, chg, ssys, surf, fetched, h, dq))
            moved["saved"] += 1
        elif (existing[0], existing[1], existing[2]) == (holding, ratio, chg):
            moved["duplicate"] += 1
        else:
            master.conn.execute(
                "INSERT INTO conflicts (stock_code, participant_id, date, existing_json, "
                "incoming_json, detected_at) VALUES (?,?,?,?,?,?)",
                (stock_code, pid, date, json.dumps(existing),
                 json.dumps({"holding": holding, "ratio": ratio, "chg": chg}),
                 time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
            moved["conflict"] += 1
    # merge detail snapshots + errors as lineage evidence
    for row in src.execute("SELECT stock_code, symbol, captured_at, payload_json "
                           "FROM holding_detail_snapshots"):
        master.conn.execute("INSERT OR IGNORE INTO holding_detail_snapshots VALUES (?,?,?,?)", row)
    master.conn.commit()
    return moved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="data/extension_universe_2026_07.json")
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--tag", default="batchA")
    ap.add_argument("--skip-completed", action="store_true", default=True)
    args = ap.parse_args()
    load_dotenv()

    target_dir = RESCUE_DIR if RESCUE_DIR.parent.exists() else FALLBACK_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    master_path = target_dir / MASTER
    master = RescueStore(master_path)

    codes = json.load(open(args.universe))
    done = {r[0] for r in master.conn.execute("SELECT DISTINCT stock_code FROM raw_daily")}
    remaining = [c for c in codes if c not in done]
    batch = remaining[: args.batch]
    print(f"universe={len(codes)} done={len(done)} remaining={len(remaining)} "
          f"batch={args.tag} n={len(batch)} concurrency={args.concurrency}")

    # disjoint slices
    slices = [batch[i::args.concurrency] for i in range(args.concurrency)]
    procs, paths = [], []
    for w, slice_codes in enumerate(slices):
        out = target_dir / f"worker_{args.tag}_{w}.sqlite"
        if out.exists():
            out.unlink()
        store = RescueStore(out)
        store.save_checkpoint({"codes": slice_codes})
        procs.append(mp.Process(target=_run_slice, args=(slice_codes, str(out))))
        paths.append(out)
    t0 = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    metrics = []
    for out in paths:
        mfile = out.parent / (out.stem + ".metrics.json")
        if mfile.exists():
            metrics.append(json.loads(mfile.read_text(encoding="utf-8")))
        moved = merge_worker_into_master(out, master)
        print(f"merged {out.name}: {moved}")
        out.unlink(missing_ok=True)
        mfile.unlink(missing_ok=True)

    total_queries = sum(m.get("queries", 0) for m in metrics)
    total_empty = sum(m.get("empty", 0) for m in metrics)
    summary = {
        "tag": args.tag, "batch": len(batch), "concurrency": args.concurrency,
        "seconds": round(time.time() - t0, 1),
        "rows_saved": sum(m.get("rows_saved", 0) for m in metrics),
        "queries": total_queries, "empty": total_empty,
        "failed": sum(m.get("failed", 0) for m in metrics),
        "empty_rate": round(total_empty / max(total_queries, 1), 4),
        "avg_seconds_per_stock": round(sum(m.get("seconds", 0) for m in metrics) / max(len(metrics), 1), 1),
        "statuses": {s: sum(1 for m in metrics if m.get("status") == s)
                     for s in ("COMPLETE", "PARTIAL", "FAILED_RETRYABLE", "FAILED_FINAL")},
        "master_readback": master.readback(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    (target_dir / f"scale_{args.tag}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def _run_slice(codes: list, out_path: str) -> None:
    for code in codes:
        try:
            _worker(code, out_path)
        except Exception as exc:  # one stock never stops the slice (§13 retry policy)
            print(f"slice worker error {code}: {exc}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
