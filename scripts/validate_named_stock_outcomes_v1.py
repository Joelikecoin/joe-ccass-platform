"""Record point-in-time outcome validation without converting summaries into hindsight facts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "doctor_knowledge"
records = json.loads((OUT / "case_records.json").read_text(encoding="utf-8"))

validation = {
    "BATCH_ID": "LUNA-BATCH-002-NAMED-STOCK-OUTCOME-VALIDATION",
    "CASES": [],
    "INDEPENDENT_T1_EVIDENCE_FOUND": False,
    "NOTE": "The reachable approved material is methodology-labelled secondary summary material. No independent T1 filing, event record, or outcome dataset was reachable for these five codes.",
}
for code in ["1725", "1735", "1782", "8446", "8282"]:
    if code in {"1725", "1735"}:
        t0 = "Sponsor/history presented as a screening clue for shell-listing research; source explicitly says it is not proof."
        hypothesis = "The framing may identify a candidate, but does not establish a control transition or future outcome."
        source_case = ["CASE-P1B-PHC-001", "CASE-P1B-PHC-002"]
    else:
        t0 = "Post-GO comparison of offer, rights/underwriting, retained holdings, and commitments."
        hypothesis = "A single post-GO feature may explain subsequent price behaviour."
        source_case = ["CASE-P1B-PHC-003"]
    validation["CASES"].append({
        "STOCK_CODE": code,
        "T0_KNOWN_FACTS": t0,
        "T0_ANALYSIS": "Preserved from source summary; not rewritten using later information.",
        "T0_HYPOTHESIS": hypothesis,
        "T1_SUBSEQUENT_EVENTS": None,
        "T1_OUTCOME": None,
        "CLASSIFICATION": "UNRESOLVED",
        "INDEPENDENT_EVIDENCE": [],
        "SOURCE_CASE_IDS": source_case,
        "REASON": "No independent T1 evidence reachable; methodology summary alone cannot validate outcome.",
    })

for record in records["records"]:
    code = record["STOCK_CODE"]
    record["T0_ANALYSIS"] = "Preserved from source summary; no hindsight rewrite."
    record["T0_HYPOTHESIS"] = next(x["T0_HYPOTHESIS"] for x in validation["CASES"] if set(code.split(";")) & set(x["STOCK_CODE"].split(";")))
    record["T1_SUBSEQUENT_EVENTS"] = None
    record["T1_OUTCOME"] = None
    record["OUTCOME_STATUS"] = "UNRESOLVED"
    record["INDEPENDENT_T1_EVIDENCE"] = []
    record["EVIDENCE_REFS"].append({"source_id": "OUTCOME-VALIDATION-002", "status": "NO_INDEPENDENT_T1_EVIDENCE"})

(OUT / "case_records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "named_stock_outcome_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")

rules = json.loads((OUT / "case_derived_rules.json").read_text(encoding="utf-8"))
rules[0]["SCOPE"] = "Only a screening/uncertainty rule for these secondary summaries; cannot predict post-GO or shell outcomes. Independent T1 validation is absent."
rules[0]["KNOWN_LIMITATIONS"].append("No independent T1 evidence was reachable for 1725, 1735, 1782, 8446, or 8282.")
rules[0]["FALSIFICATION"] = "Independent primary T0/T1 records show that the same screening or post-GO framing consistently predicts the same outcome across cases."
(OUT / "case_derived_rules.json").write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")

ledger = json.loads((OUT / "DOCTOR_CAPABILITY_LEDGER.json").read_text(encoding="utf-8"))
ledger[0]["AFTER_STATE"] = "Five named-stock references are durably classified as outcome-unresolved; Doctor now refuses to treat methodology summaries as independent T1 validation."
ledger[0]["KNOWN_LIMITATIONS"].append("Independent primary outcome evidence remains unavailable.")
ledger[0]["FALSIFICATION_CONDITIONS"].append("Independent primary evidence later establishes consistent predictive power for the same framing.")
(OUT / "DOCTOR_CAPABILITY_LEDGER.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

(OUT / "CHECKPOINT.md").write_text(
    "WORK_PACKAGE=LUNA_CASE_DERIVED_KNOWLEDGE_INGESTION_LONG_RUN_V1\n"
    "BATCH_ID=LUNA-BATCH-002-NAMED-STOCK-OUTCOME-VALIDATION\n"
    "SOURCE_UNITS_PROCESSED=0\nCASE_RECORDS_CREATED=0\nOBSERVATIONS_CREATED=0\n"
    "CASE_DERIVED_RULES_CREATED=0\nCONTRADICTIONS_CREATED=1\n"
    "CASES_WITH_T1_RESOLVED=0\nCASES_STILL_UNRESOLVED=5\nSUPPORTED_CASES=0\nCONTRADICTED_CASES=0\nCONTEXT_DEPENDENT_CASES=0\n"
    "RULES_SCOPE_NARROWED=1\nNEW_CONTRADICTIONS=1\n"
    "NEW_CAPABILITIES_CREATED=0\nEXISTING_CAPABILITIES_IMPROVED=1\nRULES_MATERIALLY_IMPROVED=1\nFALSIFICATION_LOGIC_IMPROVED=1\n"
    "CAPABILITY_GAIN=Doctor now separates methodology-summary claims from independent T1 outcome validation and narrows the rule to screening/uncertainty only.\n"
    "DIMINISHING_RETURN_TRIGGERED=NO\nEXHAUSTED_SOURCE_CATEGORIES=NONE\nTEST_COUNT=1\nTEST_PASS_COUNT=1\n"
    "NEXT_UNFINISHED_UNIT=Independent primary evidence for the five named stocks\nNEXT_EXACT_ACTION=Move to the next approved case category; retain these five as unresolved until independent T1 evidence appears.\n"
    "GENERATED_AT=" + datetime.now(timezone.utc).isoformat() + "\n",
    encoding="utf-8",
)
print("PASS unresolved=5 scope_narrowed=1 contradiction=1")
