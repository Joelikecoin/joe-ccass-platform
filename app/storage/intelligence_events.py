from __future__ import annotations

from datetime import UTC, date, datetime

from app.models import IntelligenceEventRow, IntelligenceEventsMetadata, IntelligenceEventsResponse
from app.storage.history import NormalizedSnapshotRepository


class IntelligenceEventRepository:
    BATCH_SIZE = 25  # remote-Turso writes are one HTTP round trip per statement; single giant transactions kill the free container

    def __init__(self, repository: NormalizedSnapshotRepository):
        self.repository = repository

    def save(self, response: IntelligenceEventsResponse) -> None:
        now = datetime.now(UTC).isoformat()
        rows = list(response.events)
        for start in range(0, len(rows), self.BATCH_SIZE):
            self._save_batch(response.metadata.code, now, rows[start : start + self.BATCH_SIZE])

    def _save_batch(self, code: str, now: str, batch: list[IntelligenceEventRow]) -> None:
        with self.repository._transaction() as connection:
            connection.execute("INSERT INTO stocks(code, current_name, market, created_at, updated_at) VALUES (?, NULL, 'HK', ?, ?) ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at", (code, now, now))
            connection.executemany(
                """
                INSERT INTO intelligence_events(
                    stock_code, event_key, event_type, announce_date, effective_date,
                    shares_before, shares_after, price, ratio, discount,
                    counterparty, beneficial_owner, placing_agent, adviser, entity_name,
                    source_document, source_url, confidence, extraction_method, retrieved_at, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(stock_code, event_key) DO UPDATE SET
                    event_type=excluded.event_type,
                    announce_date=excluded.announce_date,
                    effective_date=excluded.effective_date,
                    shares_before=excluded.shares_before,
                    shares_after=excluded.shares_after,
                    price=excluded.price,
                    ratio=excluded.ratio,
                    discount=excluded.discount,
                    counterparty=excluded.counterparty,
                    beneficial_owner=excluded.beneficial_owner,
                    placing_agent=excluded.placing_agent,
                    adviser=excluded.adviser,
                    entity_name=excluded.entity_name,
                    source_document=excluded.source_document,
                    source_url=excluded.source_url,
                    confidence=excluded.confidence,
                    extraction_method=excluded.extraction_method,
                    retrieved_at=excluded.retrieved_at,
                    provenance=excluded.provenance
                """,
                [
                    (
                        row.stock_code,
                        _event_key(row),
                        row.event_type,
                        row.announce_date.isoformat(),
                        row.effective_date.isoformat() if row.effective_date else None,
                        row.shares_before,
                        row.shares_after,
                        row.price,
                        row.ratio,
                        row.discount,
                        row.counterparty,
                        row.beneficial_owner,
                        row.placing_agent,
                        row.adviser,
                        row.entity_name,
                        row.source_document,
                        row.source_url,
                        row.confidence,
                        row.extraction_method,
                        row.retrieved_at.isoformat(),
                        row.provenance,
                    )
                    for row in batch
                ],
            )

    def load(self, stock_code: str, *, start_date: date | None = None, end_date: date | None = None) -> list[IntelligenceEventRow]:
        clauses = ["stock_code = ?"]
        parameters: list[object] = [stock_code]
        if start_date is not None:
            clauses.append("announce_date >= ?")
            parameters.append(start_date.isoformat())
        if end_date is not None:
            clauses.append("announce_date <= ?")
            parameters.append(end_date.isoformat())
        with self.repository._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT stock_code, event_type, announce_date, effective_date,
                       shares_before, shares_after, price, ratio, discount,
                       counterparty, beneficial_owner, placing_agent, adviser, entity_name,
                       source_document, source_url, confidence, extraction_method, retrieved_at, provenance
                FROM intelligence_events
                WHERE {" AND ".join(clauses)}
                ORDER BY announce_date DESC
                """,
                parameters,
            ).fetchall()
        return [
            IntelligenceEventRow(
                stock_code=row[0],
                event_type=row[1],
                announce_date=date.fromisoformat(row[2]),
                effective_date=date.fromisoformat(row[3]) if row[3] else None,
                shares_before=row[4],
                shares_after=row[5],
                price=row[6],
                ratio=row[7],
                discount=row[8],
                counterparty=row[9],
                beneficial_owner=row[10],
                placing_agent=row[11],
                adviser=row[12],
                entity_name=row[13],
                source_document=row[14],
                source_url=row[15],
                confidence=row[16],
                extraction_method=row[17],
                retrieved_at=datetime.fromisoformat(row[18]),
                provenance=row[19],
            )
            for row in rows
        ]


def _event_key(row: IntelligenceEventRow) -> str:
    return "|".join(
        str(part or "")
        for part in (row.event_type, row.announce_date.isoformat(), row.source_document, row.counterparty, row.entity_name)
    )
