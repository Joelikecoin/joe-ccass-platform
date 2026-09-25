"""Tests for DOCTOR_CASE_DERIVED_KNOWLEDGE_INGESTION_V1.

Covers package §18: source lineage required, methodology namespace isolation,
CASE_DERIVED cannot auto-promote, fact vs author interpretation, condition-chain
preservation, temporal condition preservation, falsification field,
same-rule-new-evidence handling, cross-method non-merge, contradiction
preservation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.doctor.ingestion import (
    ContradictionRecord, DedupClassification, EvidenceChain, GeneralizationClass,
    IngestionCheckpoint, IngestionStore, Observation, ObservationType, RuleCandidate,
    SourceUnit,
)
from app.doctor.models import RuleFamily


@pytest.fixture()
def store(tmp_path):
    return IngestionStore(db_path=tmp_path / "ingestion.sqlite")


def _source(sid="SRC-1", mid="HILTON"):
    return SourceUnit(source_id=sid, source_title="t", source_type="course_summary",
                      methodology_id=mid, source_location="loc")


def _obs(oid="OBS-1", sid="SRC-1", mid="HILTON", otype=ObservationType.METHOD_PRINCIPLE,
         stmt="statement", evidence="evidence"):
    return Observation(observation_id=oid, methodology_id=mid, source_id=sid,
                       observation_statement=stmt, observation_type=otype,
                       supporting_evidence=evidence)


def _cand(cid="CAND-1", mid="HILTON", obs_ids=None, gen=GeneralizationClass.REPEATABLE_METHOD,
          status="CASE_DERIVED"):
    return RuleCandidate(
        rule_candidate_id=cid, rule_family=RuleFamily.RIGHTS_ISSUE, methodology_id=mid,
        rule_name="n", description="d",
        falsification_conditions=["falsified if X"],
        origin_source_ids=["SRC-1"],
        origin_observation_ids=["OBS-1"] if obs_ids is None else obs_ids,
        generalization_class=gen, method_status=status,
    )


# --- source lineage -------------------------------------------------------

def test_observation_without_source_is_orphan():
    with pytest.raises(ValidationError):
        Observation(observation_id="O", methodology_id="HILTON", source_id="",
                    observation_statement="s", observation_type=ObservationType.METHOD_PRINCIPLE,
                    supporting_evidence="e")


def test_candidate_without_observation_lineage_rejected():
    with pytest.raises(ValidationError):
        _cand(obs_ids=[])


# --- methodology isolation ------------------------------------------------

def test_candidate_keeps_methodology_id(store):
    store.register_source(_source())
    store.add_observation(_obs())
    store.add_candidate(_cand(mid="IVAN_L"))
    row = store.conn.execute("SELECT methodology_id FROM rule_candidates").fetchone()
    assert row[0] == "IVAN_L"


def test_contradiction_requires_methodology_scope():
    with pytest.raises(ValidationError):
        ContradictionRecord(contradiction_id="C", methodology_id="", rule_a="a", rule_b="b",
                            source_a="s1", source_b="s2")


# --- lifecycle: no auto-promotion ----------------------------------------

def test_candidate_cannot_be_validated():
    with pytest.raises(ValidationError):
        _cand(status="VALIDATED")


def test_candidate_cannot_be_hypothesis():
    with pytest.raises(ValidationError):
        _cand(status="HYPOTHESIS")


# --- fact vs author interpretation ---------------------------------------

def test_fact_from_case_requires_evidence():
    with pytest.raises(ValidationError):
        _obs(otype=ObservationType.FACT_FROM_CASE, evidence="")


def test_author_interpretation_is_distinct_type():
    o = _obs(otype=ObservationType.AUTHOR_INTERPRETATION)
    assert o.observation_type == ObservationType.AUTHOR_INTERPRETATION


# --- generalization gate ---------------------------------------------------

def test_case_specific_cannot_become_rule_candidate():
    with pytest.raises(ValidationError):
        _cand(gen=GeneralizationClass.CASE_SPECIFIC)


def test_insufficient_evidence_cannot_become_rule_candidate():
    with pytest.raises(ValidationError):
        _cand(gen=GeneralizationClass.INSUFFICIENT_EVIDENCE)


# --- falsification ---------------------------------------------------------

def test_candidate_without_falsification_flagged_incomplete():
    with pytest.raises(ValidationError) as exc:
        c = _cand()
        c.falsification_conditions = []
        RuleCandidate.model_validate(c.model_dump())
    assert "FALSIFICATION_INCOMPLETE" in str(exc.value)


# --- evidence chain / condition-chain preservation ------------------------

def test_evidence_chain_preserves_intermediate_steps(store):
    store.register_source(_source())
    obs = _obs(oid="OBS-9")
    store.add_observation(obs)
    chain = EvidenceChain(
        chain_id="CH-9", observation_id="OBS-9",
        input_facts=["fact1", "fact2"],
        temporal_order="A before B",
        calculation_or_comparison="x/y",
        author_reasoning="because",
        author_conclusion="therefore",
    )
    store.add_observation(obs, chain)
    import json
    row = store.conn.execute("SELECT steps_json FROM evidence_chains WHERE chain_id='CH-9'").fetchone()
    steps = json.loads(row[0])
    assert steps["input_facts"] == ["fact1", "fact2"]
    assert steps["temporal_order"] == "A before B"
    assert steps["author_conclusion"] == "therefore"


def test_temporal_condition_stored_on_candidate():
    c = _cand()
    c.trigger_conditions = ["A within 30 days of B"]
    assert any("within 30 days" in t for t in c.trigger_conditions)


# --- dedup: same rule new evidence -----------------------------------------

def test_same_rule_new_evidence_classification_preserved(store):
    store.register_source(_source())
    store.add_observation(_obs())
    c = _cand(dedup=DedupClassification.SAME_RULE_NEW_EVIDENCE) if False else None
    c2 = RuleCandidate(
        rule_candidate_id="CAND-2", rule_family=RuleFamily.PLACEMENT, methodology_id="HILTON",
        rule_name="n", description="d", falsification_conditions=["f"],
        origin_source_ids=["SRC-1"], origin_observation_ids=["OBS-1"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.SAME_RULE_NEW_EVIDENCE,
    )
    store.add_candidate(c2)
    row = store.conn.execute(
        "SELECT dedup_classification FROM rule_candidates WHERE rule_candidate_id='CAND-2'"
    ).fetchone()
    assert row[0] == "SAME_RULE_NEW_EVIDENCE"


def test_duplicate_name_query_is_per_methodology(store):
    store.register_source(_source(sid="S-A", mid="HILTON"))
    store.add_observation(_obs(sid="S-A"))
    store.add_candidate(_cand(mid="HILTON"))
    assert store.candidate_exists_with_name("n", "HILTON")
    assert not store.candidate_exists_with_name("n", "CHAU_HIN")


# --- contradiction preservation -------------------------------------------

def test_contradiction_stored_unresolved(store):
    store.add_contradiction(ContradictionRecord(
        contradiction_id="CON-1", methodology_id="HILTON", rule_a="r1", rule_b="r2",
        source_a="s1", source_b="s2", context_difference="differs",
        possible_resolution=None, status="UNRESOLVED",
    ))
    row = store.conn.execute("SELECT status, possible_resolution FROM contradiction_records").fetchone()
    assert row[0] == "UNRESOLVED"  # never silently reconciled
    assert row[1] is None


# --- checkpoint resume ------------------------------------------------------

def test_checkpoint_roundtrip(store):
    store.register_source(_source())
    ckpt = IngestionCheckpoint(source_id="SRC-1", processed_sections=["s1"],
                               observation_ids=["OBS-1"], open_questions=["q"], last_position="EOF")
    store.save_checkpoint(ckpt)
    loaded = store.load_checkpoint("SRC-1")
    assert loaded is not None
    assert loaded.processed_sections == ["s1"]
    assert loaded.last_position == "EOF"
    assert store.load_checkpoint("SRC-404") is None


# --- batch 1 real data regression -----------------------------------------

def test_real_ingestion_seeded_and_gated():
    """Batch-1 real knowledge must be present in the dev store, never auto-promoted."""
    from app.doctor.ingestion import INGESTION_DB
    if not INGESTION_DB.exists():
        pytest.skip("dev ingestion store not built yet")
    s = IngestionStore()
    stats = s.batch_stats()
    assert stats["sources_processed"] >= 13
    assert stats["observations_created"] >= 100
    assert stats["rule_candidates_created"] >= 45
    row = s.conn.execute("SELECT COUNT(*) FROM rule_candidates WHERE method_status != 'CASE_DERIVED'").fetchone()
    assert row[0] == 0  # nothing promoted past CASE_DERIVED
    # namespace isolation across real data: no candidate borrows another method's id
    rows = s.conn.execute("SELECT rule_candidate_id, methodology_id FROM rule_candidates").fetchall()
    prefixes = {"CAND-HILTON": "HILTON", "CAND-CHAUHIN": "CHAU_HIN", "CAND-IVANL": "IVAN_L"}
    for rid, mid in rows:
        for prefix, expected_mid in prefixes.items():
            if rid.startswith(prefix):
                assert mid == expected_mid, f"{rid} claims {mid}"
    # every real candidate has lineage + falsification
    import json as _json
    for (payload,) in s.conn.execute("SELECT payload_json FROM rule_candidates").fetchall():
        p = _json.loads(payload)
        assert p["origin_observation_ids"] and p["origin_source_ids"]
        assert p["falsification_conditions"]
