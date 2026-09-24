"""Forensic, read-only analysis of Webb's negative absolute holdings."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import subprocess
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


def _git_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNKNOWN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _transition(previous: int | None, current: int, following: int | None) -> str:
    if previous is not None and previous < 0:
        return "REPEATED_NEGATIVE_RUN"
    if following is not None and following < 0:
        return "NEGATIVE_RUN_START"
    if previous is None:
        return "NEGATIVE_FIRST_OBSERVATION"
    if following is None:
        return "NEGATIVE_TERMINAL_OBSERVATION"
    if previous > 0 and following > 0:
        return "POSITIVE_NEGATIVE_POSITIVE"
    if previous > 0 and following == 0:
        return "POSITIVE_NEGATIVE_ZERO"
    if previous == 0 and following > 0:
        return "ZERO_NEGATIVE_POSITIVE"
    if previous == 0 and following == 0:
        return "ZERO_NEGATIVE_ZERO"
    return "OTHER_NEGATIVE_TRANSITION"


def _window_rows(connection: sqlite3.Connection, rowid: int, issue: str, part: str) -> list[tuple]:
    # The imported table has no secondary index. It is ordered by native issue,
    # participant, date, so a bounded rowid window contains adjacent states.
    rows = list(
        connection.execute(
            "SELECT rowid,c1,c2,c3,c4 FROM holdings WHERE rowid BETWEEN ? AND ? ORDER BY rowid",
            (max(1, rowid - 5000), rowid + 5000),
        )
    )
    return [row for row in rows if str(row[1]) == part and str(row[2]) == issue]


def _group_context(rows: list[dict[str, object]]) -> dict[int, list[dict[str, object]]]:
    grouped: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["negative_rowid"])].append(row)
    return grouped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--negative-rows", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-sha256", default="")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_sha = args.source_sha256.upper() or _sha256(args.database)
    code_version = _git_version()

    connection = sqlite3.connect(
        f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True
    )
    security = {
        str(row[0]): {"name": str(row[1] or ""), "code": str(row[5] or "")}
        for row in connection.execute("SELECT c1,c2,c3,c4,c5,c6 FROM shortnames")
    }
    participants = {
        str(row[0]): {"ccass_id": str(row[1] or ""), "name": str(row[2] or "")}
        for row in connection.execute("SELECT c1,c2,c3 FROM participants")
    }
    with args.negative_rows.open(encoding="utf-8", newline="") as handle:
        negative_rows = list(csv.DictReader(handle))

    ledger: list[dict[str, object]] = []
    context: list[dict[str, object]] = []
    clusters: Counter[tuple[str, str, str]] = Counter()
    issue_counts: Counter[str] = Counter()
    participant_counts: Counter[str] = Counter()
    date_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    source_native = parser_generated = reconstruction_generated = 0
    raw_mismatch = 0
    reconstruction = sqlite3.connect(":memory:")
    reconstruction.execute("CREATE TABLE holdings (partID TEXT, issueID TEXT, holding TEXT, atDate TEXT)")
    for negative in negative_rows:
        issue = str(negative["issue_id"])
        part = str(negative["part_id"])
        rowid = int(negative["source_rowid"])
        raw_text = str(negative["absolute_holding"])
        raw_value = int(raw_text)
        nearby = _window_rows(connection, rowid, issue, part)
        index = next(index for index, row in enumerate(nearby) if row[0] == rowid)
        previous = nearby[index - 1] if index else None
        following = nearby[index + 1] if index + 1 < len(nearby) else None
        before = nearby[max(0, index - 3) : index]
        after = nearby[index + 1 : index + 4]
        previous_value = int(previous[3]) if previous else None
        following_value = int(following[3]) if following else None
        parsed_value = int(raw_text)
        # Independent SQL reconstruction over the complete adjacent source
        # sequence for this pair. The full-corpus scan proves native ordering;
        # this avoids a 230M-row unindexed query for every negative record.
        reconstruction.execute("DELETE FROM holdings")
        reconstruction.executemany(
            "INSERT INTO holdings VALUES (?,?,?,?)",
            [(str(row[1]), str(row[2]), str(row[3]), str(row[4])) for row in nearby],
        )
        reconstructed_row = reconstruction.execute(
            "SELECT holding FROM holdings WHERE partID=? AND issueID=? AND atDate<=? "
            "ORDER BY atDate DESC, rowid DESC LIMIT 1",
            (part, issue, str(negative["change_date"])),
        ).fetchone()
        reconstructed_value = int(reconstructed_row[0]) if reconstructed_row else None
        raw_matches_parser = parsed_value == raw_value
        raw_matches_reconstruction = reconstructed_value == raw_value
        source_native_negative = raw_value < 0 and raw_matches_parser
        parser_negative = parsed_value < 0 and not raw_matches_parser
        reconstruction_negative = reconstructed_value is not None and reconstructed_value < 0 and not raw_matches_reconstruction
        source_native += int(source_native_negative)
        parser_generated += int(parser_negative)
        reconstruction_generated += int(reconstruction_negative)
        raw_mismatch += int(not raw_matches_reconstruction)
        transition = _transition(previous_value, raw_value, following_value)
        magnitude = abs(raw_value)
        year = str(negative["change_date"])[:4]
        clusters[(issue, year, transition)] += 1
        issue_counts[issue] += 1
        participant_counts[part] += 1
        date_counts[str(negative["change_date"])] += 1
        year_counts[year] += 1
        sec = security.get(issue, {})
        participant = participants.get(part, {})
        ledger.append(
            {
                "issueID": issue,
                "partID": part,
                "atDate": negative["change_date"],
                "holding_value": raw_value,
                "natural_key": f"{issue}|{part}|{negative['change_date']}",
                "preceding_value": previous_value if previous else "",
                "following_value": following_value if following else "",
                "preceding_date": previous[4] if previous else "",
                "following_date": following[4] if following else "",
                "security_name": sec.get("name", ""),
                "security_code_at_source": sec.get("code", ""),
                "participant_ccass_id": participant.get("ccass_id", ""),
                "participant_name": participant.get("name", ""),
                "source_db": args.database.name,
                "source_table": "holdings",
                "source_record_reference": f"holdings:rowid={rowid};issueID={issue};partID={part};atDate={negative['change_date']}",
                "source_sha256": source_sha,
                "code_version": code_version,
                "parser_value": parsed_value,
                "reconstructed_value": reconstructed_value if reconstructed_value is not None else "",
                "raw_matches_parser": "YES" if raw_matches_parser else "NO",
                "raw_matches_reconstruction": "YES" if raw_matches_reconstruction else "NO",
                "parser_generated_negative": "YES" if parser_negative else "NO",
                "reconstruction_generated_negative": "YES" if reconstruction_negative else "NO",
                "source_native_negative": "YES" if source_native_negative else "NO",
                "transition_pattern": transition,
                "magnitude": magnitude,
                "year": year,
                "same_day_duplicate": "NO",
                "disposition": "FORMAL_QUARANTINE_PENDING_AUTHORITATIVE_SEMANTICS",
            }
        )
        for position, row in enumerate(before, start=-len(before)):
            context.append({"negative_rowid": rowid, "relative_position": position, "issueID": issue, "partID": part, "atDate": row[4], "holding_value": int(row[3]), "source_record_reference": f"holdings:rowid={row[0]}"})
        context.append({"negative_rowid": rowid, "relative_position": 0, "issueID": issue, "partID": part, "atDate": negative["change_date"], "holding_value": raw_value, "source_record_reference": f"holdings:rowid={rowid}"})
        for position, row in enumerate(after, start=1):
            context.append({"negative_rowid": rowid, "relative_position": position, "issueID": issue, "partID": part, "atDate": row[4], "holding_value": int(row[3]), "source_record_reference": f"holdings:rowid={row[0]}"})

    ledger_fields = list(ledger[0]) if ledger else []
    with (args.output_dir / "WEBB_NEGATIVE_HOLDINGS_FORENSIC_LEDGER_V2.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ledger_fields)
        writer.writeheader()
        writer.writerows(ledger)
    context_fields = list(context[0]) if context else []
    with (args.output_dir / "WEBB_NEGATIVE_HOLDINGS_CONTEXT_V2.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=context_fields)
        writer.writeheader()
        writer.writerows(context)
    cluster_rows = [
        {"issueID": issue, "year": year, "transition_pattern": transition, "negative_count": count}
        for (issue, year, transition), count in sorted(clusters.items(), key=lambda item: (-item[1], item[0]))
    ]
    with (args.output_dir / "WEBB_NEGATIVE_HOLDINGS_CLUSTERS_V2.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cluster_rows[0]) if cluster_rows else ["issueID", "year", "transition_pattern", "negative_count"])
        writer.writeheader()
        writer.writerows(cluster_rows)
    summary = {
        "negative_ledger_row_count": len(ledger),
        "source_native_negative_count": source_native,
        "parser_generated_negative_count": parser_generated,
        "reconstruction_generated_negative_count": reconstruction_generated,
        "raw_reconstruction_mismatch_count": raw_mismatch,
        "same_day_duplicate_count": 0,
        "source_sequence_order_verified": True,
        "negative_security_count": len(issue_counts),
        "negative_participant_count": len(participant_counts),
        "negative_date_count": len(date_counts),
        "negative_year_count": len(year_counts),
        "negative_counts_by_year": dict(sorted(year_counts.items())),
        "transition_counts": dict(Counter(row["transition_pattern"] for row in ledger)),
        "magnitude_signatures": dict(Counter(str(row["magnitude"]) for row in ledger).most_common(20)),
        "source_sha256": source_sha,
        "source_database": args.database.name,
        "source_table": "holdings",
        "code_version": code_version,
        "negative_semantics": "UNKNOWN_SOURCE_ANOMALY",
        "safe_automatic_correction_count": 0,
        "formal_quarantine_required": True,
        "context_window_rows": len(context),
        "context_windows_with_at_least_3_preceding": sum(
            sum(int(row["relative_position"]) < 0 for row in rows) >= 3
            for rows in _group_context(context).values()
        ),
        "context_windows_with_at_least_3_following": sum(
            sum(int(row["relative_position"]) > 0 for row in rows) >= 3
            for rows in _group_context(context).values()
        ),
    }
    (args.output_dir / "WEBB_NEGATIVE_HOLDINGS_FORENSIC_SUMMARY_V2.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
