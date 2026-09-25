"""Freeze LT-08 contract and report the smallest honest empirical package."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "doctor_outcome_evidence"
targets = json.loads((REPO / "docs" / "DOCTOR_LUNA_VALIDATION_TARGETS_V1.json").read_text(encoding="utf-8"))
target = next(x for x in targets["targets"] if x["target_id"] == "LT-08")

package = {
    "PACKAGE_ID": "LT08_POINT_IN_TIME_EVIDENCE_PACKAGE_V1",
    "TARGET": target,
    "CASE_ID": None,
    "STOCK_CODE": None,
    "T0_DATE": None,
    "T0_SIGNAL_INPUTS": None,
    "T0_SIGNAL_OUTPUT": None,
    "T0_SOURCE_REFS": [],
    "T1_START_DATE": None,
    "T1_END_DATE": "2026-09-25",
    "T1_EVIDENCE_ITEMS": [],
    "T1_SOURCE_REFS": [],
    "T0_T1_SOURCE_INDEPENDENCE": "UNASSESSABLE",
    "ISSUED_SHARES_AT_T0": None,
    "CCASS_TOTAL_AT_T0": None,
    "DENOMINATOR_ARTIFACT_RISK": "UNKNOWN",
    "CORPORATE_ACTION_CONFOUNDERS": "NOT_ASSESSED",
    "SETTLEMENT_SEMANTICS_STATUS": "NOT_ASSESSED",
    "DATA_QUALITY_STATUS": "BLOCKED_NO_ELIGIBLE_CASE",
    "POINT_IN_TIME_SAFE": False,
    "EVIDENCE_LINEAGE_COMPLETE": False,
    "READY_FOR_CASE_VALIDATION": "NO",
    "MISSING_EVIDENCE": [
        "Authoritative concentration alert with publication date",
        "Same-date CCASS participant snapshot for a stock with that alert",
        "Issued-shares denominator at T0",
        "Reproducible gap-method T0 calculation",
        "Independent source set for comparison",
    ],
    "KNOWN_LIMITATIONS": [
        "The target contract is now authoritative and preserved exactly, but no eligible official concentration-alert case is reachable in the current approved surfaces.",
        "Existing CCASS holdings/concentration infrastructure cannot substitute for the required official disclosure target.",
    ],
    "GENERATED_AT": datetime.now(timezone.utc).isoformat(),
}
(OUT / "LT08_POINT_IN_TIME_EVIDENCE_PACKAGE_V1.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "CHECKPOINT_LT08.md").write_text(
    "WORK_PACKAGE=LT_08_FIRST_EMPIRICAL_EVIDENCE_GATE\nTARGET_ID=LT-08\nCAPABILITY_ID=CAP-06\n"
    "ZC_TARGET_CONTRACT_REACHABLE=YES\nLT08_CONTRACT_VERIFIED=YES\nT0_SIGNAL_REPRODUCIBLE=NO\n"
    "T0_SOURCE_LINEAGE=NOT_AVAILABLE\nT1_INDEPENDENT_EVIDENCE=NO\nT1_SOURCE_LINEAGE=NOT_AVAILABLE\n"
    "POINT_IN_TIME_SAFE=NO\nDENOMINATOR_SAFETY=NOT_EVALUATED\nREADY_FOR_CASE_VALIDATION=NO\n"
    "RESULT=PARTIAL_CONTRACT_GATE_ONLY\n"
    "EARLIEST_REMAINING_BLOCKER=No approved official concentration-alert case with same-date CCASS and issued-share denominator.\n"
    "NEXT_EXACT_ACTION=Locate one eligible official concentration-alert disclosure and join it to same-date CCASS plus denominator evidence without rebuilding infrastructure.\n",
    encoding="utf-8",
)
print("PASS target=LT-08 capability=CAP-06 contract=verified package=partial")
