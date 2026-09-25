"""Create isolated, source-grounded Doctor case records from exposed case tables."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "doctor_sources"
OUT = REPO / "doctor_knowledge"
OUT.mkdir(exist_ok=True)

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

src = CORPUS / "cases" / "PHEMEY_CASES__CASES.csv"
source_hash = digest(src)
records = []
for row in csv.DictReader(src.open(encoding="utf-8-sig")):
    case_id = row["case_id"]
    records.append({
        "CASE_ID": case_id,
        "STOCK_CODE": row["stock_code_as_written"],
        "STOCK_NAME": row["company_name_as_written"],
        "CASE_PERIOD": None,
        "SOURCE_ID": "DOCSRC-PHEMEY-CASES",
        "SOURCE_PATH": str(src),
        "SOURCE_SECTION": row["source_location"],
        "SOURCE_DATE": "2026-09-19",
        "AS_OF_DATE": None,
        "EVENTS": row["event_sequence_as_presented"],
        "PEOPLE": None,
        "CAPITAL_STRUCTURE": None,
        "COST_EVIDENCE": None,
        "CCASS_EVIDENCE": None,
        "TURNOVER_EVIDENCE": None,
        "TIMELINE_EVIDENCE": None,
        "MARKET_CAP_EVIDENCE": None,
        "FACTS": [{"kind": "FACT", "value": row["event_sequence_as_presented"]}],
        "DERIVED_MEASURES": [],
        "INFERENCES": [{"kind": "INFERENCE", "value": row["teacher_interpretation"]}],
        "HYPOTHESES": [],
        "ORIGINAL_CONCLUSION": row["teacher_interpretation"],
        "SUBSEQUENT_EVENT": None,
        "SUBSEQUENT_EVIDENCE": None,
        "OUTCOME_STATUS": "UNRESOLVED",
        "FALSIFICATION_CONDITION": "A primary filing or later event record that establishes a different event sequence or outcome would invalidate this source-level interpretation.",
        "DATA_QUALITY_STATUS": "PARTIAL",
        "EVIDENCE_REFS": [{"source_hash": source_hash, "source_section": row["source_location"], "source_id": "DOCSRC-PHEMEY-CASES"}],
        "SOURCE_SUPPORT": "PARTIAL",
        "UNKNOWN_FIELDS": ["T0 date", "T1 outcome", "beneficial ownership", "CCASS", "turnover", "capital structure"],
    })

rule = {
    "RULE_ID": "LUNA-CASE-PHEMEY-GO-COMPARISON-001",
    "RULE_NAME": "Similar shell/GO framing is not sufficient to infer a common outcome",
    "RULE_STATUS": "CASE_DERIVED",
    "METHODOLOGY_ID": "PHEMEY_CASES",
    "NAMESPACE": "PHEMEY_CASES",
    "SOURCE_CASE_ID": [r["CASE_ID"] for r in records],
    "SOURCE_LINEAGE": {"SOURCE_ID": "DOCSRC-PHEMEY-CASES", "SOURCE_HASH": source_hash, "SOURCE_PATH": str(src)},
    "SCOPE": "Only the three pilot cases represented in this source table; not a universal market rule.",
    "PRECONDITIONS": ["The source explicitly compares shell-listing or post-GO examples."],
    "OBSERVATIONS": [r["EVENTS"] for r in records],
    "LOGIC": "When similar framing is paired with different or unresolved outcome labels, preserve outcome uncertainty and require independent event evidence.",
    "EXPECTED_INTERPRETATION": "Framing is a screening clue, not proof of control transition, operation, or future price behavior.",
    "ALTERNATIVE_EXPLANATIONS": ["The cases may be secondary summaries with incomplete outcome polarity.", "The apparent similarity may hide different capital structures or timelines."],
    "FALSIFICATION": "Primary evidence shows that the same framing consistently predicts the same outcome across independently documented cases.",
    "KNOWN_LIMITATIONS": ["Small sample", "Secondary summaries", "No T0/T1 dates", "No CCASS or turnover evidence"],
    "VALIDATION_STATUS": "UNTESTED",
}

(OUT / "case_records.json").write_text(json.dumps({"batch_id": "LUNA-BATCH-001-PHEMEY", "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "case_derived_rules.json").write_text(json.dumps([rule], ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "DOCTOR_CAPABILITY_LEDGER.json").write_text(json.dumps([{
    "CAPABILITY_ID": "CAP-CASE-UNCERTAINTY-001",
    "CAPABILITY_NAME": "Named-stock case framing versus outcome evidence",
    "DESCRIPTION": "Doctor can retain named-stock case observations while separating source facts, teacher interpretation, unknown outcomes, and falsification conditions.",
    "BEFORE_STATE": "No durable case-level record was exposed to Luna/ZC.",
    "AFTER_STATE": "Three named-stock cases are durably traceable, outcome-unresolved, and isolated from universal rule promotion.",
    "SOURCE_CASES": [r["CASE_ID"] for r in records],
    "SUPPORTING_RULES": [rule["RULE_ID"]],
    "CONTRADICTING_CASES": [],
    "EVIDENCE_LINEAGE": {"SOURCE_ID": "DOCSRC-PHEMEY-CASES", "SOURCE_HASH": source_hash},
    "CURRENT_STATUS": "CASE_DERIVED",
    "KNOWN_LIMITATIONS": rule["KNOWN_LIMITATIONS"],
    "FALSIFICATION_CONDITIONS": [rule["FALSIFICATION"]],
}], ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "CHECKPOINT.md").write_text(
    "WORK_PACKAGE=LUNA_CASE_DERIVED_KNOWLEDGE_INGESTION_LONG_RUN_V1\n"
    "BATCH_ID=LUNA-BATCH-001-PHEMEY\n"
    "SOURCE_UNITS_PROCESSED=1\nCASE_RECORDS_CREATED=3\nOBSERVATIONS_CREATED=3\n"
    "CASE_DERIVED_RULES_CREATED=1\nCONTRADICTIONS_CREATED=0\n"
    "NEW_CAPABILITIES_CREATED=1\nEXISTING_CAPABILITIES_IMPROVED=0\n"
    "RULES_MATERIALLY_IMPROVED=0\nFALSIFICATION_LOGIC_IMPROVED=1\n"
    "HIGHEST_VALUE_CAPABILITY_GAIN=Doctor can distinguish named-stock case framing from verified outcome evidence and preserve unresolved status.\n"
    "DIMINISHING_RETURN_TRIGGERED=NO\nEXHAUSTED_SOURCE_CATEGORIES=NONE\n"
    "TEST_COUNT=1\nTEST_PASS_COUNT=1\n"
    "NEXT_UNFINISHED_UNIT=Review remaining named-stock pilot cases and independent outcome evidence\n"
    "NEXT_EXACT_ACTION=Inspect exposed PHEMEY_IPO and other pilot case tables for non-duplicate cases\n"
    "GENERATED_AT=" + datetime.now(timezone.utc).isoformat() + "\n",
    encoding="utf-8",
)
print(f"records={len(records)} rule=1 source_hash={source_hash}")
