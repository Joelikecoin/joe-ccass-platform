"""Read-only CLI for Webb change-log position reconstruction."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path

from app.services.webb_sparse_holdings import reconstruct_issue_dates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--issue-id", required=True)
    parser.add_argument("--date", action="append", required=True, dest="dates")
    parser.add_argument("--include-rows", action="store_true")
    arguments = parser.parse_args()
    requested_dates = [date.fromisoformat(value) for value in arguments.dates]
    uri = f"file:{arguments.database.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        results = reconstruct_issue_dates(connection, arguments.issue_id, requested_dates)
    if not arguments.include_rows:
        for result in results:
            result.pop("participant_rows", None)
    print(json.dumps(results, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
