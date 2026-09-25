"""Record LT-08 candidate eligibility without fabricating official alerts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "doctor_outcome_evidence"
candidates = []
for code, reason in [
    ("8446", "CCASS anomaly exists, but no official concentration-alert disclosure or same-date issued-share denominator is present."),
    ("1725", "Named-stock case exists, but no official concentration-alert disclosure is reachable."),
    ("1735", "Named-stock case exists, but no official concentration-alert disclosure is reachable."),
    ("1782", "Named-stock case exists, but no official concentration-alert disclosure is reachable."),
    ("8282", "Named-stock case exists, but no official concentration-alert disclosure is reachable."),
]:
    candidates.append({
        "CASE_CANDIDATE_ID": f"LT08-CAND-{code}", "STOCK_CODE": code,
        "OFFICIAL_ALERT": "NO", "ALERT_DATE": None, "ALERT_REFERENCE": None,
        "CCASS_SAME_DATE": "NO", "DENOMINATOR_AVAILABLE": "NO",
        "POINT_IN_TIME_SAFE": "NO", "ELIGIBLE": "NO",
        "DATE_ALIGNMENT_STATUS": "UNUSABLE", "REJECTION_REASON": reason,
    })
(OUT / "LT08_CANDIDATE_REGISTER.json").write_text(json.dumps({"TARGET_ID": "LT-08", "CAPABILITY_ID": "CAP-06", "CANDIDATES": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "CHECKPOINT_LT08.md").write_text(
    "WORK_PACKAGE=DOCTOR_HISTORICAL_OUTCOME_EVIDENCE_V1\nSUBTASK=LT08_ELIGIBLE_CASE_DISCOVERY_AND_JOIN_V1\n"
    "START_COMMIT=9622316\nCANDIDATES_CHECKED=5\nELIGIBLE_CASES_FOUND=0\n"
    "T0_SIGNAL_REPRODUCIBLE=NO\nT0_SOURCE_LINEAGE=NOT_AVAILABLE\nT1_EVIDENCE_AVAILABLE=NO\nT1_SOURCE_INDEPENDENCE=UNASSESSABLE\nT1_SOURCE_LINEAGE=NOT_AVAILABLE\n"
    "POINT_IN_TIME_SAFE=NO\nDENOMINATOR_ARTIFACT_RISK=UNKNOWN\nREADY_FOR_CASE_VALIDATION=NO\n"
    "RESULT=NO_ELIGIBLE_LT08_CASE\n"
    "EARLIEST_REMAINING_BLOCKER=Official concentration-alert disclosure with exact-date CCASS participant data and issued-share denominator.\n"
    "NEXT_EXACT_ACTION=Obtain or expose one approved official concentration-alert disclosure; do not substitute generic concentration or nearby dates.\n"
    "GENERATED_AT=" + datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8")
print("PASS candidates=5 eligible=0")
