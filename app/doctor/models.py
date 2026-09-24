"""Doctor Method Intelligence — data models (V1).

Isolated namespace. Never mutates the Research Store or Codex backfill state.
Every model exposes honest data-quality semantics: missing != zero.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- Method lifecycle ----------

class MethodStatus(str, Enum):
    OBSERVATION = "OBSERVATION"
    CASE_DERIVED = "CASE_DERIVED"
    HYPOTHESIS = "HYPOTHESIS"
    EMPIRICALLY_TESTED = "EMPIRICALLY_TESTED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    SUPERSEDED = "SUPERSEDED"


class AnalysisValueKind(str, Enum):
    FACT = "FACT"
    DERIVED_MEASURE = "DERIVED_MEASURE"
    RULE_OUTPUT = "RULE_OUTPUT"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


class DataQualityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    SOURCE_ANOMALY = "SOURCE_ANOMALY"
    IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"
    DENOMINATOR_MISSING = "DENOMINATOR_MISSING"


class PositionStatus(str, Enum):
    VALID = "VALID"
    UNKNOWN_SOURCE_ANOMALY = "UNKNOWN_SOURCE_ANOMALY"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    NO_OBSERVATION_YET = "NO_OBSERVATION_YET"


class ResultKind(str, Enum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


# ---------- Rule families ----------

class RuleFamily(str, Enum):
    CONTROL_CHANGE = "CONTROL_CHANGE"
    GO = "GO"
    NON_GO = "NON_GO"
    WHITEWASH = "WHITEWASH"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    PLACEMENT = "PLACEMENT"
    CB = "CB"
    SHARE_CONSOLIDATION = "SHARE_CONSOLIDATION"
    SHARE_SPLIT = "SHARE_SPLIT"
    CAPITAL_STRUCTURE = "CAPITAL_STRUCTURE"
    OPERATOR_COST = "OPERATOR_COST"
    COST_REPAIR = "COST_REPAIR"
    CCASS_ACCUMULATION = "CCASS_ACCUMULATION"
    CCASS_TRANSFER = "CCASS_TRANSFER"
    CCASS_DISTRIBUTION = "CCASS_DISTRIBUTION"
    CCASS_CONCENTRATION = "CCASS_CONCENTRATION"
    SHOOTING_WAREHOUSE = "SHOOTING_WAREHOUSE"
    DARK_NUMBER_CONVERSION = "DARK_NUMBER_CONVERSION"
    PUBLIC_FLOAT = "PUBLIC_FLOAT"
    SUPPLY_DRYNESS = "SUPPLY_DRYNESS"
    BROKER_FINGERPRINT = "BROKER_FINGERPRINT"
    EVENT_SEQUENCE = "EVENT_SEQUENCE"
    EVENT_INTERVAL = "EVENT_INTERVAL"
    RISK_WINDOW = "RISK_WINDOW"
    SHELL_VALUE = "SHELL_VALUE"
    CONTROL_PREMIUM = "CONTROL_PREMIUM"
    STAGE_CLASSIFICATION = "STAGE_CLASSIFICATION"
    SCENARIO = "SCENARIO"
    FALSIFICATION = "FALSIFICATION"


class MethodNamespace(str, Enum):
    """Methodologies from different teachers stay isolated. No synthetic
    cross-framework conclusions without an explicit meta-rule."""
    HILTON = "HILTON"
    IVAN_L = "IVAN_L"
    JAMES_RTSS = "JAMES_RTSS"
    ELVIS = "ELVIS"
    MJ = "MJ"
    CHAU_HIN = "CHAU_HIN"
    MIZUHO_SHUI = "MIZUHO_SHUI"  # 渾水
    PLATFORM = "PLATFORM"  # platform-derived generic rules


DOCTOR_STAGES = (
    "前期部署", "壓價", "收貨", "轉倉", "等股東大會", "等除權", "供股權階段",
    "Last Pay Day後", "等R", "新股出爐", "Settle", "成本修復", "試盤",
    "第一段表演", "二次換手", "震倉", "高位派貨", "局已完成", "失敗／向下炒",
)


# ---------- Evidence ----------

class EvidenceRef(BaseModel):
    evidence_id: str
    kind: AnalysisValueKind = AnalysisValueKind.UNKNOWN
    source_system: Optional[str] = None
    source_date: Optional[date] = None
    retrieved_at: Optional[datetime] = None
    summary: str = ""
    ref: Optional[str] = None  # URL / doc / DB pointer
    data_quality: DataQualityStatus = DataQualityStatus.UNKNOWN


# ---------- Method rule registry model ----------

class MethodRule(BaseModel):
    rule_id: str
    rule_version: int = 1
    rule_name: str
    rule_family: RuleFamily
    description: str = ""

    method_status: MethodStatus = MethodStatus.OBSERVATION
    methodology: MethodNamespace = MethodNamespace.PLATFORM

    origin_case_ids: list[str] = Field(default_factory=list)
    origin_source_ids: list[str] = Field(default_factory=list)
    origin_methodology_ids: list[str] = Field(default_factory=list)

    applicable_market: str = "HK"
    applicable_security_type: Optional[str] = None

    preconditions: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    optional_inputs: list[str] = Field(default_factory=list)

    positive_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    unknown_conditions: list[str] = Field(default_factory=list)

    calculation_logic: Optional[str] = None
    sequence_logic: Optional[str] = None
    timing_logic: Optional[str] = None

    output_type: Optional[str] = None
    output_semantics: Optional[str] = None
    confidence_semantics: Optional[str] = None

    false_positive_conditions: list[str] = Field(default_factory=list)
    false_negative_conditions: list[str] = Field(default_factory=list)
    falsification_conditions: list[str] = Field(default_factory=list)

    first_observed_at: Optional[date] = None
    last_revalidated_at: Optional[date] = None

    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    validation_run_ids: list[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_case_derived(self) -> bool:
        return self.method_status == MethodStatus.CASE_DERIVED


# ---------- Rule execution ----------

class RuleExecutionResult(BaseModel):
    rule_id: str
    rule_version: int
    method_status: MethodStatus

    input_facts: dict[str, Any] = Field(default_factory=dict)
    derived_measures: dict[str, Any] = Field(default_factory=dict)
    supporting_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    unknown_inputs: list[str] = Field(default_factory=list)

    result: ResultKind = ResultKind.UNKNOWN
    result_type: AnalysisValueKind = AnalysisValueKind.RULE_OUTPUT
    confidence_semantics: Optional[str] = None
    falsification_conditions: list[str] = Field(default_factory=list)

    evaluated_at: Optional[datetime] = None
    as_of_date: Optional[date] = None

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


# ---------- Stage / scenario ----------

class StageClassification(BaseModel):
    stock_code: str
    as_of_date: date
    candidate_stage: str  # MUST be in DOCTOR_STAGES
    supporting_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    unknown_inputs: list[str] = Field(default_factory=list)
    method_rules_used: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    scenario_id: str
    description: str
    required_conditions: list[str] = Field(default_factory=list)
    supporting_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    next_confirming_event: Optional[str] = None
    falsification_condition: Optional[str] = None


# ---------- Research surface models (read-only contracts) ----------

class SecurityProfile(BaseModel):
    stock_code: str
    as_of_date: date
    canonical_security_id: Optional[str] = None
    security_name: Optional[str] = None
    former_names: list[str] = Field(default_factory=list)
    listing_date: Optional[date] = None
    market: Optional[str] = None
    board: Optional[str] = None
    issued_shares: Optional[int] = None
    public_float: Optional[int] = None
    market_cap: Optional[float] = None
    nav: Optional[float] = None
    latest_financial_period: Optional[str] = None
    control_persons: list[str] = Field(default_factory=list)
    major_shareholders: list[str] = Field(default_factory=list)
    data_quality: DataQualityStatus = DataQualityStatus.UNKNOWN
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class EventTimelineEntry(BaseModel):
    stock_code: str
    event_type: str
    announcement_date: Optional[date] = None
    effective_date: Optional[date] = None
    completion_date: Optional[date] = None
    trade_date: Optional[date] = None
    estimated_trade_date: Optional[date] = None
    settlement_date: Optional[date] = None
    holdings_date: Optional[date] = None
    record_date: Optional[date] = None
    listing_date: Optional[date] = None
    source_observed_date: Optional[date] = None
    title: str = ""
    source: Optional[str] = None
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class ControlNetwork(BaseModel):
    stock_code: str
    as_of_date: date
    old_controller: Optional[str] = None
    new_controller: Optional[str] = None
    offeror: Optional[str] = None
    beneficial_owner: Optional[str] = None
    directors: list[str] = Field(default_factory=list)
    chairman: Optional[str] = None
    ceo: Optional[str] = None
    company_secretary: Optional[str] = None
    financial_advisor: Optional[str] = None
    placing_agent: Optional[str] = None
    underwriter: Optional[str] = None
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    validity_windows: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    note_same_name_not_same_person: bool = True


class CapitalAction(BaseModel):
    action_type: str  # GO/NON_GO/WHITEWASH/rights/placement/CB/consolidation/split/repurchase/cancellation/mandate
    announcement_date: Optional[date] = None
    raw_terms: dict[str, Any] = Field(default_factory=dict)
    derived: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class CostComponent(BaseModel):
    cost_type: str
    value: Optional[float] = None
    method: Optional[str] = None
    fact_or_estimate: str = "UNKNOWN"  # FACT / ESTIMATE / UNKNOWN
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    confidence: Optional[str] = None


class OperatorCostModel(BaseModel):
    stock_code: str
    as_of_date: date
    components: list[CostComponent] = Field(default_factory=list)
    note_never_mix_statutory_with_inferred: bool = True


class CcassHoldingRow(BaseModel):
    participant_id: str
    participant_name: Optional[str] = None
    share_quantity: Optional[int] = None
    position_status: PositionStatus = PositionStatus.VALID
    data_quality_warning: Optional[str] = None
    source_reference: Optional[str] = None


class CcassHoldingsResult(BaseModel):
    stock_code: str
    requested_date: date
    resolved_source_date: Optional[date] = None
    rows: list[CcassHoldingRow] = Field(default_factory=list)
    data_quality: DataQualityStatus = DataQualityStatus.UNKNOWN
    note_unknown_never_zero: bool = True


class ParticipantHistoryPoint(BaseModel):
    holdings_date: date
    share_quantity: Optional[int] = None
    position_status: PositionStatus = PositionStatus.VALID
    anomaly: Optional[str] = None


class ParticipantHistoryResult(BaseModel):
    stock_code: str
    participant_id: str
    start_date: date
    end_date: date
    points: list[ParticipantHistoryPoint] = Field(default_factory=list)
    anomalies_preserved: bool = True


class CcassChangeRow(BaseModel):
    holdings_date: date
    estimated_trade_date: Optional[date] = None
    participant_id: str
    participant_name: Optional[str] = None
    before: Optional[int] = None
    after: Optional[int] = None
    change: Optional[int] = None
    change_percent: Optional[float] = None


class CcassChangesResult(BaseModel):
    stock_code: str
    start_date: date
    end_date: date
    rows: list[CcassChangeRow] = Field(default_factory=list)
    t2_note: str = "Big Changes date = settlement/holdings-side date; T+2 adjustment explicit"


class CcassConcentration(BaseModel):
    stock_code: str
    holdings_date: date
    issued_shares: Optional[int] = None
    total_in_ccass: Optional[int] = None
    top_1: Optional[int] = None
    top_5: Optional[int] = None
    top_10: Optional[int] = None
    participant_count: Optional[int] = None
    top1_pct_of_issued: Optional[float] = None
    top5_pct_of_issued: Optional[float] = None
    top10_pct_of_issued: Optional[float] = None
    top1_pct_of_ccass: Optional[float] = None
    top5_pct_of_ccass: Optional[float] = None
    top10_pct_of_ccass: Optional[float] = None
    issued_shares_unavailable: bool = False


class BrokerFingerprintInputs(BaseModel):
    stock_code: str
    start_date: date
    end_date: date
    participant_history: list[ParticipantHistoryResult] = Field(default_factory=list)
    large_transfers: list[dict[str, Any]] = Field(default_factory=list)
    entry_exit_dates: list[dict[str, Any]] = Field(default_factory=list)
    concentration_changes: list[dict[str, Any]] = Field(default_factory=list)
    cross_stock_appearances: list[dict[str, Any]] = Field(default_factory=list)
    note_fingerprint_conclusion_belongs_to_method_intelligence: bool = True


class EntityAcrossStocks(BaseModel):
    entity_id: str
    start_date: date
    end_date: date
    matches: list[dict[str, Any]] = Field(default_factory=list)


class EventSequenceMatch(BaseModel):
    sequence_definition: str
    stock_code: str
    matched_events: list[dict[str, Any]] = Field(default_factory=list)
    note_similarity_is_research_prior_not_prediction: bool = True


class EventInterval(BaseModel):
    stock_code: str
    event_a: str
    event_b: str
    interval_calendar_days: Optional[int] = None
    interval_trading_days: Optional[int] = None
    trading_days_status: str = "PARTIAL_OR_UNKNOWN"


class FingerprintComparison(BaseModel):
    target_stock: str
    reference_cases: list[str] = Field(default_factory=list)
    feature_matches: list[dict[str, Any]] = Field(default_factory=list)
    feature_mismatches: list[dict[str, Any]] = Field(default_factory=list)
    unknown_features: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    similarity_is: str = "RESEARCH_PRIOR"


class MarketActivity(BaseModel):
    stock_code: str
    start_date: date
    end_date: date
    rows: list[dict[str, Any]] = Field(default_factory=list)
    large_volume_dates: list[date] = Field(default_factory=list)
    low_liquidity_baseline: Optional[float] = None
    note_no_directional_forecast: bool = True


class ShellValueInputs(BaseModel):
    stock_code: str
    as_of_date: date
    issued_shares: Optional[int] = None
    nav: Optional[float] = None
    earnings: Optional[float] = None
    comparable_go_transactions: list[dict[str, Any]] = Field(default_factory=list)
    note_no_fake_shell_price_when_inputs_missing: bool = True


class DoctorContext(BaseModel):
    stock_code: str
    as_of_date: date
    lookback_years: int = 5
    business: dict[str, Any] = Field(default_factory=dict)
    market_cap: dict[str, Any] = Field(default_factory=dict)
    capital_structure: dict[str, Any] = Field(default_factory=dict)
    financial_engineering_events: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    control_change: dict[str, Any] = Field(default_factory=dict)
    people_network: dict[str, Any] = Field(default_factory=dict)
    go_non_go: list[dict[str, Any]] = Field(default_factory=list)
    rights_issue: list[dict[str, Any]] = Field(default_factory=list)
    placement: list[dict[str, Any]] = Field(default_factory=list)
    operator_cost: dict[str, Any] = Field(default_factory=dict)
    price_turnover: list[dict[str, Any]] = Field(default_factory=list)
    ccass: dict[str, Any] = Field(default_factory=dict)
    stage: Optional[str] = None
    next_key_dates: list[dict[str, Any]] = Field(default_factory=list)
    positive_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    scenarios: list[Scenario] = Field(default_factory=list)
    falsification: list[str] = Field(default_factory=list)
    shell_value_inputs: dict[str, Any] = Field(default_factory=dict)
    data_quality_status: DataQualityStatus = DataQualityStatus.UNKNOWN
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    note_assembles_evidence_not_conclusions: bool = True
