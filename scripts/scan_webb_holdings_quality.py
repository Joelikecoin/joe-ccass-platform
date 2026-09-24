"""One-pass, read-only quality scan of the imported Webb holdings corpus."""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from collections import defaultdict
from datetime import date
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    connection = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
    issue_ids = {str(row[0]) for row in connection.execute("SELECT DISTINCT c1 FROM shortnames")}
    participant_ids = {str(row[0]) for row in connection.execute("SELECT c1 FROM participants")}
    yearly_issues: dict[str, set[str]] = defaultdict(set)
    yearly_participants: dict[str, set[str]] = defaultdict(set)
    counts = defaultdict(int)
    prior_key: tuple[int, int, str] | None = None
    prior_value: int | None = None
    current_pair: tuple[int, int] | None = None
    current_pair_holding: int | None = None
    started = time.time()
    cursor = connection.execute("SELECT c1,c2,c3,c4 FROM holdings ORDER BY rowid")
    while True:
        batch = cursor.fetchmany(100_000)
        if not batch:
            break
        for part_raw, issue_raw, holding_raw, date_raw in batch:
            counts["rows"] += 1
            part_id, issue_id = str(part_raw), str(issue_raw)
            try:
                part_number, issue_number, holding = int(part_id), int(issue_id), int(holding_raw)
            except (TypeError, ValueError):
                counts["invalid_numeric"] += 1
                continue
            date_text = str(date_raw)
            try:
                parsed = date.fromisoformat(date_text)
            except ValueError:
                counts["invalid_dates"] += 1
                continue
            # Webb's native holdings primary key is (issueID, partID, atDate).
            key = (issue_number, part_number, date_text)
            if prior_key is not None and key < prior_key:
                counts["source_order_violations"] += 1
            if key == prior_key:
                counts["duplicate_natural_keys"] += 1
                if holding != prior_value:
                    counts["conflicting_natural_keys"] += 1
            if holding < 0:
                counts["negative_holdings"] += 1
            if holding > 1_000_000_000_000:
                counts["extreme_over_1tn"] += 1
            if issue_id not in issue_ids:
                counts["orphan_issue_rows"] += 1
            if part_id not in participant_ids:
                counts["orphan_participant_rows"] += 1
            pair = (issue_number, part_number)
            if pair != current_pair:
                counts["distinct_issue_participant_pairs"] += 1
                current_pair = pair
                current_pair_holding = None
            if holding == 0 and current_pair_holding is not None and current_pair_holding > 0:
                counts["zero_transitions"] += 1
            if holding > 0 and current_pair_holding == 0:
                counts["reentries_after_zero"] += 1
            current_pair_holding = holding
            year = str(parsed.year)
            yearly_issues[year].add(issue_id)
            yearly_participants[year].add(part_id)
            prior_key, prior_value = key, holding
        if counts["rows"] % 5_000_000 == 0:
            print(json.dumps({"rows": counts["rows"], "elapsed_seconds": round(time.time()-started, 1)}), flush=True)
    result = {
        "source": str(args.database),
        "elapsed_seconds": round(time.time() - started, 2),
        **dict(counts),
        "yearly_change_issue_count": {year: len(values) for year, values in sorted(yearly_issues.items())},
        "yearly_change_participant_count": {year: len(values) for year, values in sorted(yearly_participants.items())},
        "duplicate_check_complete": counts["source_order_violations"] == 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
