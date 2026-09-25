"""Tests for ZC_DOCTOR_INTELLIGENCE_LONG_RUN_V4 capability consolidation."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.doctor.capabilities import (
    CAPABILITIES, LUNA_TARGETS, RULE_FAMILIES, VALIDATION_GAPS,
    ConfidenceLevel, Capability, inflation_stats, validate_consolidation,
)
from app.doctor.ingestion import IngestionStore, INGESTION_DB


def _all_rule_ids():
    if not INGESTION_DB.exists():
        pytest.skip("dev ingestion store not built")
    s = IngestionStore()
    return [r[0] for r in s.conn.execute("SELECT rule_candidate_id FROM rule_candidates")]


def test_no_orphan_rule_family_against_raw_inventory():
    problems = validate_consolidation(_all_rule_ids())
    assert problems == []


def test_every_capability_has_supporting_rules_and_falsification():
    for c in CAPABILITIES:
        assert c.supporting_rule_ids, c.capability_id
        assert c.falsification_conditions, c.capability_id
        assert c.source_ids, c.capability_id


def test_every_rule_family_has_members_and_purpose():
    for f in RULE_FAMILIES:
        assert f.member_rule_ids
        assert f.shared_analytical_purpose
        assert f.keep_separate_reason


def test_methodology_variants_not_silently_merged():
    """Threshold rules exist separately per methodology and are labelled variants."""
    fam = next(f for f in RULE_FAMILIES if f.rule_family_id == "RF-10")
    assert "CAND-HILTON-THRESHOLD-HUG-001" in fam.member_rule_ids
    assert "CAND-CHAUHIN-THRESHOLD-ASK-001" in fam.member_rule_ids
    assert fam.context_variants, "cross-method relationship must be recorded, not merged"


def test_luna_targets_reference_valid_capability_and_family():
    cap_ids = {c.capability_id for c in CAPABILITIES}
    fam_ids = {f.rule_family_id for f in RULE_FAMILIES}
    for t in LUNA_TARGETS:
        assert t.capability_id in cap_ids, t.target_id
        assert t.rule_family_id in fam_ids, t.target_id


def test_luna_targets_have_falsification_and_outcome_fields():
    for t in LUNA_TARGETS:
        assert t.falsification_trigger
        assert t.support_condition
        assert t.contradiction_condition
        assert t.t1_outcome_fields_required
        assert t.t0_fields_required


def test_validation_status_not_auto_promoted():
    for c in CAPABILITIES:
        assert c.confidence_level in (
            ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
            ConfidenceLevel.PARTIALLY_CASE_SUPPORTED,
        )


def test_capability_model_rejects_auto_promotion():
    with pytest.raises(ValidationError):
        Capability(
            capability_id="CAP-X", capability_name="x", what_doctor_can_now_do="x",
            supporting_rule_families=["RF-01"], supporting_rule_ids=["CAND-HILTON-SUPPLY-INTENT-001"],
            supporting_methodologies=["HILTON"], source_ids=["S"], required_input_data=["d"],
            output_type="RULE_OUTPUT", confidence_level="EMPIRICALLY_TESTED",
            falsification_conditions=["f"],
        )


def test_luna_minimum_case_count_not_invented():
    """Method sources specify no statistical minimum — the layer must not invent one."""
    for t in LUNA_TARGETS:
        assert t.minimum_case_count is None


def test_duplicate_semantic_rule_handling_recorded():
    """Same-rule-new-evidence and variant classifications survive consolidation."""
    fam_spinoff = next(f for f in RULE_FAMILIES if f.rule_family_id == "RF-11")
    assert "CAND-HILTON-SPINOFF-PRESSURE-001" in fam_spinoff.same_rule_new_evidence
    fam_threshold = next(f for f in RULE_FAMILIES if f.rule_family_id == "RF-10")
    assert fam_threshold.context_variants


def test_source_lineage_preserved_after_consolidation():
    """Every capability's rules must still resolve to sources in the ingestion store."""
    if not INGESTION_DB.exists():
        pytest.skip("dev ingestion store not built")
    s = IngestionStore()
    known = {r[0] for r in s.conn.execute("SELECT rule_candidate_id FROM rule_candidates")}
    for c in CAPABILITIES:
        missing = set(c.supporting_rule_ids) - known
        assert not missing, f"{c.capability_id}: rules missing from lineage store {missing}"


def test_inflation_control_counts():
    stats = inflation_stats()
    assert stats["RAW_RULE_COUNT"] == 48
    assert stats["RULE_FAMILY_COUNT"] == 14
    assert stats["DISTINCT_CAPABILITY_COUNT"] == 14
    # rule inflation control: capabilities must be fewer than raw rules
    assert stats["DISTINCT_CAPABILITY_COUNT"] < stats["RAW_RULE_COUNT"]


def test_high_priority_gaps_have_targets():
    """Every HIGH-priority gap capability must have at least one Luna target."""
    high_caps = {g.capability_id for g in VALIDATION_GAPS if g.gap_priority == "HIGH"}
    targeted = {t.capability_id for t in LUNA_TARGETS}
    assert high_caps <= targeted
