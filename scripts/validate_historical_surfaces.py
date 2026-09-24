"""Validate research reads against the isolated historical acceptance store."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    connection = sqlite3.connect(f"file:{args.staging.resolve().as_posix()}?mode=ro", uri=True)
    holdings_by_date = connection.execute(
        "SELECT canonical_security_id,resolved_source_date,COUNT(*) FROM canonical_historical_holdings "
        "GROUP BY 1,2 ORDER BY 3 DESC LIMIT 1"
    ).fetchone()
    participant_history = connection.execute(
        "SELECT canonical_participant_id,COUNT(DISTINCT resolved_source_date) n "
        "FROM canonical_historical_holdings GROUP BY 1 HAVING n>1 ORDER BY n DESC LIMIT 1"
    ).fetchone()
    cross_stock = connection.execute(
        "SELECT canonical_participant_id,COUNT(DISTINCT canonical_security_id) n "
        "FROM canonical_historical_holdings GROUP BY 1 HAVING n>1 ORDER BY n DESC LIMIT 1"
    ).fetchone()
    change_pairs = connection.execute(
        "SELECT COUNT(*) FROM (SELECT canonical_security_id,canonical_participant_id,COUNT(DISTINCT resolved_source_date) n "
        "FROM canonical_historical_holdings GROUP BY 1,2 HAVING n>1)"
    ).fetchone()[0]
    concentration = connection.execute(
        "SELECT COUNT(*),SUM(share_quantity),MAX(share_quantity) FROM canonical_historical_holdings "
        "WHERE canonical_security_id=? AND resolved_source_date=?",
        (holdings_by_date[0], holdings_by_date[1]),
    ).fetchone()
    timeline_dates = connection.execute(
        "SELECT COUNT(DISTINCT resolved_source_date) FROM canonical_historical_holdings"
    ).fetchone()[0]
    result = {
        "participant_holdings_by_date": bool(holdings_by_date),
        "participant_holding_history": bool(participant_history),
        "participant_changes": int(change_pairs) > 0,
        "cross_stock_participant_search": bool(cross_stock),
        "top_participant_concentration_inputs": bool(concentration and concentration[0]),
        "broker_fingerprint_inputs": bool(cross_stock and concentration),
        "historical_ccass_timeline": int(timeline_dates) > 1,
        "ownership_percentage": "UNKNOWN_DENOMINATOR_NOT_STAGED",
        "sample_holdings_group": holdings_by_date,
        "sample_participant_history": participant_history,
        "sample_cross_stock_participant": cross_stock,
        "change_pair_count": int(change_pairs),
        "timeline_date_count": int(timeline_dates),
    }
    result["pass"] = all(result[key] is True for key in (
        "participant_holdings_by_date", "participant_holding_history", "participant_changes",
        "cross_stock_participant_search", "top_participant_concentration_inputs",
        "broker_fingerprint_inputs", "historical_ccass_timeline",
    ))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
