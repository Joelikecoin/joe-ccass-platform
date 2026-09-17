from __future__ import annotations

from app.models import DocumentEntitiesResponse
from app.storage.history import NormalizedSnapshotRepository


class DocumentEntityRepository:
    def __init__(self, repository: NormalizedSnapshotRepository):
        self.repository = repository

    def save(self, response: DocumentEntitiesResponse) -> None:
        with self.repository._transaction() as connection:
            now = response.metadata.fetched_at.isoformat()
            connection.execute("INSERT INTO stocks(code, current_name, market, created_at, updated_at) VALUES (?, NULL, 'HK', ?, ?) ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at", (response.metadata.code, now, now))
            connection.executemany(
                """INSERT INTO document_entities(
                    stock_code, document_id, document_type, entity_type, entity_name,
                    direct_source_fact, derived_classification, source_url,
                    announcement_date, retrieved_at, provenance
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM document_entities
                    WHERE stock_code=? AND document_id=? AND entity_type=?
                      AND ((entity_name = ?) OR (entity_name IS NULL AND ? IS NULL))
                )""",
                [
                    (
                        r.stock_code, r.document_id, r.document_type, r.entity_type,
                        r.entity_name, r.direct_source_fact, r.derived_classification,
                        r.source_url, r.announcement_date.isoformat(),
                        r.retrieved_at.isoformat(), r.provenance,
                        r.stock_code, r.document_id, r.entity_type,
                        r.entity_name, r.entity_name,
                    )
                    for r in response.rows
                ],
            )
