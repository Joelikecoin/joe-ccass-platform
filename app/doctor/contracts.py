"""Research Surface Contracts + Doctor Context/Stage/Scenario contracts.

ZC Doctor Intelligence track (work package ZC_DOCTOR_INTELLIGENCE_LONG_RUN_V3).
Isolated from Codex's Webb source-reconciliation/backfill assets: this module
defines READ-ONLY contract shapes only; it never mutates staging, source DBs,
or the production Research Store.

Contract principles (binding):
- Every surface result carries data_quality_status, evidence_refs,
  source_system, source_date, as_of_date.
- Missing != zero: absence of observation is UNKNOWN, never 0/exit/entry.
- UNKNOWN_SOURCE_ANOMALY never silently converts to a position change.
- Point-in-time safety: every query accepts as_of_date; no future leakage;
  historical identity (name/controller/issued shares/participant) must be
  valid FOR that date or carried as UNKNOWN.
- Doctor outputs separate FACT / DERIVED_MEASURE / RULE_OUTPUT / INFERENCE /
  HYPOTHESIS / UNKNOWN.
- No stage without evidence; no scenario without falsification condition.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from app.doctor.models import (
    AnalysisValueKind,
    DataQualityStatus,
    DOCTOR_STAGES,
    EvidenceRef,
    MethodNamespace,
)

__all__ = [
    "SurfaceName",
    "SURFACE_CONTRACTS",
    "SurfaceResult",
    "DoctorContext",
    "StageAssessment",
    "ScenarioAssessment",
    "FactBook",
    "point_in_time_guard",
]


# ---------------------------------------------------------------------------
# Track C — the 17 read-only research surface contracts
# ---------------------------------------------------------------------------

class SurfaceName(str, Enum):
    GET_SECURITY_PROFILE = "get_security_profile"
    GET_EVENT_TIMELINE = "get_event_timeline"
    GET_CONTROL_NETWORK = "get_control_network"
    GET_CAPITAL_ACTIONS = "get_capital_actions"
    GET_OPERATOR_COST_MODEL = "get_operator_cost_model"
    GET_CCASS_HOLDINGS = "get_ccass_holdings"
    GET_PARTICIPANT_HISTORY = "get_participant_history"
    GET_CCASS_CHANGES = "get_ccass_changes"
    GET_CCASS_CONCENTRATION = "get_ccass_concentration"
    GET_BROKER_FINGERPRINT_INPUTS = "get_broker_fingerprint_inputs"
    SEARCH_ENTITY_ACROSS_STOCKS = "search_entity_across_stocks"
    SEARCH_EVENT_SEQUENCE = "search_event_sequence"
    CALCULATE_EVENT_INTERVALS = "calculate_event_intervals"
    COMPARE_FINGERPRINTS = "compare_fingerprints"
    GET_MARKET_ACTIVITY = "get_market_activity"
    GET_SHELL_VALUE_INPUTS = "get_shell_value_inputs"
    BUILD_DOCTOR_CONTEXT = "build_doctor_context"


# surface -> (required params beyond stock/as_of, implemented status)
SURFACE_CONTRACTS: dict[SurfaceName, dict[str, Any]] = {
    SurfaceName.GET_SECURITY_PROFILE: {
        "params": {}, "implemented": False, "real_data_wired": False,
        "notes": "Point-in-time security identity; name/controller valid-for-date.",
    },
    SurfaceName.GET_EVENT_TIMELINE: {
        "params": {"lookback_years": 5}, "implemented": False, "real_data_wired": False,
        "notes": "Unified events with evidence refs per item.",
    },
    SurfaceName.GET_CONTROL_NETWORK: {
        "params": {}, "implemented": False, "real_data_wired": False,
        "notes": "Controllers / concert parties / beneficial-owner candidates. participant != beneficial owner.",
    },
    SurfaceName.GET_CAPITAL_ACTIONS: {
        "params": {"lookback_years": 5}, "implemented": False, "real_data_wired": False,
        "notes": "供股/配股/CB/合股/拆股/全購 with effective vs announce dates.",
    },
    SurfaceName.GET_OPERATOR_COST_MODEL: {
        "params": {}, "implemented": False, "real_data_wired": False,
        "notes": "Operator cost inputs; every number a DERIVED_MEASURE with formula lineage.",
    },
    SurfaceName.GET_CCASS_HOLDINGS: {
        "params": {"holdings_date": None}, "implemented": True, "real_data_wired": True,
        "notes": "app/doctor/ccass_surfaces.py CcassArchive — local Webb/gap reads; UNKNOWN on anomaly.",
    },
    SurfaceName.GET_PARTICIPANT_HISTORY: {
        "params": {"participant_id": None, "start": None, "end": None}, "implemented": True, "real_data_wired": True,
        "notes": "ccass_surfaces.py; identity ambiguous flag preserved.",
    },
    SurfaceName.GET_CCASS_CHANGES: {
        "params": {"start": None, "end": None}, "implemented": True, "real_data_wired": True,
        "notes": "ccass_surfaces.py; NO_OBSERVATION_YET preserved, never zero.",
    },
    SurfaceName.GET_CCASS_CONCENTRATION: {
        "params": {"holdings_date": None}, "implemented": True, "real_data_wired": True,
        "notes": "ccass_surfaces.py; DENOMINATOR_MISSING when issued shares unknown for date.",
    },
    SurfaceName.GET_BROKER_FINGERPRINT_INPUTS: {
        "params": {}, "implemented": False, "real_data_wired": False,
        "notes": "Feeds fingerprint compare; same name != same person discipline.",
    },
    SurfaceName.SEARCH_ENTITY_ACROSS_STOCKS: {
        "params": {"entity": None}, "implemented": False, "real_data_wired": False,
        "notes": "Cross-stock entity co-occurrence; namespace-scoped.",
    },
    SurfaceName.SEARCH_EVENT_SEQUENCE: {
        "params": {"sequence": None}, "implemented": True, "real_data_wired": False,
        "notes": "Sequence engine exists (tests test_sequence_*); not yet wired to production historical store.",
    },
    SurfaceName.CALCULATE_EVENT_INTERVALS: {
        "params": {"events": None}, "implemented": True, "real_data_wired": False,
        "notes": "Calendar/trading intervals; partial-knowledge -> UNKNOWN.",
    },
    SurfaceName.COMPARE_FINGERPRINTS: {
        "params": {"left": None, "right": None}, "implemented": True, "real_data_wired": False,
        "notes": "ResultKind MATCH/NO_MATCH/PARTIAL/UNKNOWN; similarity != prediction.",
    },
    SurfaceName.GET_MARKET_ACTIVITY: {
        "params": {"lookback_days": None}, "implemented": False, "real_data_wired": False,
        "notes": "Price/turnover; tape today-only caveat labelled.",
    },
    SurfaceName.GET_SHELL_VALUE_INPUTS: {
        "params": {}, "implemented": False, "real_data_wired": False,
        "notes": "Shell-value inputs only; never a baked valuation.",
    },
    SurfaceName.BUILD_DOCTOR_CONTEXT: {
        "params": {"lookback_years": 5}, "implemented": True, "real_data_wired": False,
        "notes": "DoctorContext assembly defined below; evidence assembly, no hard-coded conclusion.",
    },
}


class SurfaceResult(BaseModel):
    """Envelope every surface must return. Missing != zero."""
    surface: SurfaceName
    stock_code: Optional[str] = None
    as_of_date: date
    source_system: str = "UNKNOWN"
    source_date: Optional[date] = None
    data_quality_status: DataQualityStatus = DataQualityStatus.UNKNOWN
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_future_leakage(self) -> "SurfaceResult":
        for ref in self.evidence_refs:
            if ref.source_date is not None and ref.source_date > self.as_of_date:
                raise ValueError(
                    f"point-in-time violation: evidence {ref.evidence_id} source_date "
                    f"{ref.source_date} is after as_of_date {self.as_of_date}"
                )
        return self


def point_in_time_guard(as_of_date: date, *dates: Optional[date]) -> None:
    """Raise on any date later than as_of_date. No future leakage."""
    for d in dates:
        if d is not None and d > as_of_date:
            raise ValueError(f"point-in-time violation: {d} > as_of_date {as_of_date}")


# ---------------------------------------------------------------------------
# Track B — Doctor context / stage / scenario contracts
# ---------------------------------------------------------------------------

class FactItem(BaseModel):
    """Fact/inference separation at the item level."""
    kind: AnalysisValueKind
    label: str
    value: Any = None
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    as_of_date: Optional[date] = None
    note: str = ""

    @model_validator(mode="after")
    def _facts_need_evidence(self) -> "FactItem":
        if self.kind == AnalysisValueKind.FACT and not self.evidence_refs:
            raise ValueError(f"FACT '{self.label}' requires at least one evidence ref")
        return self


class FactBook(BaseModel):
    """Grouped evidence assembly for one security at one point in time."""
    stock_code: str
    as_of_date: date
    business: list[FactItem] = Field(default_factory=list)
    market_cap: list[FactItem] = Field(default_factory=list)
    share_capital: list[FactItem] = Field(default_factory=list)
    corporate_actions: list[FactItem] = Field(default_factory=list)
    event_timeline: list[FactItem] = Field(default_factory=list)
    new_controller: list[FactItem] = Field(default_factory=list)
    old_controller: list[FactItem] = Field(default_factory=list)
    key_persons: list[FactItem] = Field(default_factory=list)
    go_non_go_whitewash: list[FactItem] = Field(default_factory=list)
    rights_issue_placement_cb: list[FactItem] = Field(default_factory=list)
    operator_cost: list[FactItem] = Field(default_factory=list)
    price_turnover: list[FactItem] = Field(default_factory=list)
    ccass_holdings: list[FactItem] = Field(default_factory=list)
    control_and_float: list[FactItem] = Field(default_factory=list)
    current_stage_evidence: list[FactItem] = Field(default_factory=list)
    next_key_dates: list[FactItem] = Field(default_factory=list)
    positive_evidence: list[FactItem] = Field(default_factory=list)
    negative_evidence: list[FactItem] = Field(default_factory=list)
    scenarios: list[FactItem] = Field(default_factory=list)
    falsification_conditions: list[FactItem] = Field(default_factory=list)
    shell_value_inputs: list[FactItem] = Field(default_factory=list)

    def all_items(self) -> list[FactItem]:
        items: list[FactItem] = []
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, list):
                items.extend(value)
        return items


class DoctorContext(BaseModel):
    """build_doctor_context(stock_code, as_of_date, lookback_years=5) result.

    Assembles evidence. Does NOT hard-code a final conclusion.
    """
    stock_code: str
    as_of_date: date
    lookback_years: int = 5
    fact_book: FactBook
    data_quality_status: DataQualityStatus = DataQualityStatus.UNKNOWN
    unknown_inputs: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_future(self) -> "DoctorContext":
        point_in_time_guard(self.as_of_date, *(i.as_of_date for i in self.fact_book.all_items() if i.as_of_date))
        return self


class StageAssessment(BaseModel):
    """Stage classification. Whitelist = DOCTOR_STAGES. No stage without evidence."""
    candidate_stage: str
    supporting_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    unknown_inputs: list[str] = Field(default_factory=list)
    method_rules_used: list[str] = Field(default_factory=list)  # rule_id@version
    falsification_conditions: list[str] = Field(default_factory=list)
    methodology: Optional[MethodNamespace] = None

    @model_validator(mode="after")
    def _stage_in_whitelist_and_evidenced(self) -> "StageAssessment":
        if self.candidate_stage not in DOCTOR_STAGES:
            raise ValueError(f"stage '{self.candidate_stage}' not in DOCTOR_STAGES whitelist")
        if not self.supporting_evidence:
            raise ValueError("no stage without evidence: supporting_evidence is empty")
        if not self.method_rules_used:
            raise ValueError("stage must cite method_rules_used (rule_id@version)")
        return self


class ScenarioAssessment(BaseModel):
    """Scenario output. Similarity != prediction; falsification mandatory."""
    scenario_id: str
    description: str
    required_conditions: list[str] = Field(default_factory=list)
    supporting_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    next_confirming_event: Optional[str] = None
    falsification_condition: str  # mandatory — no unfalsifiable scenario

    @model_validator(mode="after")
    def _falsifiable(self) -> "ScenarioAssessment":
        if not self.falsification_condition.strip():
            raise ValueError("scenario requires a non-empty falsification_condition")
        return self
