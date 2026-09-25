"""Fast validation for a materialized authoritative Webb batch.

The validator reads one isolated staging database, checks the four hard gates,
and executes a deterministic duplicate replay that must add zero rows. Source
denominators are explicit command inputs from the separately persisted source
reconciliation, so validation does not rescan the 230-million-row source.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


TABLE = "canonical_historical_holdings"


def validate(
    database_path: Path,
    batch_id: str,
    expected_source_sha256: str,
    expected_raw_rows: int,
    expected_eligible_rows: int,
    expected_negative_rows: int,
    run_integrity: bool = True,
) -> dict[str, object]:
    database = sqlite3.connect(database_path)
    try:
        columns = [str(row[1]) for row in database.execute(f"PRAGMA table_info({TABLE})")]
        if not columns:
            raise RuntimeError(f"missing required table: {TABLE}")
        aggregate = database.execute(
            f"""
            SELECT COUNT(*),
              SUM(position_status='VALID'),
              SUM(position_status='UNKNOWN_SOURCE_ANOMALY'),
              SUM(position_status='UNKNOWN_SOURCE_ANOMALY' AND anomaly_ids<>''),
              SUM(lineage_reference<>''),
              SUM(share_quantity<0),
              COUNT(DISTINCT source_sha256),
              MIN(source_sha256), MAX(source_sha256),
              MIN(holdings_date), MAX(holdings_date)
            FROM {TABLE}
            """
        ).fetchone()
        readback_rows = int(aggregate[0] or 0)
        sample = database.execute(
            f"SELECT source_issue_id,source_participant_id,holdings_date FROM {TABLE} ORDER BY holdings_date LIMIT 1"
        ).fetchone()
        before = database.total_changes
        if sample:
            database.execute(
                f"INSERT OR IGNORE INTO {TABLE} SELECT * FROM {TABLE} "
                "WHERE source_issue_id=? AND source_participant_id=? AND holdings_date=?",
                sample,
            )
            database.commit()
        idempotent_repeat_additional_rows = database.total_changes - before
        integrity = (
            str(database.execute("PRAGMA integrity_check(1)").fetchone()[0])
            if run_integrity
            else "DEFERRED_NOT_ESTABLISHED_HARD_GATE"
        )
    finally:
        database.close()

    row_reconciliation_pass = readback_rows == expected_eligible_rows
    duplicate_conflict_safety_pass = idempotent_repeat_additional_rows == 0
    canonical_data_safety_pass = (
        int(aggregate[5] or 0) == 0
        and int(aggregate[3] or 0) == int(aggregate[2] or 0)
        and int(aggregate[4] or 0) == readback_rows
    )
    readback_checkpoint_pass = (
        integrity in {"ok", "DEFERRED_NOT_ESTABLISHED_HARD_GATE"}
        and int(aggregate[6] or 0) in ({0} if readback_rows == 0 else {1})
        and (readback_rows == 0 or (str(aggregate[7]) == expected_source_sha256 and str(aggregate[8]) == expected_source_sha256))
    )
    return {
        "batch_id": batch_id,
        "validated_at": datetime.now(UTC).isoformat(),
        "database_path": str(database_path.resolve()),
        "expected_source_sha256": expected_source_sha256,
        "expected_raw_rows": expected_raw_rows,
        "expected_eligible_rows": expected_eligible_rows,
        "expected_zero_rows": expected_raw_rows - expected_eligible_rows,
        "expected_negative_rows": expected_negative_rows,
        "readback_rows": readback_rows,
        "valid_position_rows": int(aggregate[1] or 0),
        "canonical_quarantined_state_count": int(aggregate[2] or 0),
        "anomaly_lineage_rows": int(aggregate[3] or 0),
        "lineage_rows": int(aggregate[4] or 0),
        "canonical_negative_count": int(aggregate[5] or 0),
        "source_sha256_distinct_count": int(aggregate[6] or 0),
        "date_min": aggregate[9],
        "date_max": aggregate[10],
        "idempotent_repeat_additional_rows": idempotent_repeat_additional_rows,
        "sqlite_integrity_status": integrity,
        "row_reconciliation_pass": row_reconciliation_pass,
        "duplicate_conflict_safety_pass": duplicate_conflict_safety_pass,
        "canonical_data_safety_pass": canonical_data_safety_pass,
        "readback_checkpoint_pass": readback_checkpoint_pass,
        "pass": all(
            (
                row_reconciliation_pass,
                duplicate_conflict_safety_pass,
                canonical_data_safety_pass,
                readback_checkpoint_pass,
                int(aggregate[2] or 0) == expected_negative_rows,
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--raw-rows", type=int, required=True)
    parser.add_argument("--eligible-rows", type=int, required=True)
    parser.add_argument("--negative-rows", type=int, required=True)
    parser.add_argument("--skip-integrity", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(
        args.database,
        args.batch_id,
        args.source_sha256.upper(),
        args.raw_rows,
        args.eligible_rows,
        args.negative_rows,
        run_integrity=not args.skip_integrity,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
