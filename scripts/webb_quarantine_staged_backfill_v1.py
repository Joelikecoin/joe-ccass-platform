"""Resumable isolated Webb event-state backfill with quarantine propagation."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

BATCHES = (
    ("BATCH_1", "2007", "2010"),
    ("BATCH_2", "2011", "2014"),
    ("BATCH_3", "2015", "2018"),
    ("BATCH_4", "2019", "2022"),
    ("BATCH_5", "2023", "2024"),
    ("BATCH_6", "2025", "2025"),
    ("BATCH_7", "2026", "2026"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS canonical_historical_holdings (
 source_issue_id TEXT NOT NULL,
 source_participant_id TEXT NOT NULL,
 canonical_security_id TEXT NOT NULL,
 hk_stock_code TEXT,
 holdings_date TEXT NOT NULL,
 resolved_source_date TEXT NOT NULL,
 canonical_participant_id TEXT NOT NULL,
 participant_name TEXT,
 share_quantity INTEGER,
 position_status TEXT NOT NULL CHECK(position_status IN ('VALID','VALID_CORRECTED_WITH_LINEAGE','UNKNOWN_SOURCE_ANOMALY')),
 anomaly_ids TEXT NOT NULL,
 quarantine_valid_from TEXT,
 quarantine_valid_to TEXT,
 data_quality_status TEXT NOT NULL,
 source_system TEXT NOT NULL,
 source_record_reference TEXT NOT NULL,
 reconstruction_method TEXT NOT NULL,
 reconstruction_version TEXT NOT NULL,
 identity_status TEXT NOT NULL,
 lineage_reference TEXT NOT NULL,
 source_sha256 TEXT NOT NULL,
 ingested_at TEXT NOT NULL,
 code_version TEXT NOT NULL,
 schema_version TEXT NOT NULL,
 PRIMARY KEY(source_issue_id, source_participant_id, holdings_date)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS canonical_date_idx ON canonical_historical_holdings(holdings_date);
"""


def _version() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--quarantine", required=True, type=Path)
    parser.add_argument("--issue-identity", required=True, type=Path)
    parser.add_argument("--participant-identity", required=True, type=Path)
    parser.add_argument("--staging-dir", required=True, type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--max-batches", type=int, default=7)
    args = parser.parse_args()
    args.staging_dir.mkdir(parents=True, exist_ok=True)
    version = _version()
    issues = {row["source_issue_id"]: row for row in _read_csv(args.issue_identity)}
    participants = {row["source_participant_id"]: row for row in _read_csv(args.participant_identity)}
    quarantine_rows = _read_csv(args.quarantine)
    quarantine: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in quarantine_rows:
        quarantine[(row["issueID"], row["partID"])].append(row)
    source = sqlite3.connect(f"file:{args.source.resolve().as_posix()}?mode=ro", uri=True)
    summaries: list[dict[str, object]] = []
    all_batches = BATCHES[: max(0, min(args.max_batches, len(BATCHES)))]
    for batch_id, year_min, year_max in all_batches:
        target = args.staging_dir / f"webb_quarantine_{batch_id.lower()}.sqlite"
        database = sqlite3.connect(target)
        database.executescript(SCHEMA)
        manifest = {
            "batch_id": batch_id, "date_min": f"{year_min}-01-01", "date_max": f"{year_max}-12-31",
            "status": "RUNNING", "source_sha256": args.source_sha256.upper(), "code_version": version,
            "schema_version": "webb-quarantine-canonical-v1", "retry_count": 0,
        }
        (args.staging_dir / f"{batch_id}_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        counts = defaultdict(int)
        chunk: list[tuple[object, ...]] = []
        ingested_at = datetime.now(UTC).isoformat()

        def flush(values: list[tuple[object, ...]]) -> None:
            if not values:
                return
            before = database.total_changes
            database.executemany(
                "INSERT OR IGNORE INTO canonical_historical_holdings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                values,
            )
            database.commit()
            counts["write_rows"] += database.total_changes - before
            before_repeat = database.total_changes
            database.executemany(
                "INSERT OR IGNORE INTO canonical_historical_holdings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                values,
            )
            database.commit()
            counts["idempotent_repeat_additional_rows"] += database.total_changes - before_repeat

        try:
            for rowid, part_raw, issue_raw, holding_raw, date_raw in source.execute(
                "SELECT rowid,c1,c2,c3,c4 FROM holdings ORDER BY rowid"
            ):
                source_date = str(date_raw)
                year = source_date[:4]
                if not (year_min <= year <= year_max):
                    continue
                counts["source_rows"] += 1
                issue = str(issue_raw)
                part = str(part_raw)
                holding = int(holding_raw)
                if holding == 0:
                    counts["zero_source_rows"] += 1
                    continue
                identity = issues.get(issue, {})
                participant = participants.get(part, {})
                canonical_security = identity.get("canonical_security_id") or f"webb:issue:{issue}"
                canonical_participant = participant.get("canonical_participant_id") or f"ccass:source:{part}"
                pair_windows = quarantine.get((issue, part), [])
                anomaly_matches = [
                    item for item in pair_windows
                    if str(item["quarantine_valid_from"]) <= date_raw <= str(item["quarantine_valid_to"])
                ]
                if holding < 0:
                    anomaly_matches = [
                        item for item in pair_windows if item["negative_atDate"] == source_date
                    ]
                    counts["raw_negative_rows"] += 1
                unknown = bool(anomaly_matches) or holding < 0
                if unknown:
                    counts["quarantined_states"] += 1
                    share = None
                    status = "UNKNOWN_SOURCE_ANOMALY"
                    anomaly_ids = ";".join(sorted({str(item["anomaly_id"]) for item in anomaly_matches}))
                    q_from = min((str(item["quarantine_valid_from"]) for item in anomaly_matches), default=source_date)
                    q_to = max((str(item["quarantine_valid_to"]) for item in anomaly_matches), default=source_date)
                    quality = "SOURCE_ANOMALY"
                else:
                    counts["valid_states"] += 1
                    share = holding
                    status = "VALID"
                    anomaly_ids, q_from, q_to, quality = "", None, None, "OK"
                if identity.get("mapping_status") in {"AMBIGUOUS", "UNRESOLVED"}:
                    counts["unresolved_security_count"] += 1
                if participant.get("identity_status") != "CANONICAL_MAPPED":
                    counts["source_only_participant_count"] += 1
                reference = f"webbsite_full.sqlite:holdings:rowid={rowid};issueID={issue};partID={part};atDate={source_date}"
                chunk.append((
                    issue, part, canonical_security, identity.get("hk_stock_codes", "").split(";")[0] or None,
                    source_date, source_date, canonical_participant, participant.get("participant_name", ""),
                    share, status, anomaly_ids, q_from, q_to, quality, "webb_ccass",
                    reference, "SOURCE_ABSOLUTE_EVENT_STATE", "webb-quarantine-v1",
                    identity.get("mapping_status", "UNRESOLVED"), reference, args.source_sha256.upper(),
                    ingested_at, version, "canonical-historical-quarantine-v1",
                ))
                if len(chunk) >= 5000:
                    flush(chunk)
                    chunk.clear()
            flush(chunk)
            counts["readback_rows"] = database.execute("SELECT COUNT(*) FROM canonical_historical_holdings").fetchone()[0]
            counts["duplicate_count"] = database.execute(
                "SELECT COUNT(*) FROM (SELECT source_issue_id,source_participant_id,holdings_date,COUNT(*) n FROM canonical_historical_holdings GROUP BY 1,2,3 HAVING n>1)"
            ).fetchone()[0]
            counts["lineage_rows"] = database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE lineage_reference<>''").fetchone()[0]
            counts["anomaly_lineage_rows"] = database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE position_status='UNKNOWN_SOURCE_ANOMALY' AND anomaly_ids<>''").fetchone()[0]
            counts["status"] = "COMPLETED"
            counts["pass"] = (
                counts["duplicate_count"] == 0
                and counts["idempotent_repeat_additional_rows"] == 0
                and counts["readback_rows"] == counts["write_rows"]
                and counts["anomaly_lineage_rows"] == counts["quarantined_states"]
            )
            summary = {"batch_id": batch_id, "date_min": f"{year_min}-01-01", "date_max": f"{year_max}-12-31", **dict(counts)}
            (args.staging_dir / f"{batch_id}_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            summaries.append(summary)
            manifest.update({"status": "COMPLETED", "row_counts": dict(counts), "validation_result": bool(counts["pass"])})
            (args.staging_dir / f"{batch_id}_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception as exc:
            manifest.update({"status": "FAILED", "failed_stage": "SOURCE_STREAM_AND_WRITE", "root_cause": repr(exc), "retry_count": 1})
            (args.staging_dir / f"{batch_id}_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raise
        finally:
            database.close()
    overall = {
        "completed_batches": len(summaries),
        "batch_summaries": summaries,
        "source_sha256": args.source_sha256.upper(),
        "code_version": version,
        "pass": len(summaries) == len(all_batches) and all(bool(item["pass"]) for item in summaries),
    }
    (args.staging_dir / "WEBB_QUARANTINE_STAGED_BACKFILL_SUMMARY_V1.json").write_text(json.dumps(overall, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(overall, sort_keys=True))
    return 0 if overall["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
