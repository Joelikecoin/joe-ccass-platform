"""Generate docs/LONGBRIDGE_DAILY_CCASS_RESCUE_COVERAGE_V2.json from the rescue store.

Run after (or during) the rescue: python -m scripts.zc_rescue_coverage_v2
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

STORE = Path("G:/我的雲端硬碟/投資 - 享受與豐盛/AI Projects/joe-ccass-platform/08_DATA_ASSETS/longbridge_rescue/longbridge_ccass_daily_rescue_20260925.sqlite")
FALLBACK = Path("data/longbridge_rescue/longbridge_ccass_daily_rescue_20260925.sqlite")
OUT = Path("docs/LONGBRIDGE_DAILY_CCASS_RESCUE_COVERAGE_V2.json")


def main() -> int:
    path = STORE if STORE.exists() else FALLBACK
    if not path.exists():
        print("rescue store not found")
        return 1
    import sqlite3
    conn = sqlite3.connect(path)
    q = lambda sql: conn.execute(sql).fetchone()[0]

    per_date = [
        {"date": d, "stock_count": s, "participant_count": p, "row_count": n,
         "status": "RECOVERED_CONFIRMED"}
        for d, s, p, n in conn.execute(
            "SELECT date, COUNT(DISTINCT stock_code), COUNT(DISTINCT participant_id), "
            "COUNT(*) FROM raw_daily GROUP BY date ORDER BY date")]
    per_stock = [
        {"stock_code": c, "symbol": sym, "earliest_date": e, "latest_date": l,
         "date_count": dc, "participant_count": pc}
        for c, sym, e, l, dc, pc in conn.execute(
            "SELECT stock_code, MIN(symbol), MIN(date), MAX(date), COUNT(DISTINCT date), "
            "COUNT(DISTINCT participant_id) FROM raw_daily GROUP BY stock_code ORDER BY stock_code")]

    aug = conn.execute("SELECT COUNT(*), COUNT(DISTINCT stock_code) FROM raw_daily "
                       "WHERE date BETWEEN '2026-08-01' AND '2026-09-08'").fetchone()
    doc = {
        "schema": "LONGBRIDGE_DAILY_CCASS_RESCUE_COVERAGE_V2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rescue_store": str(path),
        "rescue_store_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "totals": {
            "TOTAL_ROWS": q("SELECT COUNT(*) FROM raw_daily"),
            "DISTINCT_STOCKS": q("SELECT COUNT(DISTINCT stock_code) FROM raw_daily"),
            "DISTINCT_PARTICIPANTS": q("SELECT COUNT(DISTINCT participant_id) FROM raw_daily"),
            "DISTINCT_DATES": q("SELECT COUNT(DISTINCT date) FROM raw_daily"),
            "EARLIEST_DATE": q("SELECT MIN(date) FROM raw_daily"),
            "LATEST_DATE": q("SELECT MAX(date) FROM raw_daily"),
            "CONFLICTING_DUPLICATE_COUNT": q("SELECT COUNT(*) FROM conflicts"),
            "ERROR_COUNT": q("SELECT COUNT(*) FROM errors"),
        },
        "august_gap": {"AUG_01_TO_SEP_08_ROWS": aug[0],
                       "AUG_01_TO_SEP_08_STOCK_COUNT": aug[1],
                       "status": "RECOVERED" if aug[0] > 0 else "UNKNOWN"},
        "per_date": per_date,
        "per_stock": per_stock,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(doc["totals"], ensure_ascii=False))
    print("august:", doc["august_gap"]["status"], aug[0], "rows")
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
