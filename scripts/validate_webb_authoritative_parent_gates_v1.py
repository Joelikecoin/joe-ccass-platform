"""Validate parent gates across selectively rebuilt authoritative Webb batches."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


AUTHORITY = "9CCDE356D068399BFBC931CA6E367E5944AFCF5C16C83D2FF240636995B0BE7C"
BATCH_1_ROWS = 38_525_367
BATCH_1_QUARANTINE = 34
EXPECTED_ELIGIBLE_ROWS = 225_071_295


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def batch_summary(path: Path) -> dict:
    payload = load(path)
    if "batch_summaries" in payload:
        return dict(payload["batch_summaries"][0])
    return payload


def sample_surface(database_path: Path, era: str, day: str) -> dict[str, object]:
    with sqlite3.connect(f"file:{database_path.resolve().as_posix()}?mode=ro", uri=True) as database:
        database.execute("PRAGMA query_only=ON")
        issue = database.execute(
            "SELECT source_issue_id,COUNT(*) FROM canonical_historical_holdings "
            "WHERE holdings_date=? GROUP BY source_issue_id ORDER BY COUNT(*) DESC LIMIT 1",
            (day,),
        ).fetchone()
        if not issue:
            return {"era": era, "date": day, "pass": False, "reason": "NO_ROWS"}
        sample = database.execute(
            "SELECT source_issue_id,source_participant_id,position_status,data_quality_status,"
            "lineage_reference,source_sha256 FROM canonical_historical_holdings "
            "WHERE holdings_date=? AND source_issue_id=? ORDER BY share_quantity DESC LIMIT 1",
            (day, str(issue[0])),
        ).fetchone()
        cross_stock = database.execute(
            "SELECT COUNT(DISTINCT source_issue_id) FROM canonical_historical_holdings "
            "WHERE holdings_date=? AND source_participant_id=?",
            (day, str(sample[1])),
        ).fetchone()[0]
        top_ten = database.execute(
            "SELECT COUNT(*) FROM (SELECT 1 FROM canonical_historical_holdings "
            "WHERE holdings_date=? AND source_issue_id=? AND share_quantity IS NOT NULL "
            "ORDER BY share_quantity DESC LIMIT 10)",
            (day, str(issue[0])),
        ).fetchone()[0]
    passed = bool(
        int(issue[1]) > 0
        and int(cross_stock) > 0
        and int(top_ten) > 0
        and str(sample[4])
        and str(sample[5]) == AUTHORITY
    )
    return {
        "era": era,
        "date": day,
        "source_issue_id": str(issue[0]),
        "holdings_by_stock_date_rows": int(issue[1]),
        "cross_stock_participant_issue_count": int(cross_stock),
        "top_10_input_count": int(top_ten),
        "sample_participant_id": str(sample[1]),
        "sample_position_status": str(sample[2]),
        "sample_data_quality_status": str(sample[3]),
        "sample_lineage_reference": str(sample[4]),
        "source_sha256": str(sample[5]),
        "pass": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    for number in range(2, 8):
        parser.add_argument(f"--batch{number}-summary", type=Path, required=True)
    parser.add_argument("--batch2-db", type=Path, required=True)
    parser.add_argument("--batch4-db", type=Path, required=True)
    parser.add_argument("--batch6-db", type=Path, required=True)
    parser.add_argument("--prior-parent", type=Path, required=True)
    parser.add_argument("--bridge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summaries = {
        number: batch_summary(getattr(args, f"batch{number}_summary"))
        for number in range(2, 8)
    }
    prior = load(args.prior_parent)
    bridge = load(args.bridge)
    rebuilt_rows = sum(int(summaries[number]["readback_rows"]) for number in range(2, 8))
    rebuilt_quarantine = sum(
        int(summaries[number].get("quarantined_position_states", summaries[number].get("canonical_quarantined_state_count", 0)))
        for number in range(2, 8)
    )
    all_rebuilt_pass = all(bool(summaries[number]["pass"]) for number in range(2, 8))
    global_lineage_pass = all(
        int(summaries[number]["lineage_rows"]) == int(summaries[number]["readback_rows"])
        for number in range(2, 8)
    ) and bool(prior["gates"]["global_lineage_pass"])
    global_anomaly_lineage_pass = all(
        int(summaries[number]["anomaly_lineage_rows"])
        == int(summaries[number].get("quarantined_position_states", summaries[number].get("canonical_quarantined_state_count", 0)))
        for number in range(2, 8)
    ) and rebuilt_quarantine + BATCH_1_QUARANTINE == 92
    global_idempotency_pass = all(
        int(summaries[number]["idempotent_repeat_additional_rows"]) == 0
        for number in range(2, 8)
    ) and bool(prior["gates"]["global_idempotency_pass"])
    surfaces = [
        sample_surface(args.batch2_db, "early_rebuilt", "2014-09-18"),
        sample_surface(args.batch4_db, "middle_rebuilt", "2020-01-02"),
        sample_surface(args.batch6_db, "late_rebuilt", "2025-01-02"),
    ]
    historical_surfaces_pass = all(bool(item["pass"]) for item in surfaces)
    row_reconciliation_pass = rebuilt_rows + BATCH_1_ROWS == EXPECTED_ELIGIBLE_ROWS
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "authoritative_source_sha256": AUTHORITY,
        "batch_1_retained_rows": BATCH_1_ROWS,
        "rebuilt_batch_rows": rebuilt_rows,
        "authoritative_eligible_rows": EXPECTED_ELIGIBLE_ROWS,
        "canonical_quarantined_state_count": rebuilt_quarantine + BATCH_1_QUARANTINE,
        "all_rebuilt_batches_pass": all_rebuilt_pass,
        "all_active_batches_use_authoritative_source": all_rebuilt_pass,
        "global_row_reconciliation_pass": row_reconciliation_pass,
        "global_lineage_pass": global_lineage_pass,
        "global_anomaly_lineage_pass": global_anomaly_lineage_pass,
        "global_idempotency_pass": global_idempotency_pass,
        "historical_research_surfaces": surfaces,
        "historical_research_surfaces_pass": historical_surfaces_pass,
        "historical_current_bridge_final_pass": bool(bridge.get("pass")),
        "source_layering_2026_pass": bool(prior["gates"]["source_layering_2026_pass"]),
    }
    report["pass"] = all(
        (
            all_rebuilt_pass,
            row_reconciliation_pass,
            global_lineage_pass,
            global_anomaly_lineage_pass,
            global_idempotency_pass,
            historical_surfaces_pass,
            report["historical_current_bridge_final_pass"],
            report["source_layering_2026_pass"],
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
