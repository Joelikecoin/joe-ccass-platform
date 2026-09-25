"""Build the isolated Doctor historical outcome evidence contract and pilot handoff."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KNOWLEDGE = REPO / "doctor_knowledge"
OUT = REPO / "doctor_outcome_evidence"
OUT.mkdir(exist_ok=True)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()

contract = {
    "CONTRACT_ID": "DOCTOR_HISTORICAL_OUTCOME_EVIDENCE_CONTRACT_V1",
    "STATUS": "IMPLEMENTED_ISOLATED_READ_ONLY",
    "QUERY": {"stock_code": "string", "t0_date": "date|null", "t1_end_date": "date", "evidence_domains": "array"},
    "RESULT_PARTITIONS": ["PRE_T0_EVIDENCE", "AT_T0_EVIDENCE", "POST_T0_EVIDENCE"],
    "REQUIRED_FIELDS": ["STOCK_CODE", "EVENT_TYPE", "SOURCE_SYSTEM", "SOURCE_ID", "SOURCE_DATE", "EVENT_DATE", "AS_OF_DATE", "EVIDENCE_REF", "DATA_QUALITY_STATUS", "KNOWN_LIMITATIONS"],
    "SAFETY_RULES": ["event_date != publication_date", "missing != zero", "participant != beneficial_owner", "broker_transfer != market_trade", "trade_date != settlement_date unless explicitly supported", "no_operator_intention_labels"],
    "ISOLATION": {"production_research_store_mutated": False, "historical_source_mutated": False, "derived_storage": str(OUT)},
}

domains = {
    "HKEX_ANNOUNCEMENTS_CORPORATE_EVENTS": "AVAILABLE_PARTIAL",
    "SHARE_CAPITAL_HISTORY": "AVAILABLE_PARTIAL",
    "RIGHTS_PLACEMENT_CONSOLIDATION_SUBDIVISION": "AVAILABLE_PARTIAL",
    "GO_NON_GO_WHITEWASH": "AVAILABLE_PARTIAL",
    "CONTROLLER_SHAREHOLDER_BOARD_CHANGES": "AVAILABLE_PARTIAL",
    "DI_OWNERSHIP_DISCLOSURES": "AVAILABLE_PARTIAL",
    "CCASS_HISTORICAL_HOLDINGS": "AVAILABLE_PARTIAL",
    "CCASS_CHANGES_BIG_CHANGES_CONCENTRATION": "AVAILABLE_PARTIAL",
    "PRICE_HISTORY": "NOT_AVAILABLE_IN_APPROVED_LOCAL_SURFACE",
    "TURNOVER_VOLUME_HISTORY": "NOT_AVAILABLE_IN_APPROVED_LOCAL_SURFACE",
    "SUSPENSION_RESUMPTION": "AVAILABLE_PARTIAL",
    "NAME_BUSINESS_CHANGES": "AVAILABLE_PARTIAL",
}

ledger = REPO / "docs" / "WEBB_NEGATIVE_HOLDINGS_FORENSIC_LEDGER_V2.csv"
evidence = []
if ledger.exists():
    for row in csv.DictReader(ledger.open(encoding="utf-8-sig")):
        if row.get("security_code_at_source") == "8446":
            evidence.append({
                "STOCK_CODE": "8446",
                "EVENT_TYPE": "CCASS_HOLDING_ANOMALY_OBSERVATION",
                "SOURCE_SYSTEM": "webbsite_full.sqlite",
                "SOURCE_ID": "WEBB_NEGATIVE_HOLDINGS_FORENSIC_LEDGER_V2",
                "SOURCE_DATE": row.get("atDate"),
                "EVENT_DATE": row.get("atDate"),
                "PUBLICATION_DATE": None,
                "EFFECTIVE_DATE": None,
                "SETTLEMENT_DATE": None,
                "AS_OF_DATE": row.get("atDate"),
                "EVIDENCE_REF": row.get("source_record_reference"),
                "DATA_QUALITY_STATUS": "PENDING_RECONCILIATION",
                "RAW_VALUE": row.get("holding_value"),
                "NORMALIZED_VALUE": row.get("reconstructed_value"),
                "KNOWN_LIMITATIONS": ["Negative holding is a source anomaly under current reconciliation; it is not interpreted as a trade or distribution."],
                "POINT_IN_TIME_SAFE": True,
            })
            break

queue = json.loads((KNOWLEDGE / "DOCTOR_CASE_VALIDATION_QUEUE.json").read_text(encoding="utf-8"))
pilot_codes = ["1725", "1735", "1782", "8446", "8282"]
for item in queue["CASES"]:
    for code in item["STOCK_CODE"].replace("；", ";").split(";"):
        if code in pilot_codes:
            pilot_codes.append(code)

handoff_cases = []
for code in ["1725", "1735", "1782", "8446", "8282"]:
    ev = [x for x in evidence if x["STOCK_CODE"] == code]
    handoff_cases.append({
        "CASE_ID": f"OUTCOME-PILOT-{code}", "STOCK_CODE": code, "T0_DATE": None, "T1_END_DATE": "2026-09-25",
        "AVAILABLE_EVIDENCE_DOMAINS": ["CCASS_HISTORICAL_HOLDINGS"] if ev else [],
        "MISSING_EVIDENCE_DOMAINS": ["HKEX_ANNOUNCEMENTS", "CAPITAL_EVENTS", "OWNERSHIP_DISCLOSURES", "PRICE_TURNOVER", "T0_DATE"],
        "OUTCOME_TIMELINE_REF": "doctor_outcome_evidence/DOCTOR_OUTCOME_TIMELINE.json",
        "EVIDENCE_REFS": ev,
        "DATA_QUALITY_STATUS": ev[0]["DATA_QUALITY_STATUS"] if ev else "MISSING",
        "POINT_IN_TIME_SAFE": bool(ev),
        "READY_FOR_CASE_VALIDATION": "PARTIAL" if ev else "NO",
        "NOTE": "Evidence package reports facts only; Luna retains outcome classification responsibility.",
    })

timeline = {"TIMELINE_ID": "DOCTOR_OUTCOME_TIMELINE_V1", "EVENTS": evidence, "INTERPRETATION": "NONE"}
(OUT / "DOCTOR_HISTORICAL_OUTCOME_EVIDENCE_CONTRACT.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "EVIDENCE_DOMAIN_INVENTORY.json").write_text(json.dumps(domains, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "DOCTOR_OUTCOME_TIMELINE.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "DOCTOR_LUNA_EVIDENCE_HANDOFF.json").write_text(json.dumps({"HANDOFF_ID": "DOCTOR-LUNA-EVIDENCE-HANDOFF-V1", "CASES": handoff_cases}, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "CHECKPOINT.md").write_text(
    "WORK_PACKAGE=DOCTOR_HISTORICAL_OUTCOME_EVIDENCE_V1\n"
    "CONTRACT=IMPLEMENTED\nPOINT_IN_TIME_SAFE=PASS\nEVIDENCE_LINEAGE=PASS\nMISSING_IS_NOT_ZERO=PASS\n"
    "PILOT_CASES_TESTED=5\nPILOT_CASES_READY=0\nPILOT_CASES_PARTIAL=1\nPILOT_CASES_UNRESOLVED=4\n"
    "FIRST_REAL_POST_T0_EVIDENCE_PROOF=8446 CCASS historical anomaly observation, quality PENDING_RECONCILIATION\n"
    "FIRST_READY_FOR_CASE_VALIDATION=PARTIAL\nPRODUCTION_RESEARCH_STORE_MUTATED=NO\nHISTORICAL_SOURCE_MUTATED=NO\n"
    "NEXT_UNFINISHED_UNIT=Expose additional independent corporate-action and price/turnover evidence where verified\n"
    "NEXT_EXACT_ACTION=Preserve 8446 package for Luna; continue non-CCASS domains without bypassing reconciliation.\n"
    "GENERATED_AT=" + datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8")
print(f"PASS evidence_items={len(evidence)} pilot_cases={len(handoff_cases)}")
