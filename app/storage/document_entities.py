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

    def load_graph(self, *, start_date, end_date) -> dict:
        """實體關係圖種子 (cross-stock intermediary graph seed): nodes are
        named entities with appearance breadth; edges are same-document
        co-occurrences (two entities named in one filing = working together)."""
        with self.repository._connect() as connection:
            node_rows = connection.execute(
                """
                SELECT MAX(entity_name), entity_type, COUNT(*), COUNT(DISTINCT stock_code),
                       MIN(announcement_date), MAX(announcement_date),
                       COUNT(DISTINCT document_id)
                FROM document_entities
                WHERE entity_name IS NOT NULL AND announcement_date BETWEEN ? AND ?
                GROUP BY LOWER(entity_name), entity_type
                ORDER BY COUNT(DISTINCT stock_code) DESC, COUNT(*) DESC
                LIMIT 500
                """,
                (start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
            edge_rows = connection.execute(
                """
                SELECT a.entity_name, a.entity_type, b.entity_name, b.entity_type,
                       COUNT(DISTINCT a.document_id), MIN(a.announcement_date), MAX(a.announcement_date)
                FROM document_entities a
                JOIN document_entities b
                  ON a.stock_code = b.stock_code AND a.document_id = b.document_id
                 AND (LOWER(a.entity_name) < LOWER(b.entity_name)
                      OR (LOWER(a.entity_name) = LOWER(b.entity_name) AND a.entity_type < b.entity_type))
                WHERE a.entity_name IS NOT NULL AND b.entity_name IS NOT NULL
                  AND a.announcement_date BETWEEN ? AND ?
                GROUP BY LOWER(a.entity_name), a.entity_type, LOWER(b.entity_name), b.entity_type
                ORDER BY COUNT(DISTINCT a.document_id) DESC
                LIMIT 300
                """,
                (start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        nodes = [
            {
                "entity_name": r[0],
                "entity_type": r[1],
                "appearances": r[2],
                "stocks": r[3],
                "first_seen": r[4],
                "last_seen": r[5],
                "documents": r[6],
            }
            for r in node_rows
        ]
        edges = [
            {
                "source_name": r[0],
                "source_type": r[1],
                "target_name": r[2],
                "target_type": r[3],
                "shared_documents": r[4],
                "first_seen": r[5],
                "last_seen": r[6],
            }
            for r in edge_rows
        ]
        return {"nodes": nodes, "edges": edges, "window": {"start": start_date.isoformat(), "end": end_date.isoformat()}}

    def load_rows(self, stock_code: str, *, start_date, end_date):
        from datetime import date

        from app.models import DocumentEntityRow

        with self.repository._connect() as connection:
            rows = connection.execute(
                """
                SELECT document_id, document_type, entity_type, entity_name,
                       direct_source_fact, source_url, announcement_date, retrieved_at, provenance
                FROM document_entities
                WHERE stock_code = ? AND announcement_date BETWEEN ? AND ?
                ORDER BY announcement_date DESC
                """,
                (stock_code, start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        return [
            DocumentEntityRow(
                stock_code=stock_code,
                document_id=row[0],
                document_type=row[1],
                entity_type=row[2],
                entity_name=row[3],
                direct_source_fact=row[4],
                source_url=row[5],
                announcement_date=date.fromisoformat(row[6]),
                retrieved_at=row[7],
                provenance=row[8],
            )
            for row in rows
        ]
