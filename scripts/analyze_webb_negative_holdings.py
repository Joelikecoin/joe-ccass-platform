"""Describe negative Webb absolute holdings without changing source data."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--negative-rows", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    connection = sqlite3.connect(
        f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True
    )
    issue_names = {
        str(row[0]): str(row[1] or "")
        for row in connection.execute("SELECT c1, c2 FROM shortnames")
    }
    participant_names = {
        str(row[0]): str(row[1] or "")
        for row in connection.execute("SELECT c1, c3 FROM participants")
    }
    with args.negative_rows.open(encoding="utf-8", newline="") as handle:
        negative_rows = list(csv.DictReader(handle))

    output_rows: list[dict[str, object]] = []
    classifications: Counter[str] = Counter()
    for negative in negative_rows:
        rowid = int(negative["source_rowid"])
        issue_id = negative["issue_id"]
        part_id = negative["part_id"]
        nearby = list(
            connection.execute(
                "SELECT rowid,c1,c2,c3,c4 FROM holdings "
                "WHERE rowid BETWEEN ? AND ? ORDER BY rowid",
                (max(1, rowid - 1000), rowid + 1000),
            )
        )
        same_pair = [
            row for row in nearby if str(row[1]) == part_id and str(row[2]) == issue_id
        ]
        index = next(index for index, row in enumerate(same_pair) if row[0] == rowid)
        previous = same_pair[index - 1] if index else None
        following = same_pair[index + 1] if index + 1 < len(same_pair) else None
        previous_value = int(previous[3]) if previous else None
        following_value = int(following[3]) if following else None
        if previous_value is not None and previous_value < 0:
            classification = "REPEATED_NEGATIVE_RUN"
        elif following_value is not None and following_value < 0:
            classification = "NEGATIVE_RUN_START"
        elif previous is None:
            classification = "NEGATIVE_FIRST_OBSERVATION"
        elif following is None:
            classification = "NEGATIVE_TERMINAL_OBSERVATION"
        else:
            classification = "ISOLATED_NEGATIVE_BETWEEN_STATES"
        classifications[classification] += 1
        output_rows.append(
            {
                **negative,
                "security_name": issue_names.get(issue_id, ""),
                "participant_name": participant_names.get(part_id, ""),
                "previous_change_date": previous[4] if previous else "",
                "previous_absolute_holding": previous_value if previous else "",
                "next_change_date": following[4] if following else "",
                "next_absolute_holding": following_value if following else "",
                "forensic_classification": classification,
                "safe_automatic_disposition": "NONE",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print(
        {
            "rows": len(output_rows),
            "issues": len({row["issue_id"] for row in output_rows}),
            "participants": len({row["part_id"] for row in output_rows}),
            "classifications": dict(sorted(classifications.items())),
            "automatic_dispositions": 0,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
