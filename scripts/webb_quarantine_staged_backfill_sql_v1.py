"""Set-based SQLite staged backfill with explicit Webb anomaly quarantine."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

BATCHES = (
    ("BATCH_1", "2007-01-01", "2011-01-01"),
    ("BATCH_2", "2011-01-01", "2015-01-01"),
    ("BATCH_3", "2015-01-01", "2019-01-01"),
    ("BATCH_4", "2019-01-01", "2023-01-01"),
    ("BATCH_5", "2023-01-01", "2025-01-01"),
    ("BATCH_6", "2025-01-01", "2026-01-01"),
    ("BATCH_7", "2026-01-01", "2027-01-01"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS canonical_historical_holdings (
 source_issue_id TEXT NOT NULL, source_participant_id TEXT NOT NULL,
 canonical_security_id TEXT NOT NULL, hk_stock_code TEXT,
 holdings_date TEXT NOT NULL, resolved_source_date TEXT NOT NULL,
 canonical_participant_id TEXT NOT NULL, participant_name TEXT,
 share_quantity INTEGER,
 position_status TEXT NOT NULL CHECK(position_status IN ('VALID','VALID_CORRECTED_WITH_LINEAGE','UNKNOWN_SOURCE_ANOMALY')),
 anomaly_ids TEXT NOT NULL, quarantine_valid_from TEXT, quarantine_valid_to TEXT,
 data_quality_status TEXT NOT NULL, source_system TEXT NOT NULL,
 source_record_reference TEXT NOT NULL, reconstruction_method TEXT NOT NULL,
 reconstruction_version TEXT NOT NULL, identity_status TEXT NOT NULL,
 lineage_reference TEXT NOT NULL, source_sha256 TEXT NOT NULL,
 ingested_at TEXT NOT NULL, code_version TEXT NOT NULL, schema_version TEXT NOT NULL,
 PRIMARY KEY(source_issue_id, source_participant_id, holdings_date)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS canonical_date_idx ON canonical_historical_holdings(holdings_date);
"""


def _version() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_lookup(database: sqlite3.Connection, args: argparse.Namespace) -> None:
    database.executescript(
        """
        CREATE TABLE IF NOT EXISTS issue_identity (
          source_issue_id TEXT PRIMARY KEY, canonical_security_id TEXT,
          hk_stock_codes TEXT, mapping_status TEXT
        );
        CREATE TABLE IF NOT EXISTS participant_identity (
          source_participant_id TEXT PRIMARY KEY, canonical_participant_id TEXT,
          participant_name TEXT, identity_status TEXT
        );
        CREATE TABLE IF NOT EXISTS quarantine_windows (
          issueID TEXT NOT NULL, partID TEXT NOT NULL,
          quarantine_valid_from TEXT NOT NULL, quarantine_valid_to TEXT NOT NULL,
          anomaly_ids TEXT NOT NULL,
          PRIMARY KEY(issueID, partID, quarantine_valid_from, quarantine_valid_to)
        );
        CREATE INDEX IF NOT EXISTS quarantine_pair_date_idx
          ON quarantine_windows(issueID, partID, quarantine_valid_from, quarantine_valid_to);
        """
    )
    issues = _csv(args.issue_identity)
    participants = _csv(args.participant_identity)
    windows = _csv(args.quarantine)
    database.executemany(
        "INSERT OR REPLACE INTO issue_identity VALUES (?,?,?,?)",
        [(r["source_issue_id"], r.get("canonical_security_id", ""), r.get("hk_stock_codes", ""), r.get("mapping_status", "UNRESOLVED")) for r in issues],
    )
    database.executemany(
        "INSERT OR REPLACE INTO participant_identity VALUES (?,?,?,?)",
        [(r["source_participant_id"], r.get("canonical_participant_id", ""), r.get("participant_name", ""), r.get("identity_status", "SOURCE_ID_ONLY")) for r in participants],
    )
    database.executemany(
        "INSERT OR REPLACE INTO quarantine_windows VALUES (?,?,?,?,?)",
        [(r["issueID"], r["partID"], r["quarantine_valid_from"], r["quarantine_valid_to"], r.get("origin_anomaly_ids", r.get("anomaly_id", ""))) for r in windows],
    )
    database.commit()


def _insert_select(database: sqlite3.Connection, start: str, end: str, source_hash: str, version: str) -> int:
    now = datetime.now(UTC).isoformat()
    before = database.total_changes
    database.execute(
        """
        INSERT OR IGNORE INTO canonical_historical_holdings
        SELECT h.c2, h.c1,
          COALESCE(NULLIF(i.canonical_security_id,''), 'webb:issue:' || h.c2),
          NULLIF(substr(i.hk_stock_codes, 1, instr(i.hk_stock_codes || ';', ';') - 1), ''),
          h.c4, h.c4,
          COALESCE(NULLIF(p.canonical_participant_id,''), 'ccass:source:' || h.c1),
          COALESCE(p.participant_name,''),
          CASE WHEN h.c3 < 0 OR q.issueID IS NOT NULL THEN NULL ELSE CAST(h.c3 AS INTEGER) END,
          CASE WHEN h.c3 < 0 OR q.issueID IS NOT NULL THEN 'UNKNOWN_SOURCE_ANOMALY' ELSE 'VALID' END,
          COALESCE(q.anomaly_ids, ''), q.quarantine_valid_from, q.quarantine_valid_to,
          CASE WHEN h.c3 < 0 OR q.issueID IS NOT NULL THEN 'SOURCE_ANOMALY' ELSE 'OK' END,
          'webb_ccass',
          'webbsite_full.sqlite:holdings:rowid=' || h.rowid || ';issueID=' || h.c2 || ';partID=' || h.c1 || ';atDate=' || h.c4,
          'SOURCE_ABSOLUTE_EVENT_STATE', 'webb-quarantine-v1',
          COALESCE(NULLIF(i.mapping_status,''), 'UNRESOLVED'),
          'webbsite_full.sqlite:holdings:rowid=' || h.rowid || ';issueID=' || h.c2 || ';partID=' || h.c1 || ';atDate=' || h.c4,
          ?, ?, ?, 'canonical-historical-quarantine-v1'
        FROM source.holdings h
        LEFT JOIN issue_identity i ON i.source_issue_id=h.c2
        LEFT JOIN participant_identity p ON p.source_participant_id=h.c1
        LEFT JOIN quarantine_windows q
          ON q.issueID=h.c2 AND q.partID=h.c1
         AND h.c4 BETWEEN q.quarantine_valid_from AND q.quarantine_valid_to
        WHERE h.c4>=? AND h.c4<? AND CAST(h.c3 AS INTEGER)<>0
        """,
        (source_hash, now, version, start, end),
    )
    database.commit()
    return database.total_changes - before


def _source_counts(database: sqlite3.Connection, start: str, end: str) -> dict[str, int]:
    row = database.execute(
        "SELECT COUNT(*), SUM(CAST(c3 AS INTEGER)>0), SUM(CAST(c3 AS INTEGER)<0), SUM(CAST(c3 AS INTEGER)=0), COUNT(DISTINCT c2), COUNT(DISTINCT c1) FROM source.holdings WHERE c4>=? AND c4<?",
        (start, end),
    ).fetchone()
    return {
        "source_rows": int(row[0] or 0), "valid_source_rows": int(row[1] or 0),
        "raw_negative_rows": int(row[2] or 0), "zero_source_rows": int(row[3] or 0),
        "source_security_count": int(row[4] or 0), "source_participant_count": int(row[5] or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--quarantine", required=True, type=Path)
    parser.add_argument("--issue-identity", required=True, type=Path)
    parser.add_argument("--participant-identity", required=True, type=Path)
    parser.add_argument("--staging-dir", required=True, type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--max-batches", type=int, default=7)
    parser.add_argument("--start-batch", type=int, default=1)
    args = parser.parse_args()
    args.staging_dir.mkdir(parents=True, exist_ok=True)
    version = _version()
    summaries: list[dict[str, object]] = []
    selected = BATCHES[max(0, args.start_batch - 1): max(0, args.start_batch - 1) + max(0, args.max_batches)]
    for batch_id, start, end in selected:
        target = args.staging_dir / f"webb_quarantine_{batch_id.lower()}.sqlite"
        database = sqlite3.connect(target)
        database.executescript(SCHEMA)
        # Python's bundled SQLite does not accept URI query parameters in
        # ATTACH. The source connection is used only in SELECT statements;
        # no source table is ever a write target.
        database.execute("ATTACH DATABASE ? AS source", (str(args.source.resolve()),))
        _load_lookup(database, args)
        manifest_path = args.staging_dir / f"{batch_id}_MANIFEST.json"
        manifest = {"batch_id": batch_id, "date_min": start, "date_max": end, "status": "RUNNING", "retry_count": 0, "source_sha256": args.source_sha256.upper(), "code_version": version, "schema_version": "canonical-historical-quarantine-v1"}
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            counts = _source_counts(database, start, end)
            counts["write_rows"] = _insert_select(database, start, end, args.source_sha256.upper(), version)
            counts["readback_rows"] = int(database.execute("SELECT COUNT(*) FROM canonical_historical_holdings").fetchone()[0])
            counts["valid_position_rows"] = int(database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE position_status='VALID'").fetchone()[0])
            counts["quarantined_position_states"] = int(database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE position_status='UNKNOWN_SOURCE_ANOMALY'").fetchone()[0])
            counts["anomaly_lineage_rows"] = int(database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE position_status='UNKNOWN_SOURCE_ANOMALY' AND anomaly_ids<>''").fetchone()[0])
            counts["lineage_rows"] = int(database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE lineage_reference<>''").fetchone()[0])
            counts["duplicate_count"] = int(database.execute("SELECT COUNT(*) FROM (SELECT source_issue_id,source_participant_id,holdings_date,COUNT(*) n FROM canonical_historical_holdings GROUP BY 1,2,3 HAVING n>1)").fetchone()[0])
            repeat_before = database.total_changes
            repeat_rows = _insert_select(database, start, end, args.source_sha256.upper(), version)
            counts["idempotent_repeat_additional_rows"] = repeat_rows
            counts["unresolved_security_count"] = int(database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE identity_status IN ('AMBIGUOUS','UNRESOLVED')").fetchone()[0])
            counts["source_only_participant_count"] = int(database.execute("SELECT COUNT(*) FROM canonical_historical_holdings WHERE canonical_participant_id LIKE 'ccass:source:%'").fetchone()[0])
            counts["status"] = "COMPLETED"
            counts["pass"] = counts["duplicate_count"] == 0 and counts["idempotent_repeat_additional_rows"] == 0 and counts["readback_rows"] == counts["write_rows"] and counts["anomaly_lineage_rows"] == counts["quarantined_position_states"]
            summary = {"batch_id": batch_id, "date_min": start, "date_max": end, **counts}
            (args.staging_dir / f"{batch_id}_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            summaries.append(summary)
            manifest.update({"status": "COMPLETED", "row_counts": counts, "validation_result": bool(counts["pass"])})
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception as exc:
            manifest.update({"status": "FAILED", "failed_stage": "SET_BASED_INSERT_SELECT", "root_cause": repr(exc), "retry_count": 1})
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raise
        finally:
            database.close()
    overall = {"completed_batches": len(summaries), "batch_summaries": summaries, "source_sha256": args.source_sha256.upper(), "code_version": version, "pass": len(summaries) == len(selected) and all(bool(item["pass"]) for item in summaries)}
    (args.staging_dir / "WEBB_QUARANTINE_STAGED_BACKFILL_SQL_SUMMARY_V1.json").write_text(json.dumps(overall, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(overall, sort_keys=True))
    return 0 if overall["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
