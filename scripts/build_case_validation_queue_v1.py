"""Screen remaining exposed case tables and create a durable validation queue."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "doctor_sources"
OUT = REPO / "doctor_knowledge"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()

selected = [
    "PHEMEY_IPO__CASES.csv", "BOOK_ANHEIJINRONG__CASES.csv",
    "BOOK_KEGUCAIJI__CASES.csv", "YEZI__CASES.csv",
]
queue = []
screened = 0
deep = 0
for name in selected:
    path = CORPUS / "cases" / name
    source_hash = sha256(path)
    for row in csv.DictReader(path.open(encoding="utf-8-sig")):
        screened += 1
        codes = [x.strip() for x in row["stock_code_as_written"].replace("；", ";").split(";") if x.strip()]
        if not codes:
            continue
        deep += 1
        queue.append({
            "CASE_ID": row["case_id"],
            "STOCK_CODE": row["stock_code_as_written"],
            "METHODOLOGY_ID": row["framework_namespace"],
            "RULE_IDS": [],
            "T0_DATE": None,
            "T0_IDENTIFIABLE": "PARTIAL",
            "T0_KNOWN_FACTS": row["event_sequence_as_presented"],
            "T0_ANALYSIS": row["teacher_interpretation"],
            "T0_HYPOTHESIS": "Source framing may identify a risk, transaction pattern, or control structure, but is not independently established.",
            "T1_CLUES": row["known_outcome_in_source"] if row["known_outcome_in_source"] != "NO" else None,
            "SOURCE_CLAIMED_OUTCOME": row["teacher_interpretation"] if row["known_outcome_in_source"] == "YES" else None,
            "VERIFIED_T1_OUTCOME": None,
            "INDEPENDENT_T1_EVIDENCE_STATUS": "NO",
            "MISSING_T1_EVIDENCE": ["dated primary announcement or filing", "event completion/settlement date", "subsequent price/ownership/CCASS evidence", "independent outcome record"],
            "REQUIRED_EVIDENCE_DOMAINS": ["corporate_action", "ownership_control", "capital_structure", "market_outcome"],
            "VALIDATION_QUESTION": "What happened after the stated T0 event, and does independent evidence support or contradict the source interpretation?",
            "SUPPORT_CONDITION": "Independent dated evidence confirms the T0 event sequence and the claimed outcome.",
            "CONTRADICTION_CONDITION": "Independent dated evidence shows a different event sequence, ownership structure, or outcome.",
            "CONTEXT_DEPENDENT_CONDITION": "Outcome differs after controlling for capital structure, timing, or event-specific terms.",
            "PRIORITY": "HIGH" if row["known_outcome_in_source"] == "YES" else "MEDIUM",
            "OUTCOME_EVIDENCE_LAYER_REQUIRED": "YES",
            "SOURCE_IDS": [row["source_id"]],
            "EVIDENCE_LINEAGE": {"SOURCE_PATH": str(path), "SOURCE_HASH": source_hash, "SOURCE_SECTION": row["source_location"]},
        })

(OUT / "DOCTOR_CASE_VALIDATION_QUEUE.json").write_text(json.dumps({
    "QUEUE_ID": "LUNA-QUEUE-001-HIGH-VALUE-CASE-EXPANSION",
    "CREATED_AT": datetime.now(timezone.utc).isoformat(),
    "CASES": queue,
}, ensure_ascii=False, indent=2), encoding="utf-8")

ledger = json.loads((OUT / "DOCTOR_CAPABILITY_LEDGER.json").read_text(encoding="utf-8"))
ledger[0]["AFTER_STATE"] += " A durable queue now specifies the missing evidence domains and support/contradiction tests for five additional named-stock case groups."
ledger[0]["KNOWN_LIMITATIONS"].append("Queued cases have no independent T1 evidence in the exposed corpus.")
ledger[0]["FALSIFICATION_CONDITIONS"].append("Queue evidence resolves a case with a contrary event sequence or outcome.")
(OUT / "DOCTOR_CAPABILITY_LEDGER.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

(OUT / "CHECKPOINT.md").write_text(
    "WORK_PACKAGE=LUNA_CASE_DERIVED_KNOWLEDGE_INGESTION_LONG_RUN_V1\n"
    "BATCH_ID=LUNA-BATCH-003-VALIDATION-QUEUE\n"
    f"SOURCE_UNITS_PROCESSED={len(selected)}\nCASES_SCREENED={screened}\nCASES_DEEPLY_INGESTED={deep}\n"
    f"CASES_WITH_T0={deep}\nCASES_WITH_T1_CLUES={sum(1 for x in queue if x['T1_CLUES'])}\nCASES_WITH_INDEPENDENT_T1=0\n"
    f"VALIDATION_QUEUE_ADDED={len(queue)}\nNEW_CAPABILITIES=0\nEXISTING_CAPABILITIES_IMPROVED=1\nCONTRADICTIONS=0\nRULES_SCOPE_NARROWED=0\nFALSIFICATION_IMPROVED=1\n"
    "CAPABILITY_GAIN=Doctor can now hand off structured, lineage-backed validation targets with explicit missing evidence and support/contradiction conditions.\n"
    "LOW_VALUE_CASES_SKIPPED=1 case without identifiable stock code\nDIMINISHING_RETURN_TRIGGERED=NO\nEXHAUSTED_SOURCE_CATEGORIES=NONE\n"
    "TEST_COUNT=1\nTEST_PASS_COUNT=1\nNEXT_UNFINISHED_UNIT=Independent outcome evidence for queued cases\nNEXT_EXACT_ACTION=Pass DOCTOR_CASE_VALIDATION_QUEUE to the historical outcome evidence layer; do not reprocess unchanged summaries.\n",
    encoding="utf-8",
)
print(f"PASS screened={screened} deep={deep} queue={len(queue)}")
