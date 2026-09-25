"""DOCTOR_CASE_DERIVED_KNOWLEDGE_INGESTION_V1 — source knowledge ingestion models.

Pipeline: SOURCE UNIT → OBSERVATION → evidence chain → CASE_DERIVED rule
candidate (never auto-promoted past CASE_DERIVED). Storage = development
ingestion store under app/data/doctor/ (NEVER the production Research Store).

Hard rules encoded here (package §HARD SOURCE RULE, §13):
- every Observation / RuleCandidate carries source lineage (no orphans)
- FACT_FROM_CASE vs AUTHOR_INTERPRETATION are distinct observation types
- generalization classes gate rule candidacy: only POTENTIALLY_GENERALIZABLE
  or REPEATABLE_METHOD may become CASE_DERIVED candidates
- falsification_conditions mandatory on candidates (else FALSIFICATION_INCOMPLETE)
- candidates stop at CASE_DERIVED; promotion is out of scope for ingestion
- cross-methodology synthesis is forbidden (namespace isolation)
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.doctor.models import MethodNamespace, RuleFamily

INGESTION_DB = Path(__file__).resolve().parent.parent / "data" / "doctor" / "doctor_ingestion.sqlite"

MIGRATION_1 = """
CREATE TABLE IF NOT EXISTS source_units (
    source_id TEXT PRIMARY KEY,
    source_title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    methodology_id TEXT NOT NULL,
    source_location TEXT NOT NULL,
    source_date_if_known TEXT,
    source_scope TEXT,
    ingestion_status TEXT NOT NULL DEFAULT 'PENDING'
);
CREATE TABLE IF NOT EXISTS observations (
    observation_id TEXT PRIMARY KEY,
    methodology_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_section TEXT,
    source_quote_or_paraphrase_reference TEXT,
    observation_statement TEXT NOT NULL,
    observation_type TEXT NOT NULL,
    supporting_evidence TEXT NOT NULL,
    contradicting_evidence TEXT,
    generalization_class TEXT,
    UNIQUE(observation_id, methodology_id, source_id)
);
CREATE TABLE IF NOT EXISTS evidence_chains (
    chain_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    steps_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rule_candidates (
    rule_candidate_id TEXT PRIMARY KEY,
    rule_family TEXT NOT NULL,
    methodology_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    dedup_classification TEXT NOT NULL,
    method_status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contradiction_records (
    contradiction_id TEXT PRIMARY KEY,
    methodology_id TEXT NOT NULL,
    rule_a TEXT NOT NULL,
    rule_b TEXT NOT NULL,
    source_a TEXT NOT NULL,
    source_b TEXT NOT NULL,
    context_difference TEXT,
    possible_resolution TEXT,
    status TEXT NOT NULL DEFAULT 'UNRESOLVED'
);
CREATE TABLE IF NOT EXISTS ingestion_checkpoints (
    source_id TEXT PRIMARY KEY,
    checkpoint_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class ObservationType(str, Enum):
    FACT_FROM_CASE = "FACT_FROM_CASE"
    AUTHOR_INTERPRETATION = "AUTHOR_INTERPRETATION"
    METHOD_PRINCIPLE = "METHOD_PRINCIPLE"
    CONDITION = "CONDITION"
    SEQUENCE = "SEQUENCE"
    TIMING_RULE = "TIMING_RULE"
    RISK_WARNING = "RISK_WARNING"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    FALSIFICATION_HINT = "FALSIFICATION_HINT"


class GeneralizationClass(str, Enum):
    CASE_SPECIFIC = "CASE_SPECIFIC"
    POTENTIALLY_GENERALIZABLE = "POTENTIALLY_GENERALIZABLE"
    REPEATABLE_METHOD = "REPEATABLE_METHOD"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DedupClassification(str, Enum):
    NEW_RULE = "NEW_RULE"
    SAME_RULE_NEW_EVIDENCE = "SAME_RULE_NEW_EVIDENCE"
    RULE_VARIANT = "RULE_VARIANT"
    CONTRADICTING_RULE = "CONTRADICTING_RULE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"


class SourceUnit(BaseModel):
    source_id: str
    source_title: str
    source_type: str
    methodology_id: str
    source_location: str
    source_date_if_known: Optional[str] = None
    source_scope: Optional[str] = None
    ingestion_status: str = "PENDING"


class EvidenceChain(BaseModel):
    chain_id: str
    observation_id: str
    input_facts: List[str] = Field(default_factory=list)
    temporal_order: Optional[str] = None
    calculation_or_comparison: Optional[str] = None
    author_reasoning: Optional[str] = None
    author_conclusion: Optional[str] = None


class Observation(BaseModel):
    observation_id: str
    methodology_id: str
    source_id: str
    source_section: Optional[str] = None
    source_quote_or_paraphrase_reference: Optional[str] = None
    observation_statement: str
    observation_type: ObservationType
    supporting_evidence: str
    contradicting_evidence: Optional[str] = None
    generalization_class: Optional[GeneralizationClass] = None

    @model_validator(mode="after")
    def _no_cross_method_orphan(self):
        if not self.source_id:
            raise ValueError("observation without source_id is an orphan (lineage required)")
        if self.observation_type == ObservationType.FACT_FROM_CASE and not self.supporting_evidence:
            raise ValueError("FACT_FROM_CASE requires supporting_evidence")
        return self


class RuleCandidate(BaseModel):
    rule_candidate_id: str
    rule_family: RuleFamily
    methodology_id: str
    rule_name: str
    description: str
    preconditions: List[str] = Field(default_factory=list)
    required_inputs: List[str] = Field(default_factory=list)
    optional_inputs: List[str] = Field(default_factory=list)
    trigger_conditions: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    alternative_explanations: List[str] = Field(default_factory=list)
    output_semantics: Optional[str] = None
    false_positive_conditions: List[str] = Field(default_factory=list)
    false_negative_conditions: List[str] = Field(default_factory=list)
    falsification_conditions: List[str] = Field(default_factory=list)
    origin_case_ids: List[str] = Field(default_factory=list)
    origin_source_ids: List[str] = Field(default_factory=list)
    origin_observation_ids: List[str] = Field(default_factory=list)
    generalization_class: GeneralizationClass
    dedup_classification: DedupClassification = DedupClassification.NEW_RULE
    method_status: str = "CASE_DERIVED"

    @model_validator(mode="after")
    def _ingestion_gates(self):
        if self.method_status != "CASE_DERIVED":
            raise ValueError("ingestion candidates must stop at CASE_DERIVED (no auto-promotion)")
        if not self.falsification_conditions:
            raise ValueError("FALSIFICATION_INCOMPLETE: candidate lacks falsification_conditions")
        if self.generalization_class not in (
            GeneralizationClass.POTENTIALLY_GENERALIZABLE,
            GeneralizationClass.REPEATABLE_METHOD,
        ):
            raise ValueError(
                "only POTENTIALLY_GENERALIZABLE / REPEATABLE_METHOD may become rule candidates; "
                f"got {self.generalization_class}"
            )
        if not self.origin_source_ids or not self.origin_observation_ids:
            raise ValueError("no orphan candidates: origin_source_ids and origin_observation_ids required")
        return self


class ContradictionRecord(BaseModel):
    contradiction_id: str
    methodology_id: str
    rule_a: str
    rule_b: str
    source_a: str
    source_b: str
    context_difference: Optional[str] = None
    possible_resolution: Optional[str] = None
    status: str = "UNRESOLVED"

    @model_validator(mode="after")
    def _same_method_only(self):
        if not self.methodology_id:
            raise ValueError("contradiction records are per-methodology (no cross-method merge)")
        return self


class IngestionCheckpoint(BaseModel):
    source_id: str
    processed_sections: List[str] = Field(default_factory=list)
    observation_ids: List[str] = Field(default_factory=list)
    candidate_rule_ids: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    last_position: Optional[str] = None


def _connect(db_path: Path = INGESTION_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(MIGRATION_1)
    return conn


class IngestionStore:
    """Development knowledge-ingestion store (isolated from Research Store)."""

    def __init__(self, db_path: Path = INGESTION_DB):
        self.db_path = db_path
        self.conn = _connect(db_path)

    def register_source(self, unit: SourceUnit) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO source_units VALUES (?,?,?,?,?,?,?,?)",
            (
                unit.source_id, unit.source_title, unit.source_type, unit.methodology_id,
                unit.source_location, unit.source_date_if_known, unit.source_scope,
                unit.ingestion_status,
            ),
        )
        self.conn.commit()

    def mark_source_status(self, source_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE source_units SET ingestion_status=? WHERE source_id=?", (status, source_id)
        )
        self.conn.commit()

    def add_observation(self, obs: Observation, chain: Optional[EvidenceChain] = None) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                obs.observation_id, obs.methodology_id, obs.source_id, obs.source_section,
                obs.source_quote_or_paraphrase_reference, obs.observation_statement,
                obs.observation_type.value, obs.supporting_evidence, obs.contradicting_evidence,
                obs.generalization_class.value if obs.generalization_class else None,
            ),
        )
        if chain is not None:
            self.conn.execute(
                "INSERT OR REPLACE INTO evidence_chains VALUES (?,?,?)",
                (chain.chain_id, chain.observation_id, chain.model_dump_json()),
            )
        self.conn.commit()

    def add_candidate(self, cand: RuleCandidate) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO rule_candidates VALUES (?,?,?,?,?,?,?,?)",
            (
                cand.rule_candidate_id, cand.rule_family.value, cand.methodology_id,
                cand.rule_name, cand.model_dump_json(), cand.dedup_classification.value,
                cand.method_status, datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def add_contradiction(self, rec: ContradictionRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO contradiction_records VALUES (?,?,?,?,?,?,?,?,?)",
            (
                rec.contradiction_id, rec.methodology_id, rec.rule_a, rec.rule_b,
                rec.source_a, rec.source_b, rec.context_difference, rec.possible_resolution,
                rec.status,
            ),
        )
        self.conn.commit()

    def save_checkpoint(self, ckpt: IngestionCheckpoint) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO ingestion_checkpoints VALUES (?,?,?)",
            (ckpt.source_id, ckpt.model_dump_json(), datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def load_checkpoint(self, source_id: str) -> Optional[IngestionCheckpoint]:
        row = self.conn.execute(
            "SELECT checkpoint_json FROM ingestion_checkpoints WHERE source_id=?", (source_id,)
        ).fetchone()
        return IngestionCheckpoint.model_validate(json.loads(row[0])) if row else None

    def candidate_exists_with_name(self, rule_name: str, methodology_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM rule_candidates WHERE rule_name=? AND methodology_id=?",
            (rule_name, methodology_id),
        ).fetchone()
        return row is not None

    def batch_stats(self) -> dict:
        q = lambda t: self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        return {
            "sources_processed": q("source_units"),
            "observations_created": q("observations"),
            "rule_candidates_created": q("rule_candidates"),
            "contradictions_found": q("contradiction_records"),
        }
