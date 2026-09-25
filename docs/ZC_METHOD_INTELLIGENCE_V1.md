# ZC METHOD INTELLIGENCE & RESEARCH SURFACE CONTRACTS — STATUS V1

> Work package `ZC_DOCTOR_INTELLIGENCE_LONG_RUN_V3`, Tracks B + C.
> ZC = secondary research-engineering support; Codex owns production/backfill.
> Date: 2026-09-25. Registry = dev-only `app/data/doctor/doctor_registry.sqlite` (never the Research Store).

## 1. Architecture (binding)

```text
SOURCE KNOWLEDGE (教材/課程摘要/案例/歷史分析/教師方法論)
  → METHOD INTELLIGENCE (app/doctor: MethodRule registry, versioned, supersession-aware)
    → RESEARCH SURFACE CONTRACTS (app/doctor/contracts.py: 17 read-only surfaces)
      → DOCTOR ANALYSIS (FactBook/DoctorContext/Stage/Scenario — evidence assembly only)
```

Doctor reasoning originates ONLY from source knowledge above. ZC invents no hidden framework.

## 2. Method Intelligence — component status

| Component | Status | Evidence |
|---|---|---|
| Rule registry schema (full §6 field set) | IMPLEMENTED + LOCALLY_TESTED | `app/doctor/models.py` MethodRule (474L); tests green |
| Versioning + supersession (never delete) | IMPLEMENTED + LOCALLY_TESTED | `supersede()` sets versioned pointers `id@version` both directions; test `test_rule_lifecycle_order_enforced` |
| Rule lineage (case/source/methodology/validation) | IMPLEMENTED + LOCALLY_TESTED | `answer_lineage_question()` returns source-of-thought chain |
| Lifecycle OBSERVATION→CASE_DERIVED→HYPOTHESIS→EMPIRICALLY_TESTED→VALIDATED/REJECTED/CONTEXT_DEPENDENT→SUPERSEDED | IMPLEMENTED (enum + no-auto-promote test) | promotion requires explicit status change w/ validation_run_ids — never automatic |
| Method namespace isolation (HILTON/IVAN_L/JAMES_RTSS/ELVIS/MJ/CHAU_HIN/MIZUHO_SHUI/PLATFORM) | IMPLEMENTED + LOCALLY_TESTED | isolation test; cross-method synthesis requires explicit meta-rule |
| Rule families | 30 enum values defined (§7 superset) | category existence ≠ validated rule |
| REAL_SOURCE_DERIVED rules seeded | 2 CASE_DERIVED + 1 OBSERVATION | `scripts/zc_seed_rule_candidates.py`: R-JAMES-RTSS-BURST-TIMING-001 (616樣本 p=0.600), R-PLATFORM-5PCT-LINE-001 (02318 DION 生產數據), R-HILTON-STAGE-GATE-001 (框架規則, OBSERVATION) |
| Test fixtures rules | test-only (tmp_path registries) | no fixture leakage into dev registry |

## 3. Research Surface Contracts — inventory

17/17 surfaces defined in `SURFACE_CONTRACTS` (`app/doctor/contracts.py`), each envelope
carries `data_quality_status / evidence_refs / source_system / source_date / as_of_date`;
`SurfaceResult` validator REJECTS future-dated evidence (point-in-time).

| Implemented | Real-data wired | Surfaces |
|---|---|---|
| 8 | 4 | get_ccass_holdings / get_participant_history / get_ccass_changes / get_ccass_concentration (ccass_surfaces.py, local Webb+gap reads, UNKNOWN-safety) |
| 4 | 0 | search_event_sequence / calculate_event_intervals / compare_fingerprints / build_doctor_context (engines exist+tested; production historical wiring awaits Codex §0 readiness) |
| 5 | 0 | get_security_profile / get_event_timeline / get_control_network / get_capital_actions / get_operator_cost_model / get_broker_fingerprint_inputs / search_entity_across_stocks / get_market_activity / get_shell_value_inputs — CONTRACT_ONLY |

Counts: CONTRACT_DEFINED=17, IMPLEMENTED=8+, CONTRACT_ONLY=9, REAL_DATA_WIRED=4 (local dev reads only — NOT production).

## 4. Doctor context / stage / scenario contracts

- `build_doctor_context(stock_code, as_of_date, lookback_years=5)` → `DoctorContext(FactBook)`:
  22 evidence groups (業務/市值/股本/財技/新舊主/人物/GO/供配CB/操作者成本/價量/CCASS/控制權/階段/關鍵日/正反證據/劇本/推翻條件/殼價輸入).
  Assembles evidence; **no hard-coded conclusion**.
- `StageAssessment`: whitelist = DOCTOR_STAGES (19); validator rejects out-of-whitelist stage,
  stage without supporting_evidence, stage without method_rules_used.
- `ScenarioAssessment`: `falsification_condition` mandatory; similarity never becomes prediction.
- Fact/inference separation: `FactItem.kind` ∈ FACT/DERIVED_MEASURE/RULE_OUTPUT/INFERENCE/HYPOTHESIS/UNKNOWN;
  FACT without evidence refs is a validation error.

## 5. Safety contracts (tested)

- Point-in-time: SurfaceResult + DoctorContext validators + `point_in_time_guard`.
- Unknown propagation: default DQ=UNKNOWN; SOURCE_ANOMALY surfaces as warning + empty payload (missing != zero, no exit/entry/accumulation conversion).
- CCASS unknown safety: PositionStatus includes UNKNOWN_SOURCE_ANOMALY / NO_OBSERVATION_YET (models.py).
- same name != same person: IDENTITY_AMBIGUOUS DQ status + fingerprint compare returns UNKNOWN not NO_MATCH on ambiguity (existing tests).

## 6. Test suite

`tests/test_doctor_contracts.py` (18 tests) + `tests/test_doctor_local_engineering.py` (24 tests)
= **42 passed**. Coverage: PIT/future-leakage, FACT-needs-evidence, unknown-default,
missing!=zero, stage whitelist + evidence + rules-cited, scenario falsification,
17-surface inventory, lifecycle/supersession, namespace isolation, no-auto-promotion,
case-derived lineage roundtrip.

## 7. Acceptance (per §23)

```text
RULE_REGISTRY_SCHEMA_PASS=YES
RULE_VERSIONING_PASS=YES
RULE_LINEAGE_PASS=YES
RULE_LIFECYCLE_PASS=YES
METHOD_NAMESPACE_ISOLATION_PASS=YES
UNKNOWN_PROPAGATION_PASS=YES
POINT_IN_TIME_SAFETY_PASS=YES
TEST_SUITE_PASS=YES (42/42)
=> METHOD_INTELLIGENCE_V1_PASS=YES   (knowledge layer; production readiness NOT claimed)

CONTRACTS_DEFINED=YES (17)
DATA_QUALITY_CONTRACT_PASS=YES
EVIDENCE_CONTRACT_PASS=YES
POINT_IN_TIME_CONTRACT_PASS=YES
CCASS_UNKNOWN_SAFETY_PASS=YES
DOCTOR_CONTEXT_CONTRACT_PASS=YES
=> RESEARCH_SURFACE_CONTRACTS_V1_PASS=YES (contracts; real-data wiring gated on Codex mainline)
```

## 8. Next recommended ZC stages

1. Case-derived ingestion workflow (§19): source_document → OBSERVATION → CASE_DERIVED candidate (manual review gate; never auto-VALIDATED).
2. Wire sequence/interval/fingerprint surfaces to Codex's reconciled historical store once SOURCE_RECONCILIATION passes.
3. Per-教材 digest sessions feeding real CASE_DERIVED candidates (Hilton/周顯/渾水 materials).
