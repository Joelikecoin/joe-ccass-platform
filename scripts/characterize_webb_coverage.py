"""Produce year-level source coverage using dailylog trading-date semantics."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--quality", required=True, type=Path)
    parser.add_argument("--issue-identity", required=True, type=Path)
    parser.add_argument("--research-store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    quality = json.loads(args.quality.read_text(encoding="utf-8"))
    with args.issue_identity.open(encoding="utf-8") as handle:
        identity = {row["source_issue_id"]: row["mapping_status"] for row in csv.DictReader(handle)}
    connection = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
    dates: dict[int, set[str]] = defaultdict(set)
    issues: dict[int, set[str]] = defaultdict(set)
    for at_date, issue_id in connection.execute("SELECT c1,c2 FROM dailylog"):
        year = int(str(at_date)[:4])
        dates[year].add(str(at_date)); issues[year].add(str(issue_id))
    output = []
    for year in range(2007, 2026):
        issue_set = issues[year]
        mapped = sum(identity.get(issue) in {"EXACT", "DATE_BOUNDED"} for issue in issue_set)
        output.append({
            "year": year, "issue_count": len(issue_set),
            "source_date_count": len(dates[year]),
            "reconstructable_issue_count": len(issue_set),
            "identity_mapped_issue_count": mapped,
            "participant_count": quality["yearly_change_participant_count"].get(str(year), 0),
            "classification": (
                "RECONSTRUCTABLE_FULL_SOURCE_COVERAGE" if mapped == len(issue_set)
                else "IDENTITY_PARTIAL"
            ),
            "participant_count_semantics": "distinct participants with a recorded change in year",
        })
    research = sqlite3.connect(f"file:{args.research_store.resolve().as_posix()}?mode=ro", uri=True)
    row = research.execute(
        "SELECT COUNT(DISTINCT normalized_security_code),COUNT(DISTINCT trade_date),"
        "COUNT(DISTINCT participant_id),MIN(trade_date),MAX(trade_date) "
        "FROM ccass_historical_holdings WHERE trade_date LIKE '2026-%'"
    ).fetchone()
    output.append({
        "year": 2026, "issue_count": int(row[0]), "source_date_count": int(row[1]),
        "reconstructable_issue_count": int(row[0]), "identity_mapped_issue_count": int(row[0]),
        "participant_count": int(row[2]), "classification": "RECONSTRUCTABLE_PARTIAL",
        "participant_count_semantics": f"gap package participants; available {row[3]}..{row[4]}",
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader(); writer.writerows(output)
    print(json.dumps({"years": len(output), "date_min": "2007-06-26", "date_max": row[4]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
