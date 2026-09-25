"""Tests for ZC_DOCTOR_VALIDATION_TARGET_FEASIBILITY_AUDIT_V1."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.doctor.capabilities import CAPABILITIES, LUNA_TARGETS
from app.doctor.feasibility import ROWS, build_report, rank_rows


def test_all_14_targets_covered_and_refs_valid():
    assert {r.target_id for r in ROWS} == {t.target_id for t in LUNA_TARGETS}
    cap_ids = {c.capability_id for c in CAPABILITIES}
    for r in ROWS:
        assert r.capability_id in cap_ids


def test_every_row_has_domains_and_blocker():
    for r in ROWS:
        assert r.required_t0_domains and r.required_t1_domains
        assert r.blocker


def test_ranking_is_deterministic_and_complete():
    rep = build_report()
    assert len(rep.ranked_ids) == 14
    assert len(set(rep.ranked_ids)) == 14
    assert rep.ranked_ids == [r.target_id for r in rank_rows(ROWS)]


def test_top_ranked_is_low_cost_low_risk_full_local_evidence():
    rep = build_report()
    top = next(r for r in ROWS if r.target_id == rep.ranked_ids[0])
    assert top.expected_implementation_cost in ("LOW", "MEDIUM")
    assert top.evidence_availability_risk == "LOW"
    assert top.point_in_time_feasible == "YES"
    assert top.likelihood_of_ready_for_case_validation == "HIGH"


def test_gated_targets_ranked_bottom():
    """19-year-history-dependent targets cannot rank high while Codex gate is closed."""
    rep = build_report()
    assert rep.ranked_ids[-2:] == ["LT-08", "LT-11"]


def test_lt08_failure_class_recorded_without_semantic_weakening():
    lt08 = next(r for r in ROWS if r.target_id == "LT-08")
    assert "FAILURE_CLASS=A" in lt08.blocker  # missing source exposure
    assert "非 C" in lt08.blocker and "非 D" in lt08.blocker
    # semantics NOT weakened: official disclosure + exact alignment still required
    assert lt08.requires_official_disclosure is True
    assert lt08.requires_exact_date_alignment is True


def test_lt09_zero2318_path_is_complete_local_package():
    lt09 = next(r for r in ROWS if r.target_id == "LT-09")
    assert lt09.likelihood_of_ready_for_case_validation == "HIGH"
    assert not lt09.missing_domains
    assert any("02318" in d for d in lt09.currently_available_domains)
    assert lt09.requires_di and lt09.requires_share_capital


def test_codex_gated_history_never_claimed_available():
    for r in ROWS:
        for d in r.currently_available_domains:
            assert "gated" not in d.lower(), (r.target_id, d)


def test_no_semantic_weakening_of_contract_requirements():
    """Rows must not drop requirements the Luna contract demands (e.g. LT-10 media)."""
    lt10 = next(r for r in ROWS if r.target_id == "LT-10")
    assert any("MEDIA" in m for m in lt10.missing_domains)
    assert lt10.evidence_availability_risk == "HIGH"
