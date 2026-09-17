from __future__ import annotations

from datetime import UTC, datetime

from app.models import DisclosureInterestsResponse
from app.storage.history import NormalizedSnapshotRepository


class DisclosureInterestRepository:
    def __init__(self, repository: NormalizedSnapshotRepository):
        self.repository = repository

    def save(self, response: DisclosureInterestsResponse) -> None:
        now = datetime.now(UTC).isoformat()
        with self.repository._transaction() as connection:
            connection.execute("INSERT INTO stocks(code, current_name, market, created_at, updated_at) VALUES (?, NULL, 'HK', ?, ?) ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at", (response.metadata.code, now, now))
            connection.executemany("INSERT INTO disclosure_interests(stock_code, filing_id, event_date, filer, classification, shares_involved, previous_balance, present_balance, percentage, average_price, reason, source_url, retrieved_at, provenance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(stock_code, filing_id) DO UPDATE SET event_date=excluded.event_date, filer=excluded.filer, classification=excluded.classification, shares_involved=excluded.shares_involved, present_balance=excluded.present_balance, percentage=excluded.percentage, average_price=excluded.average_price, reason=excluded.reason, source_url=excluded.source_url, retrieved_at=excluded.retrieved_at, provenance=excluded.provenance", [(row.stock_code, row.filing_id, row.event_date.isoformat(), row.filer, row.classification, row.shares_involved, row.previous_balance, row.present_balance, row.percentage, row.average_price, row.reason, row.source_url, row.retrieved_at.isoformat(), row.provenance) for row in response.filings])
