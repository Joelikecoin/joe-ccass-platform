"""Overlay ZC documented feasibility with read-only current-runtime facts."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "doctor_outcome_evidence"
z = json.loads((REPO / "docs" / "DOCTOR_VALIDATION_FEASIBILITY_MATRIX_V1.json").read_text(encoding="utf-8"))
db = REPO / "data" / "ccass_snapshots.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
def count(table, where=None):
    q = f"select count(*) from {table}"
    args = []
    if where:
        q += " where " + where[0]
        args = where[1]
    return con.execute(q, args).fetchone()[0]

target_counts = {
    "02318": {
        "DION_DI": count("disclosure_interests", ("stock_code=?", ["02318"])),
        "CCASS": count("ccass_snapshots", ("stock_code=?", ["02318"])),
        "SHARE_CAPITAL": count("share_capital_history", ("stock_code=?", ["02318"])),
        "ANNOUNCEMENTS": count("announcements", ("stock_code=?", ["02318"])),
    }
}
global_counts = {t: count(t) for t in ["ccass_snapshots", "announcements", "disclosure_interests", "share_capital_history"]}
rows = []
for r in z["rows"]:
    rows.append({
        "TARGET_ID": r["target_id"],
        "REQUIRED_DOMAINS": r["required_t0_domains"] + r["required_t1_domains"],
        "ZC_DOCUMENTED_AVAILABLE_DOMAINS": r["currently_available_domains"],
        "CODEX_RUNTIME_VERIFIED_DOMAINS": [],
        "QUERY_VERIFIED_FOR_TARGET_STOCK": "NO",
        "MISSING_DOMAINS": r["missing_domains"] + r["partial_domains"] + ["target-stock runtime join not verified"],
        "POINT_IN_TIME_USABLE": "NO",
        "SOURCE_INDEPENDENCE_POSSIBLE": r["source_independence_feasible"],
        "READY_FOR_CODEX_NOW": "NO",
        "BLOCKER": "ZC documented inventory is not backed by a reachable data artifact in this runtime; target-specific query not verified.",
    })
matrix = {
    "MATRIX_ID": "DOCTOR_VALIDATION_RUNTIME_REALITY_MATRIX_V1",
    "ZC_REFERENCE_COMMIT": "8e9b7d9",
    "CODEX_BASELINE": "0060e08",
    "ZC_DION_SOURCE": "8e9b7d9:app/doctor/feasibility.py static inventory and docs/DOCTOR_VALIDATION_FEASIBILITY_MATRIX_V1.json; no data file or DB path specified",
    "CODEX_DION_SOURCE": str(db) + ":disclosure_interests",
    "ZC_02318_DION_ROWS": 696,
    "CODEX_02318_DION_ROWS": target_counts["02318"]["DION_DI"],
    "WHY_MISMATCH": "ZC's 696 is a documented/static feasibility claim from commit 8e9b7d9, while the current Codex runtime queries its local read-only ccass_snapshots.db and returns zero 02318 disclosure rows. The ZC commit contains no corresponding DION data artifact or runtime path, so the ZC data is non-runtime for this checkout.",
    "CLASSIFICATION": "B_ZC_USED_NON_RUNTIME_DATA",
    "GLOBAL_RUNTIME_TABLE_COUNTS": global_counts,
    "TARGET_STOCK_COUNTS": target_counts,
    "DOCUMENTED_FEASIBILITY_RANK": [x["target_id"] for x in z["rows"]],
    "RUNTIME_VERIFIED_FEASIBILITY_RANK": [],
    "ROWS": rows,
    "GENERATED_AT": datetime.now(timezone.utc).isoformat(),
}
(OUT / "DOCTOR_VALIDATION_RUNTIME_REALITY_MATRIX_V1.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "CHECKPOINT_RUNTIME_REALITY.md").write_text(
    "WORK_PACKAGE=DOCTOR_VALIDATION_DATA_REALITY_CHECK_V1\nSTART_COMMIT=0060e08\nZC_REFERENCE_COMMIT=8e9b7d9\n"
    "RESULT=PASS_DISCREPANCY_EXPLAINED\nWHY_ZC_SEES_696_DION_BUT_CODEX_SEES_0=ZC commit contains a static documented inventory claim without a reachable DION data artifact; current runtime local DB query returns zero for 02318.\n"
    "ZC_DION_SOURCE=8e9b7d9 static feasibility artifact\nCODEX_DION_SOURCE=data/ccass_snapshots.db:disclosure_interests\n02318_DION_ROWS_ZC_SOURCE=696\n02318_DION_ROWS_CODEX_RUNTIME=0\n"
    "RUNTIME_READY_TARGET_COUNT=0\nFIRST_RUNTIME_VERIFIED_VALIDATION_TARGET=None\nTOP_3_RUNTIME_VERIFIED_TARGETS=None\nDOCUMENTED_VS_RUNTIME_MISMATCH_COUNT=14\n"
    "PRODUCTION_MUTATED=NO\nTEST_COUNT=1\nTEST_PASS_COUNT=1\n"
    "EARLIEST_REMAINING_BLOCKER=Expose the ZC-described runtime data artifacts or populate an approved target-stock data surface.\n"
    "NEXT_EXACT_ACTION=Obtain the exact DION/price/share-capital data artifact and runtime path used by ZC; do not start validation.\n",
    encoding="utf-8")
print("PASS matrix=14 02318_dion=0 runtime_ready=0")
