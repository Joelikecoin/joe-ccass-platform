from __future__ import annotations

import json
from datetime import UTC, date, datetime

from app.models import IntelligenceEventRow, IntelligenceEventsMetadata, IntelligenceEventsResponse
from app.storage.history import NormalizedSnapshotRepository


class IntelligenceEventRepository:
    """Evidence cache for the unified event layer.

    Events are persisted as one snapshot row per (stock, coverage window) —
    the same payload_json pattern the fundamentals table uses. Row-level
    statement persistence over remote Turso costs one HTTP round trip per
    statement, which starves the free container; a snapshot is one upsert.
    """

    def __init__(self, repository: NormalizedSnapshotRepository):
        self.repository = repository

    def save(self, response: IntelligenceEventsResponse) -> None:
        metadata = response.metadata
        if metadata.coverage_start is None or metadata.coverage_end is None:
            return
        payload = [json.loads(event.model_dump_json()) for event in response.events]
        with self.repository._transaction() as connection:
            connection.execute("INSERT INTO stocks(code, current_name, market, created_at, updated_at) VALUES (?, NULL, 'HK', ?, ?) ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at", (metadata.code, datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
            connection.execute(
                """
                INSERT INTO intelligence_event_snapshots(
                    stock_code, coverage_start, coverage_end, event_count, events_json, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(stock_code, coverage_start, coverage_end) DO UPDATE SET
                    event_count=excluded.event_count,
                    events_json=excluded.events_json,
                    generated_at=excluded.generated_at
                """,
                (
                    metadata.code,
                    metadata.coverage_start.isoformat(),
                    metadata.coverage_end.isoformat(),
                    metadata.event_count,
                    json.dumps(payload, ensure_ascii=False),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def load(self, stock_code: str, *, start_date: date | None = None, end_date: date | None = None) -> list[IntelligenceEventRow]:
        with self.repository._connect() as connection:
            row = connection.execute(
                """
                SELECT events_json, coverage_start, coverage_end
                FROM intelligence_event_snapshots
                WHERE stock_code = ?
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (stock_code,),
            ).fetchone()
        if row is None:
            return []
        events = [IntelligenceEventRow.model_validate(item) for item in json.loads(row[0])]
        if start_date is not None:
            events = [event for event in events if event.announce_date >= start_date]
        if end_date is not None:
            events = [event for event in events if event.announce_date <= end_date]
        return events
