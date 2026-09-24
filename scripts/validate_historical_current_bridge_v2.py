"""Validate three source-backed historical/gap/current security bridges."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import date
from pathlib import Path

from app.services.current_holdings_readback import read_current_participant_holdings
from app.services.webb_sparse_holdings import reconstruct_issue_at
from app.storage.history import NormalizedSnapshotRepository


def load_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(("TURSO_DATABASE_URL=", "TURSO_AUTH_TOKEN=")):
            key, value = line.split("=", 1); os.environ[key] = value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--webb", required=True, type=Path)
    parser.add_argument("--research-store", required=True, type=Path)
    parser.add_argument("--env", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    load_env(args.env)
    import libsql
    production = libsql.connect(
        database=os.environ["TURSO_DATABASE_URL"], auth_token=os.environ["TURSO_AUTH_TOKEN"]
    )
    repository = object.__new__(NormalizedSnapshotRepository)
    repository.path = Path("unused-read-only.db")
    webb = sqlite3.connect(f"file:{args.webb.resolve().as_posix()}?mode=ro", uri=True)
    research = sqlite3.connect(f"file:{args.research_store.resolve().as_posix()}?mode=ro", uri=True)
    cases = []
    for code in ("00003", "00005", "00006"):
        native_code = code.lstrip("0") or "0"
        mapping = webb.execute(
            "SELECT c1,c2,c3,c4,c6 FROM shortnames WHERE c6=? AND c3<=? "
            "AND (c4 IS NULL OR c4>?) ORDER BY c3 DESC LIMIT 1",
            (native_code.zfill(4), "2025-12-24", "2025-12-24"),
        ).fetchone()
        if not mapping:
            mapping = webb.execute(
                "SELECT c1,c2,c3,c4,c6 FROM shortnames WHERE CAST(c6 AS INTEGER)=? AND c3<=? "
                "AND (c4 IS NULL OR c4>?) ORDER BY c3 DESC LIMIT 1",
                (int(code), "2025-12-24", "2025-12-24"),
            ).fetchone()
        if not mapping:
            raise RuntimeError(f"no Webb mapping for {code}")
        issue_id = str(mapping[0])
        historical = reconstruct_issue_at(webb, issue_id, date(2025, 12, 24))
        gap = research.execute(
            "SELECT COUNT(*),SUM(holding),MIN(source_file),MIN(source_sha256) "
            "FROM ccass_historical_holdings WHERE normalized_security_code=? AND trade_date=?",
            (code, "2026-07-31"),
        ).fetchone()
        current_row = production.execute(
            "SELECT MAX(snapshot_date) FROM ccass_snapshots WHERE stock_code=? AND source_id='longbridge'",
            (code,),
        ).fetchone()
        if not current_row or not current_row[0]:
            raise RuntimeError(f"no production snapshot for {code}")
        current_date = date.fromisoformat(str(current_row[0]))
        current = read_current_participant_holdings(repository, code, current_date)
        passed = (
            historical["active_participant_count"] > 0 and int(gap[0]) > 0 and len(current) > 0
            and historical["conflicting_change_keys"] == 0
            and all(int(row["share_quantity"]) >= 0 for row in current)
        )
        cases.append({
            "canonical_security_id": f"security:{code}", "hk_stock_code": code,
            "webb_issue_id": issue_id, "webb_security_name": mapping[1],
            "webb_date": historical["holdings_date"],
            "webb_participant_rows": historical["active_participant_count"],
            "webb_share_total": historical["active_share_total"],
            "webb_lineage": f"webbsite_full.sqlite:holdings:issueID={issue_id}",
            "gap_date": "2026-07-31", "gap_participant_rows": int(gap[0]),
            "gap_share_total": int(gap[1]), "gap_lineage": gap[2], "gap_sha256": gap[3],
            "current_date": current_date.isoformat(), "current_participant_rows": len(current),
            "current_share_total": sum(int(row["share_quantity"]) for row in current),
            "current_lineage": current[0]["source_reference"],
            "participant_semantics": "source participant/custodian identity; no beneficial-owner inference",
            "share_semantics": "absolute non-negative shares at source date",
            "pass": passed,
        })
    result = {"cases": cases, "validated_security_count": len(cases),
              "pass": len(cases) >= 3 and all(case["pass"] for case in cases)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"validated_security_count": len(cases), "pass": result["pass"],
                      "codes": [case["hk_stock_code"] for case in cases]}))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
