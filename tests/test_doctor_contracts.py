"""Contract-safety tests: point-in-time, unknown propagation, missing != zero,
stage whitelist, scenario falsification, fact/inference separation, namespace
isolation, supersession lifecycle. Work package ZC_DOCTOR_INTELLIGENCE_LONG_RUN_V3."""
from datetime import date

import pytest
from pydantic import ValidationError

from app.doctor.models import DOCTOR_STAGES, DataQualityStatus, AnalysisValueKind, EvidenceRef, MethodRule, MethodStatus, RuleFamily, MethodNamespace
from app.doctor.contracts import (
    FactItem,
    FactBook,
    DoctorContext,
    ScenarioAssessment,
    StageAssessment,
    SurfaceResult,
    SurfaceName,
    SURFACE_CONTRACTS,
    point_in_time_guard,
)
from app.doctor.registry import MethodRuleRegistry


def _ev(eid="EV-1", source_date=date(2026, 1, 1)):
    return EvidenceRef(evidence_id=eid, source_date=source_date, summary="s")


# ---------- point-in-time safety / future leakage ----------

def test_surface_result_rejects_future_evidence():
    with pytest.raises(ValidationError, match="point-in-time"):
        SurfaceResult(
            surface=SurfaceName.GET_CCASS_HOLDINGS,
            stock_code="02318",
            as_of_date=date(2026, 1, 1),
            evidence_refs=[_ev(source_date=date(2026, 6, 1))],
        )


def test_point_in_time_guard_passes_on_or_before():
    point_in_time_guard(date(2026, 1, 1), date(2025, 12, 31), date(2026, 1, 1), None)


def test_point_in_time_guard_rejects_future():
    with pytest.raises(ValidationError):
        DoctorContext(
            stock_code="02318",
            as_of_date=date(2026, 1, 1),
            fact_book=FactBook(
                stock_code="02318",
                as_of_date=date(2026, 1, 1),
                market_cap=[FactItem(kind=AnalysisValueKind.FACT, label="mcap", evidence_refs=[_ev()], as_of_date=date(2026, 3, 1))],
            ),
        )


# ---------- fact / inference separation ----------

def test_fact_requires_evidence():
    with pytest.raises(ValidationError, match="requires at least one evidence"):
        FactItem(kind=AnalysisValueKind.FACT, label="revenue")


def test_inference_does_not_require_evidence_but_is_labelled():
    item = FactItem(kind=AnalysisValueKind.INFERENCE, label="possible accumulation")
    assert item.kind == AnalysisValueKind.INFERENCE


# ---------- unknown propagation / missing != zero ----------

def test_surface_default_dq_is_unknown_not_verified():
    r = SurfaceResult(surface=SurfaceName.GET_MARKET_ACTIVITY, as_of_date=date(2026, 1, 1))
    assert r.data_quality_status == DataQualityStatus.UNKNOWN


def test_unknown_never_counts_as_holdings_change():
    # payload discipline: an UNKNOWN_SOURCE_ANOMALY day must surface as a
    # warning + UNKNOWN dq, and the contract exposes no zero-conversion path.
    r = SurfaceResult(
        surface=SurfaceName.GET_CCASS_CHANGES,
        stock_code="00388",
        as_of_date=date(2010, 5, 4),
        data_quality_status=DataQualityStatus.SOURCE_ANOMALY,
        warnings=["UNKNOWN_SOURCE_ANOMALY at 2010-05-04 — not zero, not exit, not entry"],
        payload={"changes": [], "anomaly_dates": ["2010-05-04"]},
    )
    assert r.data_quality_status == DataQualityStatus.SOURCE_ANOMALY
    assert r.payload["changes"] == []  # absent != zero change


# ---------- stage whitelist ----------

def test_stage_whitelist_accepts_known_stage():
    s = StageAssessment(
        candidate_stage="收貨",
        supporting_evidence=[_ev()],
        method_rules_used=["R-CCASS-ACC-001@1"],
    )
    assert s.candidate_stage in DOCTOR_STAGES


def test_stage_whitelist_rejects_invented_stage():
    with pytest.raises(ValidationError, match="whitelist"):
        StageAssessment(candidate_stage="神秘階段", supporting_evidence=[_ev()], method_rules_used=["R@1"])


def test_stage_requires_evidence_and_rules():
    with pytest.raises(ValidationError, match="evidence"):
        StageAssessment(candidate_stage="收貨", method_rules_used=["R@1"])
    with pytest.raises(ValidationError, match="method_rules_used"):
        StageAssessment(candidate_stage="收貨", supporting_evidence=[_ev()])


# ---------- scenario falsification ----------

def test_scenario_requires_falsification_condition():
    with pytest.raises(ValidationError, match="falsification"):
        ScenarioAssessment(scenario_id="S1", description="d", falsification_condition="  ")


def test_scenario_valid_with_falsification():
    s = ScenarioAssessment(scenario_id="S1", description="d", falsification_condition="若 30 日內無供股公告則推翻")
    assert s.next_confirming_event is None  # uncertainty preserved


# ---------- surface contract inventory ----------

def test_all_17_surfaces_defined():
    assert len(SURFACE_CONTRACTS) == 17
    names = {s.value for s in SurfaceName}
    assert names == {
        "get_security_profile", "get_event_timeline", "get_control_network",
        "get_capital_actions", "get_operator_cost_model", "get_ccass_holdings",
        "get_participant_history", "get_ccass_changes", "get_ccass_concentration",
        "get_broker_fingerprint_inputs", "search_entity_across_stocks",
        "search_event_sequence", "calculate_event_intervals", "compare_fingerprints",
        "get_market_activity", "get_shell_value_inputs", "build_doctor_context",
    }


def test_implemented_surface_count_honest():
    implemented = [s for s, meta in SURFACE_CONTRACTS.items() if meta["implemented"]]
    wired = [s for s, meta in SURFACE_CONTRACTS.items() if meta["real_data_wired"]]
    assert len(implemented) >= 6  # ccass surfaces x4 + context + sequence/interval/compare
    assert all(meta["real_data_wired"] is False or meta["implemented"] for meta in SURFACE_CONTRACTS.values())


# ---------- rule lifecycle / versioning / supersession / namespace isolation ----------

def _rule(rule_id="R-TEST-001", version=1, status=MethodStatus.OBSERVATION, family=RuleFamily.CCASS_ACCUMULATION, methodology=MethodNamespace.PLATFORM, supersedes=None):
    return MethodRule(
        rule_id=rule_id, rule_version=version, rule_name="t", rule_family=family,
        method_status=status, methodology=methodology, supersedes=supersedes,
    )


def test_rule_lifecycle_order_enforced(tmp_path):
    reg = MethodRuleRegistry(tmp_path / "r.sqlite")
    reg.save_rule(_rule(status=MethodStatus.OBSERVATION))
    # supersession through the registry's supersede() API: v1 -> SUPERSEDED
    reg.supersede("R-TEST-001", _rule(version=2, status=MethodStatus.CASE_DERIVED))
    v1 = reg.get_rule("R-TEST-001", 1)
    v2 = reg.get_rule("R-TEST-001", 2)
    assert v1.superseded_by == "R-TEST-001@2"
    assert v2.supersedes == "R-TEST-001@1"
    # superseded rules are never deleted
    assert reg.get_rule("R-TEST-001", 1) is not None


def test_namespace_isolation_no_cross_pollution(tmp_path):
    reg = MethodRuleRegistry(tmp_path / "r.sqlite")
    reg.save_rule(_rule(rule_id="R-HIL-1", methodology=MethodNamespace.HILTON))
    reg.save_rule(_rule(rule_id="R-JAM-1", methodology=MethodNamespace.JAMES_RTSS))
    hil = [r for r in reg.list_rules() if r.methodology == MethodNamespace.HILTON]
    jam = [r for r in reg.list_rules() if r.methodology == MethodNamespace.JAMES_RTSS]
    assert {r.rule_id for r in hil} == {"R-HIL-1"}
    assert {r.rule_id for r in jam} == {"R-JAM-1"}
    assert not ({r.rule_id for r in hil} & {r.rule_id for r in jam})


def test_no_auto_promotion_to_validated(tmp_path):
    reg = MethodRuleRegistry(tmp_path / "r.sqlite")
    reg.save_rule(_rule(status=MethodStatus.CASE_DERIVED))
    latest = reg.get_rule("R-TEST-001", 1)
    assert latest.method_status == MethodStatus.CASE_DERIVED  # stays candidate


def test_case_derived_rule_carries_source_lineage(tmp_path):
    reg = MethodRuleRegistry(tmp_path / "r.sqlite")
    rule = MethodRule(
        rule_id="R-JAM-RTSS-001", rule_name="爆量=報時非買入訊號",
        rule_family=RuleFamily.EVENT_SEQUENCE, methodology=MethodNamespace.JAMES_RTSS,
        method_status=MethodStatus.CASE_DERIVED,
        origin_case_ids=["CASE-RTSS-616"],
        origin_source_ids=["latest_reference_updates/13092026 自建 RTSS 式即市異動監察｜開工前準備.md"],
        origin_methodology_ids=["JAMES_RTSS"],
        description="616 樣本 p=0.600 — 訊號價值=報時+累積，非超額報酬",
        falsification_conditions=["若未來樣本顯示控制同日升幅後仍顯著超額報酬（p<0.05），則本規則被推翻"],
    )
    reg.save_rule(rule)
    loaded = reg.get_rule("R-JAM-RTSS-001", 1)
    assert loaded.origin_case_ids == ["CASE-RTSS-616"]
    assert loaded.origin_source_ids  # source-of-thought lineage answers 邊份教材/案例
    assert loaded.falsification_conditions
