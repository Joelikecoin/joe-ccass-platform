from __future__ import annotations

from datetime import UTC, date, datetime

from app.models import DisclosureInterestsResponse, DisclosureInterestRow
from app.storage.history import NormalizedSnapshotRepository


class DisclosureInterestRepository:
    def __init__(self, repository: NormalizedSnapshotRepository):
        self.repository = repository

    def save(self, response: DisclosureInterestsResponse) -> None:
        now = datetime.now(UTC).isoformat()
        with self.repository._transaction() as connection:
            connection.execute("INSERT INTO stocks(code, current_name, market, created_at, updated_at) VALUES (?, NULL, 'HK', ?, ?) ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at", (response.metadata.code, now, now))
            connection.executemany("INSERT INTO disclosure_interests(stock_code, filing_id, event_date, filer, classification, shares_involved, previous_balance, present_balance, percentage, average_price, reason, source_url, retrieved_at, provenance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(stock_code, filing_id) DO UPDATE SET event_date=excluded.event_date, filer=excluded.filer, classification=excluded.classification, shares_involved=excluded.shares_involved, present_balance=excluded.present_balance, percentage=excluded.percentage, average_price=excluded.average_price, reason=excluded.reason, source_url=excluded.source_url, retrieved_at=excluded.retrieved_at, provenance=excluded.provenance", [(row.stock_code, row.filing_id, row.event_date.isoformat(), row.filer, row.classification, row.shares_involved, row.previous_balance, row.present_balance, row.percentage, row.average_price, row.reason, row.source_url, row.retrieved_at.isoformat(), row.provenance) for row in response.filings])

    def count_rows(self, stock_code: str) -> int:
        with self.repository._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM disclosure_interests WHERE stock_code = ?", (stock_code,)).fetchone()
        return int(row[0])

    def load_rows(self, stock_code: str, *, start_date: date, end_date: date) -> list[DisclosureInterestRow]:
        with self.repository._connect() as connection:
            rows = connection.execute(
                """
                SELECT filing_id, stock_code, event_date, filer, classification,
                       shares_involved, previous_balance, present_balance, percentage,
                       average_price, reason, source_url, retrieved_at, provenance
                FROM disclosure_interests
                WHERE stock_code = ? AND event_date BETWEEN ? AND ?
                ORDER BY event_date DESC, filing_id
                """,
                (stock_code, start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        return [
            DisclosureInterestRow(
                filing_id=row[0],
                stock_code=row[1],
                event_date=date.fromisoformat(row[2]),
                filer=row[3],
                classification=row[4],
                shares_involved=row[5],
                previous_balance=row[6],
                present_balance=row[7],
                percentage=row[8],
                average_price=row[9],
                reason=row[10],
                source_url=row[11],
                retrieved_at=datetime.fromisoformat(row[12]),
                provenance=row[13],
            )
            for row in rows
        ]
