"""Read-only reconciliation of candidate Webb historical SQLite sources.

The script never attaches a writable database and never mutates a candidate.
It produces one machine-readable report containing file identity, schema/date
coverage, yearly row counts, directory counts, and exact reconciliation against
the frozen 92-row negative ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


YEARS = tuple(range(2007, 2027))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_ledger(path: Path) -> dict[tuple[str, str, str], int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        (str(row["issueID"]), str(row["partID"]), str(row["atDate"])): int(row["holding_value"])
        for row in rows
    }


def read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def inspect(
    path: Path,
    expected_hash: str,
    ledger: dict[tuple[str, str, str], int],
    preverified_hash: str | None = None,
) -> dict:
    if not path.is_file():
        return {
            "path": str(path),
            "present": False,
            "expected_sha256": expected_hash.upper(),
            "status": "MISSING",
        }

    actual_hash = preverified_hash.upper() if preverified_hash else sha256(path)
    with read_only(path) as connection:
        tables = [str(row[0]) for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )]
        integrity = str(connection.execute("PRAGMA integrity_check(1)").fetchone()[0])
        year_expressions = ",".join(
            f"SUM(CASE WHEN substr(c4,1,4)='{year}' THEN 1 ELSE 0 END)"
            for year in YEARS
        )
        aggregate = connection.execute(
            "SELECT COUNT(*),MIN(c4),MAX(c4),"
            + year_expressions
            + ",GROUP_CONCAT(CASE WHEN CAST(c3 AS INTEGER)<0 "
            "THEN c2||char(30)||c1||char(30)||c4||char(30)||CAST(c3 AS INTEGER) END,char(31)) "
            "FROM holdings"
        ).fetchone()
        total_rows, date_min, date_max = aggregate[:3]
        yearly = dict(zip(YEARS, (int(value or 0) for value in aggregate[3:3 + len(YEARS)])))
        issue_count = int(connection.execute("SELECT COUNT(DISTINCT c1) FROM shortnames").fetchone()[0])
        participant_count = int(connection.execute("SELECT COUNT(DISTINCT c1) FROM participants").fetchone()[0])
        negative_payload = aggregate[3 + len(YEARS)] or ""
        negatives = {}
        for record in negative_payload.split(chr(31)) if negative_payload else ():
            issue, participant, day, value = record.split(chr(30))
            negatives[(issue, participant, day)] = int(value)

    matches = sum(negatives.get(key) == value for key, value in ledger.items())
    missing = sum(key not in negatives for key in ledger)
    mismatches = sum(key in negatives and negatives[key] != value for key, value in ledger.items())
    extra = sum(key not in ledger for key in negatives)
    return {
        "path": str(path.resolve()),
        "present": True,
        "file_size": path.stat().st_size,
        "expected_sha256": expected_hash.upper(),
        "sha256": actual_hash,
        "hash_match": actual_hash == expected_hash.upper(),
        "sqlite_integrity_status": integrity,
        "tables": tables,
        "total_source_rows": int(total_rows),
        "date_min": str(date_min),
        "date_max": str(date_max),
        "yearly_row_counts": {str(year): yearly.get(year, 0) for year in YEARS},
        "issue_directory_count": issue_count,
        "participant_directory_count": participant_count,
        "negative_row_count": len(negatives),
        "negative_ledger_match_count": matches,
        "negative_ledger_missing_count": missing,
        "negative_ledger_value_mismatch_count": mismatches,
        "negative_rows_not_in_ledger": extra,
        "status": "PASS" if integrity == "ok" and actual_hash == expected_hash.upper() else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-a", type=Path, required=True)
    parser.add_argument("--candidate-a-sha256", required=True)
    parser.add_argument(
        "--candidate-a-preverified-sha256",
        help="SHA-256 already computed in this execution; avoids rereading a large cloud file",
    )
    parser.add_argument("--candidate-b", type=Path)
    parser.add_argument("--candidate-b-sha256", default="")
    parser.add_argument("--candidate-b-preverified-sha256")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    ledger = read_ledger(args.ledger)
    candidate_a = inspect(
        args.candidate_a,
        args.candidate_a_sha256,
        ledger,
        args.candidate_a_preverified_sha256,
    )
    candidate_b = (
        inspect(
            args.candidate_b,
            args.candidate_b_sha256,
            ledger,
            args.candidate_b_preverified_sha256,
        )
        if args.candidate_b
        else {"present": False, "status": "MISSING", "expected_sha256": args.candidate_b_sha256.upper()}
    )
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "READ_ONLY",
        "ledger_row_count": len(ledger),
        "candidate_a": candidate_a,
        "candidate_b": candidate_b,
        "source_version_diff": {
            "pass": bool(candidate_a.get("present") and candidate_b.get("present")),
            "status": "BLOCKED_CANDIDATE_MISSING" if not candidate_b.get("present") else "SUMMARY_AVAILABLE",
        },
        "raw_source_mutated": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if candidate_a.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
