"""Write/readback an isolated canonical acceptance sample from reconstructed Webb data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

from app.services.webb_sparse_holdings import reconstruct_issue_at

SCHEMA = """
CREATE TABLE IF NOT EXISTS canonical_historical_holdings (
 canonical_security_id TEXT NOT NULL, source_issue_id TEXT NOT NULL,
 hk_stock_code TEXT, holdings_date TEXT NOT NULL, resolved_source_date TEXT NOT NULL,
 canonical_participant_id TEXT NOT NULL, source_participant_id TEXT NOT NULL,
 participant_name TEXT, share_quantity INTEGER NOT NULL,
 source_system TEXT NOT NULL, source_record_reference TEXT NOT NULL,
 reconstruction_method TEXT NOT NULL, reconstruction_version TEXT NOT NULL,
 identity_status TEXT NOT NULL, lineage_reference TEXT NOT NULL,
 ingested_at TEXT NOT NULL, code_version TEXT NOT NULL, schema_version TEXT NOT NULL,
 PRIMARY KEY (canonical_security_id, resolved_source_date, canonical_participant_id)
)
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--issue-identity", required=True, type=Path)
    parser.add_argument("--participant-identity", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--code-version", required=True)
    args = parser.parse_args()
    with args.cases.open(encoding="utf-8") as handle:
        validation = list(csv.DictReader(handle))
    chosen_issues = list(dict.fromkeys(row["issue_id"] for row in validation))[:10]
    chosen = [row for row in validation if row["issue_id"] in chosen_issues]
    with args.issue_identity.open(encoding="utf-8") as handle:
        issues = {row["source_issue_id"]: row for row in csv.DictReader(handle)}
    with args.participant_identity.open(encoding="utf-8") as handle:
        participants = {row["source_participant_id"]: row for row in csv.DictReader(handle)}
    source = sqlite3.connect(f"file:{args.source.resolve().as_posix()}?mode=ro", uri=True)
    args.staging.parent.mkdir(parents=True, exist_ok=True)
    staging = sqlite3.connect(args.staging)
    staging.execute(SCHEMA)
    before = staging.execute("SELECT COUNT(*) FROM canonical_historical_holdings").fetchone()[0]
    raw_rows = canonical_rows = unresolved_security = source_only = 0
    expected: dict[tuple[str, str], dict[str, tuple[int, str]]] = {}
    all_values: list[tuple[object, ...]] = []
    now = datetime.now(UTC).isoformat()
    for case in chosen:
        issue_id, day = case["issue_id"], case["resolved_source_date"]
        rebuilt = reconstruct_issue_at(source, issue_id, date.fromisoformat(day))
        raw_rows += int(rebuilt["source_changes_seen"])
        issue = issues[issue_id]
        codes = [value for value in issue["hk_stock_codes"].split(";") if value]
        hk_code = codes[0] if len(codes) == 1 else None
        identity_status = issue["mapping_status"]
        unresolved_security += identity_status in {"AMBIGUOUS", "UNRESOLVED"}
        security_id = issue["canonical_security_id"]
        expected_key = (security_id, day)
        expected[expected_key] = {}
        for row in rebuilt["participant_rows"]:
            part_id = str(row["source_part_id"])
            participant = participants[part_id]
            source_only += participant["identity_status"] != "CANONICAL_MAPPED"
            canonical_participant = participant["canonical_participant_id"]
            reference = (
                f"webbsite_full.sqlite:holdings:issueID={issue_id};partID={part_id};"
                f"atDate={row['last_change_date']};rowid={row['source_rowid']}"
            )
            values = (
                security_id, issue_id, hk_code, day, day, canonical_participant,
                part_id, participant["participant_name"], int(row["share_quantity"]),
                "webb_ccass", reference, "LATEST_ABSOLUTE_AT_OR_BEFORE_DATE",
                "webb-position-v1", identity_status, reference, now,
                args.code_version, "canonical-historical-holding-v1",
            )
            staging.execute(
                "INSERT OR IGNORE INTO canonical_historical_holdings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                values,
            )
            all_values.append(values)
            canonical_rows += 1
            expected[expected_key][canonical_participant] = (int(row["share_quantity"]), part_id)
    staging.commit()
    after = staging.execute("SELECT COUNT(*) FROM canonical_historical_holdings").fetchone()[0]
    mismatches = readback_rows = 0
    for (security_id, day), expected_rows in expected.items():
        actual = {
            row[0]: (int(row[1]), row[2]) for row in staging.execute(
                "SELECT canonical_participant_id,share_quantity,source_participant_id "
                "FROM canonical_historical_holdings WHERE canonical_security_id=? AND resolved_source_date=?",
                (security_id, day),
            )
        }
        readback_rows += len(actual)
        mismatches += actual != expected_rows
    repeat_before = staging.execute("SELECT COUNT(*) FROM canonical_historical_holdings").fetchone()[0]
    staging.executemany(
        "INSERT OR IGNORE INTO canonical_historical_holdings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        all_values,
    )
    staging.commit()
    repeat_after = staging.execute("SELECT COUNT(*) FROM canonical_historical_holdings").fetchone()[0]
    duplicates = staging.execute(
        "SELECT COUNT(*) FROM (SELECT canonical_security_id,resolved_source_date,canonical_participant_id,COUNT(*) n "
        "FROM canonical_historical_holdings GROUP BY 1,2,3 HAVING n>1)"
    ).fetchone()[0]
    summary = {
        "validated_security_count": len(chosen_issues), "validated_date_count": len(chosen),
        "source_change_rows_seen": raw_rows, "canonical_rows": canonical_rows,
        "write_rows": after - before, "readback_rows": readback_rows,
        "field_mismatch_groups": mismatches, "duplicate_count": duplicates,
        "unresolved_security_case_count": unresolved_security,
        "source_id_only_participant_rows": source_only,
        "lineage_coverage_rows": staging.execute(
            "SELECT COUNT(*) FROM canonical_historical_holdings WHERE lineage_reference<>''"
        ).fetchone()[0],
        "idempotent_repeat_additional_rows": repeat_after - repeat_before,
    }
    summary["pass"] = (
        len(chosen_issues) >= 10 and len(chosen) >= 20 and mismatches == 0
        and duplicates == 0 and summary["idempotent_repeat_additional_rows"] == 0
        and readback_rows == canonical_rows
    )
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
