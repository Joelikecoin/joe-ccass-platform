"""Filter the rescue universe down to stocks not yet in the master store."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "extension_universe_2026_07.json"
OUT = REPO / "data" / "extension_universe_20260926_remaining.json"
MASTER = REPO / "data" / "longbridge_rescue" / "longbridge_ccass_daily_rescue_20260925.sqlite"


def main() -> None:
    universe = json.loads(SRC.read_text(encoding="utf-8"))
    con = sqlite3.connect(MASTER)
    done = {row[0] for row in con.execute("SELECT DISTINCT stock_code FROM raw_daily")}
    con.close()
    remaining = [c for c in universe if c not in done]
    OUT.write_text(json.dumps(remaining), encoding="utf-8")
    print("universe", len(universe), "done", len(done), "remaining", len(remaining))
    print("out", OUT)


if __name__ == "__main__":
    main()
