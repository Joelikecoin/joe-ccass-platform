from __future__ import annotations

from datetime import UTC, date, datetime

from app.models import ShareCapitalHistoryResponse
from app.storage.history import NormalizedSnapshotRepository


class ShareCapitalHistoryRepository:
    def __init__(self, repository: NormalizedSnapshotRepository):
        self.repository = repository

    def save(self, response: ShareCapitalHistoryResponse) -> None:
        now = datetime.now(UTC).isoformat()
        with self.repository._transaction() as connection:
            connection.execute("INSERT INTO stocks(code, current_name, market, created_at, updated_at) VALUES (?, NULL, 'HK', ?, ?) ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at", (response.metadata.code, now, now))
            connection.executemany(
                """
                INSERT INTO share_capital_history(
                    stock_code, announce_date, shares_million, shares_approx,
                    reason, reason_tags_json, change_date, source, source_url, retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(stock_code, announce_date, source_url) DO UPDATE SET
                    shares_million=excluded.shares_million,
                    shares_approx=excluded.shares_approx,
                    reason=excluded.reason,
                    reason_tags_json=excluded.reason_tags_json,
                    change_date=excluded.change_date,
                    retrieved_at=excluded.retrieved_at
                """,
                [
                    (
                        response.metadata.code,
                        row.announce_date.isoformat(),
                        row.shares_million,
                        row.shares_approx,
                        row.reason,
                        __import__("json").dumps(row.reason_tags, ensure_ascii=False),
                        row.change_date.isoformat() if row.change_date else None,
                        row.source,
                        row.source_url,
                        now,
                    )
                    for row in response.rows
                ],
            )

    def load(self, stock_code: str, *, start_date: date | None = None, end_date: date | None = None) -> ShareCapitalHistoryResponse | None:
        import json

        from app.models import ShareCapitalHistoryMetadata, ShareCapitalHistoryRow

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
                SELECT announce_date, shares_million, shares_approx, reason,
                       reason_tags_json, change_date, source, source_url
                FROM share_capital_history
                WHERE {" AND ".join(clauses)}
                ORDER BY announce_date DESC
                """,
                parameters,
            ).fetchall()
        if not rows:
            return None
        parsed = [
            ShareCapitalHistoryRow(
                announce_date=date.fromisoformat(row[0]),
                shares_million=row[1],
                shares_approx=row[2],
                reason=row[3],
                reason_tags=json.loads(row[4]) if row[4] else [],
                change_date=date.fromisoformat(row[5]) if row[5] else None,
                source=row[6],
                source_url=row[7],
            )
            for row in rows
        ]
        return ShareCapitalHistoryResponse(
            metadata=ShareCapitalHistoryMetadata(code=stock_code, source_name="share-capital-history store", fetched_at=datetime.now(UTC), source_status="ready", documents_attempted=len(parsed), documents_fetched=len(parsed), documents_parsed=len(parsed)),
            rows=parsed,
        )
