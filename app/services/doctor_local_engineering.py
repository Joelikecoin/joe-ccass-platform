"""Offline-first durable engineering for the Doctor Intelligence package.

This module deliberately stores derived acceptance artifacts in a separate
SQLite file.  It does not write source-native or Research Store tables.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from app.services.cross_source_intelligence import (
    CrossSourceIntelligence,
    EvidenceRef,
    EvidenceState,
    EventRecord,
    FingerprintResult,
    IntervalResult,
    SequenceResult,
)


def _stable(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


class DoctorLocalStore:
    """Append-only/idempotent store for local derived acceptance artifacts."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS doctor_artifacts (
                artifact_kind TEXT NOT NULL, artifact_key TEXT NOT NULL,
                payload_json TEXT NOT NULL, lineage_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (artifact_kind, artifact_key))""")
            db.execute("""CREATE TABLE IF NOT EXISTS identity_mappings (
                source_system TEXT NOT NULL, source_issue_id TEXT NOT NULL,
                canonical_security_id TEXT, hk_stock_code TEXT,
                security_name TEXT, valid_from TEXT, valid_to TEXT,
                mapping_status TEXT NOT NULL, mapping_confidence TEXT NOT NULL,
                source_reference TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_system, source_issue_id, valid_from, valid_to))""")
            db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS identity_mappings_natural_key
                ON identity_mappings(source_system, source_issue_id, COALESCE(valid_from, ''), COALESCE(valid_to, ''))""")
            db.execute("""CREATE TABLE IF NOT EXISTS identity_mapping_runs (
                run_id TEXT PRIMARY KEY, code_version TEXT NOT NULL, commit_sha TEXT NOT NULL,
                schema_version TEXT NOT NULL, stage_version TEXT NOT NULL,
                status TEXT NOT NULL, invalidated_from_stage TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

    def put(self, kind: str, key: str, payload: Mapping[str, object], lineage: Sequence[EvidenceRef] = ()) -> bool:
        with sqlite3.connect(self.path) as db:
            cur = db.execute(
                "INSERT OR IGNORE INTO doctor_artifacts (artifact_kind,artifact_key,payload_json,lineage_json) VALUES (?,?,?,?)",
                (kind, key, _stable(payload), _stable([r.__dict__ for r in lineage])),
            )
            return cur.rowcount == 1

    def get(self, kind: str, key: str) -> dict[str, object] | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload_json,lineage_json FROM doctor_artifacts WHERE artifact_kind=? AND artifact_key=?", (kind, key)).fetchone()
        if not row:
            return None
        return {"payload": json.loads(row[0]), "lineage": json.loads(row[1])}

    def count(self, kind: str | None = None) -> int:
        with sqlite3.connect(self.path) as db:
            if kind:
                return int(db.execute("SELECT COUNT(*) FROM doctor_artifacts WHERE artifact_kind=?", (kind,)).fetchone()[0])
            return int(db.execute("SELECT COUNT(*) FROM doctor_artifacts").fetchone()[0])

    def put_identity_mapping(self, mapping: Mapping[str, object]) -> bool:
        required = ("source_system", "source_issue_id", "mapping_status", "mapping_confidence", "source_reference")
        missing = [key for key in required if not str(mapping.get(key, "")).strip()]
        if missing:
            raise ValueError(f"identity mapping missing required fields: {missing}")
        if mapping["mapping_status"] not in {"EXACT", "DATE_BOUNDED", "AMBIGUOUS", "UNRESOLVED"}:
            raise ValueError("unsupported identity mapping status")
        with sqlite3.connect(self.path) as db:
            cur = db.execute("""INSERT OR IGNORE INTO identity_mappings
                (source_system,source_issue_id,canonical_security_id,hk_stock_code,security_name,valid_from,valid_to,mapping_status,mapping_confidence,source_reference)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", tuple(mapping.get(k) for k in (
                    "source_system", "source_issue_id", "canonical_security_id", "hk_stock_code", "security_name",
                    "valid_from", "valid_to", "mapping_status", "mapping_confidence", "source_reference")))
            return cur.rowcount == 1

    def get_identity_mapping(self, source_system: str, source_issue_id: str) -> list[dict[str, object]]:
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT source_system,source_issue_id,canonical_security_id,hk_stock_code,security_name,valid_from,valid_to,mapping_status,mapping_confidence,source_reference FROM identity_mappings WHERE source_system=? AND source_issue_id=? ORDER BY valid_from", (source_system, source_issue_id)).fetchall()
        return [dict(row) for row in rows]

    def record_identity_mapping_run(self, run_id: str, *, code_version: str, commit_sha: str,
                                    schema_version: str, stage_version: str, status: str = "PASS",
                                    invalidated_from_stage: str | None = None) -> bool:
        with sqlite3.connect(self.path) as db:
            cur = db.execute("""INSERT OR IGNORE INTO identity_mapping_runs
                (run_id,code_version,commit_sha,schema_version,stage_version,status,invalidated_from_stage)
                VALUES (?,?,?,?,?,?,?)""", (run_id, code_version, commit_sha, schema_version,
                                                stage_version, status, invalidated_from_stage))
            return cur.rowcount == 1


def persist_sequence(store: DoctorLocalStore, *, security_id: str, result: SequenceResult, lineage: Sequence[EvidenceRef] = ()) -> str:
    key = hashlib.sha256(_stable([security_id, result.matched_event_ids, result.missing_predicates]).encode()).hexdigest()
    store.put("sequence", key, {"security_id": security_id, "matched_event_ids": result.matched_event_ids, "missing_predicates": result.missing_predicates, "evidence_state": result.evidence_state.value}, lineage or result.lineage)
    return key


def query_sequence(store: DoctorLocalStore, key: str) -> dict[str, object] | None:
    return store.get("sequence", key)


def build_interval(*, anchor: date, before: int, after: int, date_semantic: str, calendar: str = "calendar", known_holidays: Iterable[date] | None = None) -> IntervalResult:
    if date_semantic not in {"announcement", "effective", "completion", "settlement", "trade", "holdings", "event"}:
        raise ValueError("unsupported date semantic")
    if calendar == "calendar":
        return CrossSourceIntelligence.interval(anchor=anchor, before=before, after=after, calendar=calendar)
    if calendar != "trading":
        raise ValueError("calendar must be calendar or trading")
    holidays = set(known_holidays or ())
    included = tuple(anchor + timedelta(days=i) for i in range(-before, after + 1) if (anchor + timedelta(days=i)).weekday() < 5 and (anchor + timedelta(days=i)) not in holidays)
    if not included:
        return IntervalResult(anchor, anchor, anchor, calendar, (), EvidenceState.UNKNOWN, ("trading_calendar",))
    # Weekday filtering is useful but cannot certify exchange holidays without a calendar.
    state = EvidenceState.SUPPORTED if known_holidays is not None else EvidenceState.UNKNOWN
    missing = () if known_holidays is not None else ("exchange_holidays",)
    return IntervalResult(anchor, included[0], included[-1], calendar, included, state, missing)


def persist_interval(store: DoctorLocalStore, result: IntervalResult, *, date_semantic: str, lineage: Sequence[EvidenceRef] = ()) -> str:
    key = hashlib.sha256(_stable([result.anchor, result.start, result.end, result.calendar, date_semantic, result.included_dates]).encode()).hexdigest()
    store.put("interval", key, {"anchor": result.anchor, "start": result.start, "end": result.end, "calendar": result.calendar, "date_semantic": date_semantic, "included_dates": result.included_dates, "evidence_state": result.evidence_state.value, "missing_input_ids": result.missing_input_ids}, lineage)
    return key


def build_fingerprint(left: Mapping[str, object], right: Mapping[str, object], *, lineage: Sequence[EvidenceRef] = ()) -> FingerprintResult:
    return CrossSourceIntelligence.fingerprint_compare(dict(left), dict(right), lineage=lineage)


def persist_fingerprint(store: DoctorLocalStore, result: FingerprintResult) -> str:
    key = hashlib.sha256(_stable([result.matched, result.unmatched_left, result.unmatched_right, result.unknown]).encode()).hexdigest()
    store.put("fingerprint", key, {"matched": result.matched, "unmatched_left": result.unmatched_left, "unmatched_right": result.unmatched_right, "unknown": result.unknown, "score": result.score, "label": result.label, "evidence_state": result.evidence_state.value}, result.lineage)
    return key


def normalize_ccass_code(value: object) -> str:
    raw = str(value).strip()
    if not raw.isdigit() or len(raw) > 5:
        raise ValueError(f"invalid HK security code: {value!r}")
    return raw.zfill(5)


def build_historical_ccass_rows(rows: Iterable[Mapping[str, object]], *, source_id: str, source_reference: str) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        code = normalize_ccass_code(row.get("security_code", row.get("stock_code")))
        participant = str(row["participant_id"]).strip()
        trade_date = str(row["trade_date"])
        holding = row["holding"]
        key = f"{trade_date}|{code}|{participant}"
        output.append({"natural_key": key, "trade_date": trade_date, "source_security_code": str(row.get("security_code", row.get("stock_code"))), "normalized_security_code": code, "participant_id": participant, "holding": holding, "source_id": source_id, "source_reference": source_reference})
    return output


def build_historical_ccass_issue_rows(rows: Iterable[Mapping[str, object]], *, source_id: str, source_reference: str) -> list[dict[str, object]]:
    """Build canonical rows from Webb raw ``(issue_id, participant_id, holding, date)``.

    An Enigma issue-to-HK-code mapping is required before a normalized HK code
    can be asserted, so the raw issue identity is retained explicitly and the
    normalized field remains ``None`` rather than being guessed.
    """
    output: list[dict[str, object]] = []
    for row in rows:
        issue_id = str(row["issue_id"]).strip()
        participant = str(row["participant_id"]).strip()
        trade_date = str(row["trade_date"])
        key = f"{trade_date}|issue:{issue_id}|{participant}"
        output.append({"natural_key": key, "trade_date": trade_date, "source_security_code": None, "source_issue_id": issue_id, "normalized_security_code": None, "participant_id": participant, "holding": row["holding"], "source_id": source_id, "source_reference": source_reference})
    return output


def persist_historical_ccass(store: DoctorLocalStore, rows: Iterable[Mapping[str, object]]) -> int:
    count = 0
    for row in rows:
        key = str(row["natural_key"])
        if store.put("historical_ccass", key, dict(row), ()): count += 1
    return count


def field_match_historical(left: Mapping[str, object], right: Mapping[str, object]) -> dict[str, object]:
    fields = ("trade_date", "normalized_security_code", "participant_id", "holding")
    matched = [f for f in fields if left.get(f) == right.get(f)]
    mismatched = [f for f in fields if left.get(f) != right.get(f)]
    return {"fields_compared": fields, "fields_matched": tuple(matched), "fields_mismatched": tuple(mismatched), "match_pass": not mismatched}


def build_stitched_historical_rows(
    rows: Iterable[Mapping[str, object]], *, source_system: str, source_reference: str,
    canonical_security_id: str, hk_stock_code: object, security_name: str,
    source_issue_id: object | None = None, ingested_at: str | None = None,
) -> list[dict[str, object]]:
    """Build provenance-preserving aggregate or participant historical rows.

    ``participant_id`` and ``share_quantity`` remain nullable for aggregate
    dailylog sources; callers must not promote those rows to participant-level
    evidence when the source does not provide participant detail.
    """
    code = normalize_ccass_code(hk_stock_code)
    output: list[dict[str, object]] = []
    for row in rows:
        trade_date = str(row["trade_date"])
        participant = row.get("participant_id")
        quantity = row.get("share_quantity", row.get("holding"))
        source_record_id = str(row.get("source_record_id", f"{source_system}:{source_issue_id or ''}:{trade_date}:{participant or ''}"))
        output.append({
            "natural_key": f"{trade_date}|{code}|{participant or source_record_id}",
            "source_system": source_system, "source_record_id": source_record_id,
            "source_issue_id": str(source_issue_id) if source_issue_id is not None else None,
            "canonical_security_id": canonical_security_id, "hk_stock_code": code,
            "security_name": security_name, "holdings_date": trade_date,
            "participant_identity": participant, "share_quantity": quantity,
            "source_reference": source_reference, "ingested_at": ingested_at,
        })
    return output
