"""Rescue runner CLI — LONGBRIDGE_CCASS_DAILY_HISTORY_EMERGENCY_RESCUE_V2_ZC.

Usage:
  python -m scripts.zc_run_longbridge_rescue [--max-stocks N] [--db PATH] [--live]

Default is LIVE capture (time-critical preservation). Universe comes from the
production Turso `stocks` table (priority 3). Checkpoints every 10 stocks.
Never touches production canonical tables; writes only the isolated rescue store.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from app.rescue.longbridge_daily_rescue import (
    RescueStore, build_universe_from_turso, rescue_stock,
)

RESCUE_DIR = Path("G:/我的雲端硬碟/投資 - 享受與豐盛/AI Projects/joe-ccass-platform/08_DATA_ASSETS/longbridge_rescue")
FALLBACK_DIR = Path("data/longbridge_rescue")
CHECKPOINT_EVERY = 10


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-stocks", type=int, default=0, help="0 = all")
    ap.add_argument("--db", type=str, default="")
    ap.add_argument("--participants", type=str, default="",
                    help="comma-separated participant ids to union into every stock")
    args = ap.parse_args()
    load_dotenv()

    target_dir = RESCUE_DIR if RESCUE_DIR.parent.exists() else FALLBACK_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    db_path = Path(args.db) if args.db else target_dir / "longbridge_ccass_daily_rescue_20260925.sqlite"
    store = RescueStore(db_path)

    url = os.getenv("TURSO_DATABASE_URL", "").replace("libsql://", "https://")
    token = os.getenv("TURSO_AUTH_TOKEN", "")
    universe = build_universe_from_turso(url, token)
    codes = universe["codes"]
    if args.max_stocks:
        codes = codes[: args.max_stocks]
    print(f"UNIVERSE={universe['STOCK_UNIVERSE_COUNT']} using={len(codes)} "
          f"(priority={universe['universe_priority']}, "
          f"P1_extension_available={universe['PRIORITY1_EXTENSION_UNIVERSE_AVAILABLE']})")

    from app.sources.longbridge import LongbridgeMcpClient
    client = LongbridgeMcpClient(interactive=False)
    extra = [p.strip() for p in args.participants.split(",") if p.strip()]

    ckpt = store.load_checkpoint() or {"last_completed_stock": "", "stocks_attempted": 0,
                                       "stocks_completed": 0, "rows_saved": 0,
                                       "queries_attempted": 0, "queries_nonempty": 0,
                                       "queries_empty": 0, "queries_failed": 0}
    done = set()
    for r in store.conn.execute("SELECT DISTINCT stock_code FROM raw_daily"):
        done.add(r[0])

    for i, code in enumerate(codes, 1):
        if code in done:
            continue
        res = rescue_stock(client, store, code, extra_participants=extra)
        ckpt["last_completed_stock"] = code
        ckpt["stocks_attempted"] += 1
        ckpt["stocks_completed"] += 1 if res.detail_captured or res.rows_saved else 0
        ckpt["rows_saved"] += res.rows_saved
        ckpt["queries_attempted"] += res.participant_queries_attempted
        ckpt["queries_nonempty"] += res.participant_queries_nonempty
        ckpt["queries_empty"] += res.participant_queries_empty
        ckpt["queries_failed"] += res.participant_queries_failed
        print(f"[{i}/{len(codes)}] {code} symbol={res.symbol} rows_saved={res.rows_saved} "
              f"participants={res.participant_queries_attempted} "
              f"(nonempty={res.participant_queries_nonempty} empty={res.participant_queries_empty} "
              f"failed={res.participant_queries_failed})")
        if i % CHECKPOINT_EVERY == 0:
            store.save_checkpoint(ckpt)
            print("  checkpoint saved")

    store.save_checkpoint(ckpt)
    rb = store.readback()
    rb["AUGUST"] = store.august_gap_stats()
    rb["CHECKPOINT"] = ckpt
    print(json.dumps(rb, ensure_ascii=False, indent=1))
    (target_dir / "rescue_readback_20260925.json").write_text(
        json.dumps(rb, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
