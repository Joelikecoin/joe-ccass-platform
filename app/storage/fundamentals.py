from __future__ import annotations

import json
from datetime import date

from app.models import FundamentalRow, FundamentalsResponse
from app.storage.history import NormalizedSnapshotRepository


class FundamentalsRepository:
    def __init__(self, repository: NormalizedSnapshotRepository):
        self.repository = repository

    def save(self, response: FundamentalsResponse) -> None:
        with self.repository._transaction() as connection:
            now = response.metadata.fetched_at.isoformat()
            connection.execute("INSERT INTO stocks(code, current_name, market, created_at, updated_at) VALUES (?, NULL, 'HK', ?, ?) ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at", (response.metadata.code, now, now))
            connection.executemany(
                "INSERT INTO fundamentals(stock_code, source_document, reporting_period, announcement_date, report_type, payload_json, retrieved_at) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(stock_code, source_document) DO UPDATE SET reporting_period=excluded.reporting_period, announcement_date=excluded.announcement_date, report_type=excluded.report_type, payload_json=excluded.payload_json, retrieved_at=excluded.retrieved_at",
                [(row.stock_code, row.source_document, row.reporting_period, row.announcement_date.isoformat(), row.report_type, row.model_dump_json(), row.retrieval_timestamp.isoformat()) for row in response.rows],
            )

    def load(self, code: str) -> FundamentalsResponse | None:
        with self.repository._connect() as connection:
            rows = connection.execute("SELECT payload_json FROM fundamentals WHERE stock_code = ? ORDER BY announcement_date DESC", (code,)).fetchall()
        if not rows:
            return None
        parsed = [FundamentalRow.model_validate(json.loads(row["payload_json"])) for row in rows]
        return FundamentalsResponse(
            metadata={"code": code, "fetched_at": parsed[0].retrieval_timestamp, "source_status": "ready", "documents_attempted": len(parsed), "documents_fetched": len(parsed), "documents_parsed": len(parsed)},
            rows=parsed,
            data_quality_warnings=["Fundamentals served from persisted HKEXnews documents."],
        )
