"""Method Rule Registry — isolated SQLite development namespace.

Never mutates the production Research Store. Versioned, supersession-aware,
lineage-tracking, methodology-namespace isolated.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from app.doctor.models import MethodRule, MethodStatus

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "doctor" / "doctor_registry.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS method_rules (
    rule_id TEXT NOT NULL,
    rule_version INTEGER NOT NULL,
    payload TEXT NOT NULL,
    rule_family TEXT NOT NULL,
    method_status TEXT NOT NULL,
    methodology TEXT NOT NULL,
    supersedes TEXT,
    superseded_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (rule_id, rule_version)
);
CREATE TABLE IF NOT EXISTS rule_lineage (
    rule_id TEXT NOT NULL,
    rule_version INTEGER NOT NULL,
    lineage_kind TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    PRIMARY KEY (rule_id, rule_version, lineage_kind, ref_id)
);
CREATE INDEX IF NOT EXISTS ix_mr_family ON method_rules(rule_family);
CREATE INDEX IF NOT EXISTS ix_mr_status ON method_rules(method_status);
CREATE INDEX IF NOT EXISTS ix_mr_methodology ON method_rules(methodology);
"""


class MethodRuleRegistry:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = str(db_path)
        con = self._con()
        con.executescript(SCHEMA)
        con.close()

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def save_rule(self, rule: MethodRule) -> MethodRule:
        if rule.created_at is None:
            rule.created_at = datetime.now(UTC)
        rule.updated_at = datetime.now(UTC)
        payload = rule.model_dump_json()
        with self._con() as con:
            con.execute(
                "INSERT OR REPLACE INTO method_rules(rule_id,rule_version,payload,rule_family,method_status,methodology,supersedes,superseded_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (rule.rule_id, rule.rule_version, payload, rule.rule_family.value, rule.method_status.value, rule.methodology.value, rule.supersedes, rule.superseded_by, rule.created_at.isoformat(), rule.updated_at.isoformat()),
            )
            for kind, refs in (
                ("positive", rule.positive_evidence),
                ("contradicting", rule.contradicting_evidence),
                ("validation", rule.validation_run_ids),
                ("case", rule.origin_case_ids),
                ("source", rule.origin_source_ids),
                ("methodology", rule.origin_methodology_ids),
            ):
                for ref in refs:
                    ref_id = ref if isinstance(ref, str) else getattr(ref, "evidence_id", str(ref))
                    con.execute(
                        "INSERT OR IGNORE INTO rule_lineage(rule_id,rule_version,lineage_kind,ref_id) VALUES(?,?,?,?)",
                        (rule.rule_id, rule.rule_version, kind, str(ref_id)),
                    )
        return rule

    def get_rule(self, rule_id: str, version: Optional[int] = None) -> Optional[MethodRule]:
        with self._con() as con:
            if version is None:
                row = con.execute(
                    "SELECT payload FROM method_rules WHERE rule_id=? ORDER BY rule_version DESC LIMIT 1",
                    (rule_id,),
                ).fetchone()
            else:
                row = con.execute(
                    "SELECT payload FROM method_rules WHERE rule_id=? AND rule_version=?",
                    (rule_id, version),
                ).fetchone()
        return MethodRule.model_validate_json(row["payload"]) if row else None

    def list_rules(self, family: Optional[str] = None, status: Optional[str] = None,
                   methodology: Optional[str] = None) -> list[MethodRule]:
        q = "SELECT payload FROM method_rules WHERE 1=1"
        params: list[str] = []
        if family:
            q += " AND rule_family=?"
            params.append(family)
        if status:
            q += " AND method_status=?"
            params.append(status)
        if methodology:
            q += " AND methodology=?"
            params.append(methodology)
        q += " ORDER BY rule_id, rule_version"
        with self._con() as con:
            rows = con.execute(q, params).fetchall()
        return [MethodRule.model_validate_json(r["payload"]) for r in rows]

    def lineage_refs(self, rule_id: str, version: Optional[int] = None) -> dict[str, list[str]]:
        rule = self.get_rule(rule_id, version)
        if rule is None:
            return {}
        with self._con() as con:
            q = "SELECT lineage_kind, ref_id FROM rule_lineage WHERE rule_id=?"
            params: list[object] = [rule_id]
            if version is not None:
                q += " AND rule_version=?"
                params.append(version)
            rows = con.execute(q, params).fetchall()
        out: dict[str, list[str]] = {}
        for row in rows:
            out.setdefault(row["lineage_kind"], []).append(row["ref_id"])
        return out

    def supersede(self, old_rule_id: str, new_rule: MethodRule) -> MethodRule:
        old = self.get_rule(old_rule_id)
        if old is not None:
            old.method_status = MethodStatus.SUPERSEDED
            old.superseded_by = f"{new_rule.rule_id}@{new_rule.rule_version}"
            self.save_rule(old)
            new_rule.supersedes = f"{old.rule_id}@{old.rule_version}"
        else:
            new_rule.supersedes = old_rule_id
        return self.save_rule(new_rule)

    def answer_lineage_question(self, rule_id: str) -> dict:
        """「呢個判斷係由邊幾個案例學返嚟？」— traceable evidence answer."""
        rule = self.get_rule(rule_id)
        if rule is None:
            return {"rule_id": rule_id, "found": False}
        lineage = self.lineage_refs(rule.rule_id, rule.rule_version)
        return {
            "rule_id": rule.rule_id,
            "rule_version": rule.rule_version,
            "method_status": rule.method_status.value,
            "found": True,
            "origin_cases": rule.origin_case_ids,
            "lineage": lineage,
            "positive_evidence": [e.model_dump(mode="json") for e in rule.positive_evidence],
            "contradicting_evidence": [e.model_dump(mode="json") for e in rule.contradicting_evidence],
            "validation_run_ids": rule.validation_run_ids,
            "supersedes": rule.supersedes,
            "superseded_by": rule.superseded_by,
        }
