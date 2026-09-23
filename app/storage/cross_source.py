"""Append-only Cross-Source V1 persistence on the existing repository DB path."""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from app.services.cross_source_intelligence import (
    Confidence, CrossSourceIntelligence, EntityRecord, EventRecord, EvidenceState,
    EvidenceRef, RelationshipRecord, SecurityRecord,
)
from app.storage.history import NormalizedSnapshotRepository


def _json(value: object) -> str:
    def default(item: object):
        if isinstance(item, date):
            return item.isoformat()
        if is_dataclass(item):
            return asdict(item)
        raise TypeError(type(item).__name__)
    return json.dumps(value, default=default, sort_keys=True)


class CrossSourceRepository:
    """Idempotent append-only records; current data never replaces history."""

    def __init__(self, snapshot_repository: NormalizedSnapshotRepository):
        self.snapshot_repository = snapshot_repository
        with self.snapshot_repository._connect() as connection:  # existing DB/Turso adapter
            connection.execute(
                """CREATE TABLE IF NOT EXISTS cross_source_records (
                    record_id TEXT NOT NULL,
                    record_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_date TEXT,
                    valid_from TEXT,
                    valid_to TEXT,
                    evidence_state TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (record_kind, record_id)
                )"""
            )
            connection.commit()

    def put(self, *, record_id: str, record_kind: str, source_id: str, payload: object,
            source_date: date | None = None, valid_from: date | None = None,
            valid_to: date | None = None, evidence_state: str = "UNKNOWN") -> None:
        with self.snapshot_repository._connect() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO cross_source_records
                (record_id, record_kind, source_id, source_date, valid_from, valid_to,
                 evidence_state, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (record_id, record_kind, source_id,
                 source_date.isoformat() if source_date else None,
                 valid_from.isoformat() if valid_from else None,
                 valid_to.isoformat() if valid_to else None,
                 evidence_state, _json(payload)),
            )
            connection.commit()

    def put_many(self, records: Iterable[dict[str, object]]) -> int:
        count = 0
        for record in records:
            self.put(**record)
            count += 1
        return count

    def records(self, record_kind: str | None = None) -> list[dict[str, object]]:
        with self.snapshot_repository._connect() as connection:
            if record_kind:
                rows = connection.execute("SELECT * FROM cross_source_records WHERE record_kind = ? ORDER BY created_at, record_id", (record_kind,)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM cross_source_records ORDER BY created_at, record_id").fetchall()
        return [dict(row) for row in rows]

    def load_engine(self) -> CrossSourceIntelligence:
        entities: list[EntityRecord] = []; securities: list[SecurityRecord] = []
        relationships: list[RelationshipRecord] = []; events: list[EventRecord] = []
        for row in self.records():
            payload = json.loads(str(row["payload_json"]))
            kind = str(row["record_kind"])
            payload = _restore(payload)
            if kind == "entity":
                payload["confidence"] = Confidence(payload.get("confidence", "UNRESOLVED")); payload["lineage"] = tuple(EvidenceRef(**x) for x in payload.get("lineage", ())); entities.append(EntityRecord(**payload))
            elif kind == "security": securities.append(SecurityRecord(**payload))
            elif kind == "relationship":
                payload["confidence"] = Confidence(payload["confidence"]); payload["evidence_state"] = EvidenceState(payload["evidence_state"]); payload["lineage"] = tuple(EvidenceRef(**x) for x in payload.get("lineage", ())); relationships.append(RelationshipRecord(**payload))
            elif kind == "event":
                payload["evidence_state"] = EvidenceState(payload["evidence_state"]); payload["lineage"] = tuple(EvidenceRef(**x) for x in payload.get("lineage", ())); events.append(EventRecord(**payload))
        return CrossSourceIntelligence(entities=entities, securities=securities, relationships=relationships, events=events)


def _restore(value):
    if isinstance(value, dict):
        return {key: _restore(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_restore(item) for item in value]
    if isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-":
        try:
            return date.fromisoformat(value)
        except ValueError:
            return value
    return value


def adapt_ccass_response(response) -> list[dict[str, object]]:
    """Convert existing holdings response into canonical source records."""
    metadata = response.metadata
    security_id = f"security:{metadata.code}"
    records: list[dict[str, object]] = [{
        "record_id": security_id, "record_kind": "security", "source_id": metadata.source_name,
        "source_date": metadata.holdings_date, "evidence_state": "SUPPORTED",
        "payload": {"security_id": security_id, "market": "HK", "stock_code": metadata.code,
                    "issue_id": str(metadata.issue_id), "listed_class": None, "canonical_name": metadata.name,
                    "valid_from": None, "valid_to": None, "source_mappings": ()},
    }]
    for row in response.holdings:
        entity_id = f"participant:{row.participant_id}"
        records.append({"record_id": entity_id, "record_kind": "entity", "source_id": metadata.source_name,
                        "source_date": metadata.holdings_date, "evidence_state": "SUPPORTED",
                        "payload": {"entity_id": entity_id, "entity_type": "PARTICIPANT", "canonical_name": row.participant,
                                    "source_id": metadata.source_name, "source_native_id": row.participant_id,
                                    "valid_from": metadata.holdings_date, "valid_to": None, "observed_at": metadata.holdings_date,
                                    "confidence": "EXACT", "status": "ACTIVE", "lineage": ()}})
        relationship_id = f"holding:{metadata.code}:{metadata.holdings_date}:{row.participant_id}"
        records.append({"record_id": relationship_id, "record_kind": "relationship", "source_id": metadata.source_name,
                        "source_date": metadata.holdings_date, "evidence_state": "SUPPORTED",
                        "payload": {"relationship_id": relationship_id, "from_entity_id": entity_id, "to_entity_id": security_id,
                                    "relationship_type": "PARTICIPANT_HOLDING", "valid_from": metadata.holdings_date,
                                    "valid_to": None, "observed_at": metadata.holdings_date, "confidence": "EXACT",
                                    "evidence_state": "SUPPORTED", "lineage": ()}})
    return records


def adapt_stock_events_response(response) -> list[dict[str, object]]:
    """Convert existing normalized stock-event rows without inventing dates."""
    code = response.metadata.code
    security_id = f"security:{code}"
    output: list[dict[str, object]] = []
    for row in response.stock_events:
        if not isinstance(row.event_date, date) or not str(row.title).strip():
            continue
        event_id = row.event_id or f"{code}:{row.event_date}:{row.title}"
        output.append({
            "record_id": event_id,
            "record_kind": "event",
            "source_id": row.source,
            "source_date": row.event_date,
            "evidence_state": "SUPPORTED",
            "payload": {
                "event_id": event_id, "event_type": row.event_type or "UNCLASSIFIED",
                "security_id": security_id, "related_entity_ids": (),
                "announcement_date": row.event_date, "effective_date": None,
                "completion_date": None, "settlement_date": None, "holdings_date": None,
                "trade_date": None, "source_observed_at": response.metadata.fetched_at.date(),
                "evidence_state": "SUPPORTED", "lineage": (),
            },
        })
    return output
