"""Freeze LT-09 contract and the verified 02318 eligibility result."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "doctor_outcome_evidence"
targets = json.loads((REPO / "docs" / "DOCTOR_LUNA_VALIDATION_TARGETS_V1.json").read_text(encoding="utf-8"))
target = next(x for x in targets["targets"] if x["target_id"] == "LT-09")

package = {
    "PACKAGE_ID": "LT09_POINT_IN_TIME_EVIDENCE_PACKAGE_V1",
    "TARGET": target,
    "CASE_ID": "LT09-CAND-02318",
    "STOCK_CODE": "02318",
    "T0_DATE": None,
    "T0_FACTS": [],
    "T0_THRESHOLD_STATE": {"THRESHOLD_VALUE": None, "THRESHOLD_SOURCE": "authoritative target specifies 29-30% zone in claim; exact historical threshold context unavailable"},
    "T0_SOURCE_REFS": [],
    "T1_START_DATE": None,
    "T1_END_DATE": "2026-09-25",
    "T1_EVIDENCE_ITEMS": [],
    "T1_SOURCE_REFS": [],
    "T0_T1_SOURCE_INDEPENDENCE": "UNASSESSABLE",
    "DENOMINATOR_EFFECT_RISK": "UNKNOWN",
    "CAPITAL_ACTION_CONFOUNDERS": "NOT_ASSESSED",
    "POINT_IN_TIME_SAFE": False,
    "EVIDENCE_LINEAGE_COMPLETE": False,
    "DATA_QUALITY_STATUS": "MISSING_LOCAL_DATA",
    "READY_FOR_CASE_VALIDATION": "NO",
    "MISSING_EVIDENCE": ["DION holding sequence", "T0 date and publication date", "exact threshold context", "subsequent 24-month capital/control path", "issued-share history"],
    "KNOWN_LIMITATIONS": ["Read-only local ccass_snapshots.db contains zero rows for 02318 in ccass_snapshots, disclosure_interests, and share_capital_history.", "No nearby-date substitution was made."],
    "GENERATED_AT": datetime.now(timezone.utc).isoformat(),
}
(OUT / "LT09_POINT_IN_TIME_EVIDENCE_PACKAGE_V1.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "LT09_CANDIDATE_REGISTER.json").write_text(json.dumps({
    "TARGET_ID": "LT-09", "CANDIDATES": [{
        "CASE_CANDIDATE_ID": "LT09-CAND-02318", "STOCK_CODE": "02318", "DION_SEQUENCE": "NO", "T0_DATE": "NO", "T1_PATH": "NO", "DENOMINATOR": "NO", "POINT_IN_TIME_SAFE": "NO", "ELIGIBLE": "NO", "REJECTION_REASON": "Actual local read-only database has zero CCASS snapshots, zero DION rows, and zero share-capital rows for 02318."
    }]
}, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "CHECKPOINT_LT09.md").write_text(
    "WORK_PACKAGE=DOCTOR_HISTORICAL_OUTCOME_EVIDENCE_V1\nTARGET_ID=LT-09\nCAPABILITY_ID=CAP-10\nRULE_FAMILY=RF-10\n"
    "LT09_CONTRACT_VERIFIED=YES\nCASE_ID=LT09-CAND-02318\nSTOCK_CODE=02318\nT0_REPRODUCIBLE=NO\nT0_THRESHOLD_STATE=INCOMPLETE\nT0_SOURCE_LINEAGE=NOT_AVAILABLE\n"
    "T1_EVIDENCE_AVAILABLE=NO\nT1_SOURCE_INDEPENDENCE=UNASSESSABLE\nT1_SOURCE_LINEAGE=NOT_AVAILABLE\nTHRESHOLD_CONTEXT_VERIFIED=NO\nDENOMINATOR_EFFECT_RISK=UNKNOWN\nCAPITAL_ACTION_CONFOUNDERS=NOT_ASSESSED\nPOINT_IN_TIME_SAFE=NO\nDATA_QUALITY_STATUS=MISSING_LOCAL_DATA\nREADY_FOR_CASE_VALIDATION=NO\n"
    "RESULT=LT09_CONTRACT_VERIFIED_CASE_INELIGIBLE\n"
    "EARLIEST_REMAINING_BLOCKER=Reachable approved DION sequence plus T0 date, exact threshold context, issued-share history, and subsequent 24-month control-path evidence for one case.\n"
    "NEXT_EXACT_ACTION=Move to another target or obtain an approved historical DION dataset; do not rebuild infrastructure or infer LT-09 outcome.\n",
    encoding="utf-8")
print("PASS LT09 contract verified; 02318 rejected by actual zero-row data check")
