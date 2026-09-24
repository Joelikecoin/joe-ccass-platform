"""Build and run a deterministic 30-security/60-case Webb validation sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import date
from pathlib import Path

from app.services.webb_sparse_holdings import compare_with_reference_query, reconstruct_issue_at

TARGET_YEARS = (2007, 2008, 2010, 2011, 2013, 2014, 2016, 2017, 2019, 2020, 2022, 2023, 2024, 2025)


def _stable_issue_order(issue_id: str) -> str:
    return hashlib.sha256(f"webb-validation-v1:{issue_id}".encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    source = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
    stats = [
        (str(issue), str(first), str(last), int(days))
        for issue, first, last, days in source.execute(
            "SELECT c2,MIN(c1),MAX(c1),COUNT(*) FROM dailylog GROUP BY c2"
        )
        if first and last and str(first) <= "2008-12-31" and str(last) >= "2025-01-01"
    ]
    candidates = [row[0] for row in sorted(stats, key=lambda row: _stable_issue_order(row[0]))[:90]]
    if len(candidates) < 30:
        raise RuntimeError("fewer than 30 long-lived issues available")
    args.stage.parent.mkdir(parents=True, exist_ok=True)
    if args.stage.exists():
        args.stage.unlink()
    stage = sqlite3.connect(args.stage)
    stage.execute("CREATE TABLE holdings (c1 TEXT,c2 TEXT,c3 TEXT,c4 TEXT,source_rowid INTEGER)")
    stage.execute("CREATE TABLE dailylog (c1 TEXT,c2 TEXT)")
    placeholders = ",".join("?" for _ in candidates)
    cursor = source.execute(
        f"SELECT c1,c2,c3,c4,rowid FROM holdings WHERE c2 IN ({placeholders})", candidates
    )
    while True:
        rows = cursor.fetchmany(100_000)
        if not rows:
            break
        stage.executemany("INSERT INTO holdings VALUES (?,?,?,?,?)", rows)
        stage.commit()
    cursor = source.execute(
        f"SELECT c1,c2 FROM dailylog WHERE c2 IN ({placeholders})", candidates
    )
    while True:
        rows = cursor.fetchmany(100_000)
        if not rows:
            break
        stage.executemany("INSERT INTO dailylog VALUES (?,?)", rows)
    stage.execute("CREATE INDEX holdings_issue_date_part ON holdings(c2,c4,c1)")
    stage.execute("CREATE INDEX dailylog_issue_date ON dailylog(c2,c1)")
    stage.commit()

    sizes = []
    for issue_id in candidates:
        last = stage.execute("SELECT MAX(c1) FROM dailylog WHERE c2=?", (issue_id,)).fetchone()[0]
        rebuilt = reconstruct_issue_at(stage, issue_id, date.fromisoformat(str(last)))
        sizes.append((int(rebuilt["active_participant_count"]), issue_id))
    sizes.sort()
    selected = sizes[:10] + sizes[len(sizes)//2-5:len(sizes)//2+5] + sizes[-10:]
    strata = {issue: "SMALL" for _, issue in sizes[:10]}
    strata.update({issue: "MEDIUM" for _, issue in sizes[len(sizes)//2-5:len(sizes)//2+5]})
    strata.update({issue: "LARGE" for _, issue in sizes[-10:]})
    selected_issues = [issue for _, issue in selected]
    cases = []
    for index, issue_id in enumerate(selected_issues):
        desired = (TARGET_YEARS[(index * 2) % len(TARGET_YEARS)], TARGET_YEARS[(index * 2 + 1) % len(TARGET_YEARS)])
        available = [str(row[0]) for row in stage.execute(
            "SELECT c1 FROM dailylog WHERE c2=? ORDER BY c1", (issue_id,)
        )]
        for year in desired:
            year_dates = [value for value in available if value.startswith(f"{year:04d}-")]
            chosen = year_dates[len(year_dates)//2] if year_dates else min(
                available, key=lambda value: abs(int(value[:4]) - year)
            )
            comparison = compare_with_reference_query(
                stage, issue_id, date.fromisoformat(chosen)
            )
            comparison.update({
                "requested_date": chosen,
                "resolved_source_date": chosen,
                "participant_size_stratum": strata[issue_id],
            })
            cases.append(comparison)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "issue_id", "requested_date", "resolved_source_date", "participant_size_stratum",
        "engine_rows", "reference_rows", "engine_share_total", "reference_share_total",
        "missing_participant_count", "extra_participant_count", "share_mismatch_count",
        "rows_match", "duplicate_change_keys", "conflicting_change_keys", "negative_value_count",
    ]
    with args.csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: case[field] for field in fields} for case in cases)
    summary = {
        "candidate_security_count": len(candidates),
        "validated_security_count": len(set(case["issue_id"] for case in cases)),
        "validated_case_count": len(cases),
        "reference_row_mismatch_count": sum(case["engine_rows"] != case["reference_rows"] for case in cases),
        "reference_share_mismatch_count": sum(case["engine_share_total"] != case["reference_share_total"] for case in cases),
        "reference_participant_mismatch_count": sum(
            case["missing_participant_count"] + case["extra_participant_count"] + case["share_mismatch_count"]
            for case in cases
        ),
        "duplicate_change_keys": sum(case["duplicate_change_keys"] for case in cases),
        "conflicting_change_keys": sum(case["conflicting_change_keys"] for case in cases),
        "negative_value_count": sum(case["negative_value_count"] for case in cases),
        "years_covered": sorted(set(int(case["resolved_source_date"][:4]) for case in cases)),
        "stratum_counts": {
            name: sum(case["participant_size_stratum"] == name for case in cases)
            for name in ("SMALL", "MEDIUM", "LARGE")
        },
    }
    summary["pass"] = (
        summary["validated_security_count"] >= 30
        and summary["validated_case_count"] >= 60
        and summary["reference_row_mismatch_count"] == 0
        and summary["reference_share_mismatch_count"] == 0
        and summary["reference_participant_mismatch_count"] == 0
    )
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
