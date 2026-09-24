"""Audit point-in-time issue and participant identity coverage."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def normalize_code(value: object) -> str | None:
    raw = "" if value is None else str(value).strip()
    return raw.zfill(5) if raw.isdigit() and len(raw) <= 5 else None


def overlaps(left, right) -> bool:
    left_start, left_end = left[2], left[3] or "9999-12-31"
    right_start, right_end = right[2], right[3] or "9999-12-31"
    return left_start < right_end and right_start < left_end


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--issue-csv", required=True, type=Path)
    parser.add_argument("--participant-csv", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--observed-only", action="store_true")
    args = parser.parse_args()
    connection = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
    observed_issues = (
        {str(row[0]) for row in connection.execute("SELECT DISTINCT c2 FROM holdings")}
        if args.observed_only else None
    )
    observed_participants = (
        {str(row[0]) for row in connection.execute("SELECT DISTINCT c1 FROM holdings")}
        if args.observed_only else None
    )
    issue_rows: dict[str, list[tuple]] = defaultdict(list)
    for issue, name, valid_from, valid_to, code in connection.execute(
        "SELECT c1,c2,c3,c4,c6 FROM shortnames ORDER BY CAST(c1 AS INTEGER),c3,c4,c6"
    ):
        issue_rows[str(issue)].append((str(issue), str(name), str(valid_from), valid_to, normalize_code(code), code))
    issue_output = []
    for issue_id, rows in issue_rows.items():
        if observed_issues is not None and issue_id not in observed_issues:
            continue
        valid = [row for row in rows if row[4]]
        ambiguous = any(
            left[4] != right[4] and overlaps(left, right)
            for index, left in enumerate(valid) for right in valid[index + 1:]
        )
        codes = sorted({row[4] for row in valid})
        if not valid:
            status = "UNRESOLVED"
        elif ambiguous:
            status = "AMBIGUOUS"
        elif len(codes) == 1:
            status = "EXACT"
        else:
            status = "DATE_BOUNDED"
        issue_output.append({
            "source_system": "webb_ccass", "source_issue_id": issue_id,
            "canonical_security_id": f"webb:issue:{issue_id}",
            "hk_stock_codes": ";".join(codes), "security_name": rows[-1][1],
            "valid_from": min(row[2] for row in rows),
            "valid_to": max((str(row[3]) for row in rows if row[3]), default=""),
            "mapping_status": status,
            "mapping_evidence": "webbsite_full.sqlite/shortnames",
            "mapping_row_count": len(rows),
        })
    args.issue_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.issue_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(issue_output[0]))
        writer.writeheader(); writer.writerows(issue_output)

    participants = [row for row in connection.execute(
        "SELECT c1,c2,c3,c4,c5 FROM participants ORDER BY CAST(c1 AS INTEGER)"
    ) if observed_participants is None or str(row[0]) in observed_participants]
    ccass_to_parts: dict[str, set[str]] = defaultdict(set)
    for part_id, ccass_id, *_ in participants:
        if ccass_id:
            ccass_to_parts[str(ccass_id)].add(str(part_id))
    participant_output = []
    for part_id, ccass_id, name, active_from, inactive_from in participants:
        part_id, ccass_id = str(part_id), str(ccass_id) if ccass_id else ""
        if not ccass_id:
            status, canonical = "SOURCE_ID_ONLY", f"webb:part:{part_id}"
        elif len(ccass_to_parts[ccass_id]) > 1:
            status, canonical = "AMBIGUOUS", f"webb:part:{part_id}"
        else:
            status, canonical = "CANONICAL_MAPPED", f"ccass:{ccass_id}"
        participant_output.append({
            "source_system": "webb_ccass", "source_participant_id": part_id,
            "source_ccass_id": ccass_id, "canonical_participant_id": canonical,
            "participant_name": name, "valid_from": active_from or "",
            "valid_to": inactive_from or "", "identity_status": status,
            "mapping_evidence": "webbsite_full.sqlite/participants",
        })
    with args.participant_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(participant_output[0]))
        writer.writeheader(); writer.writerows(participant_output)
    summary = {
        "total_issues": len(issue_output),
        "exact_mapped_issues": sum(row["mapping_status"] == "EXACT" for row in issue_output),
        "date_bounded_mapped_issues": sum(row["mapping_status"] == "DATE_BOUNDED" for row in issue_output),
        "ambiguous_issues": sum(row["mapping_status"] == "AMBIGUOUS" for row in issue_output),
        "unresolved_issues": sum(row["mapping_status"] == "UNRESOLVED" for row in issue_output),
        "total_participants": len(participant_output),
        "canonical_participant_mapped": sum(row["identity_status"] == "CANONICAL_MAPPED" for row in participant_output),
        "source_id_only_participants": sum(row["identity_status"] == "SOURCE_ID_ONLY" for row in participant_output),
        "ambiguous_participants": sum(row["identity_status"] == "AMBIGUOUS" for row in participant_output),
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
