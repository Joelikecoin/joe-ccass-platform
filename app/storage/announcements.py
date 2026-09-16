from __future__ import annotations

from datetime import UTC, date, datetime

from app.models import AnnouncementRow, AnnouncementsMetadata, AnnouncementsResponse
from app.storage.history import NormalizedSnapshotRepository


class AnnouncementRepository:
    """Idempotent historical announcement metadata storage on the canonical DB."""

    def __init__(self, repository: NormalizedSnapshotRepository) -> None:
        self.repository = repository

    def save(self, response: AnnouncementsResponse) -> None:
        now = datetime.now(UTC).isoformat()
        with self.repository._transaction() as connection:  # shared SQLite/Turso path
            connection.execute(
                """
                INSERT INTO stocks(code, current_name, market, created_at, updated_at)
                VALUES (?, ?, 'HK', ?, ?)
                ON CONFLICT(code) DO UPDATE SET current_name=excluded.current_name, updated_at=excluded.updated_at
                """,
                (response.metadata.code, response.metadata.name, now, now),
            )
            values = []
            for row in response.announcements:
                document_id = row.document_id or (
                    f"{row.announcement_date.isoformat()}|{row.title}|{row.link or ''}"
                )
                published = (
                    row.publication_datetime
                    or datetime.combine(row.announcement_date, datetime.min.time(), tzinfo=UTC)
                ).isoformat()
                values.append((
                    response.metadata.code,
                    document_id,
                    published,
                    row.announcement_date.isoformat(),
                    row.title,
                    row.category,
                    row.long_text,
                    row.link,
                    row.language,
                    row.source,
                    row.file_type,
                    row.file_info,
                    now,
                    row.retrieval_status,
                ))
            if values:
                connection.executemany(
                    """
                    INSERT INTO announcements(
                        stock_code, document_id, publication_datetime, announcement_date, title,
                        category, long_text, document_url, language, source, file_type, file_info,
                        retrieved_at, retrieval_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(stock_code, source, document_id) DO UPDATE SET
                        publication_datetime=excluded.publication_datetime,
                        announcement_date=excluded.announcement_date,
                        title=excluded.title,
                        category=excluded.category,
                        long_text=excluded.long_text,
                        document_url=excluded.document_url,
                        language=excluded.language,
                        file_type=excluded.file_type,
                        file_info=excluded.file_info,
                        retrieved_at=excluded.retrieved_at,
                        retrieval_status=excluded.retrieval_status
                    """,
                    values,
                )

    def load(
        self, code: str, *, start_date: date, end_date: date
    ) -> AnnouncementsResponse | None:
        connection = self.repository._connect()
        try:
            rows = connection.execute(
                """
                SELECT * FROM announcements
                WHERE stock_code = ? AND announcement_date BETWEEN ? AND ?
                ORDER BY publication_datetime DESC
                """,
                (code, start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        finally:
            connection.close()
        if not rows:
            return None
        announcements = [
            AnnouncementRow(
                announcement_date=date.fromisoformat(str(row["announcement_date"])),
                title=str(row["title"]),
                source=str(row["source"]),
                link=row["document_url"],
                publication_datetime=datetime.fromisoformat(str(row["publication_datetime"])),
                category=row["category"],
                long_text=row["long_text"],
                language=row["language"],
                document_id=row["document_id"],
                file_type=row["file_type"],
                file_info=row["file_info"],
                retrieval_status="cached",
            )
            for row in rows
        ]
        dates = [row.announcement_date for row in announcements]
        return AnnouncementsResponse(
            metadata=AnnouncementsMetadata(
                code=code,
                name=None,
                source_name="HKEXnews",
                source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml",
                fetched_at=datetime.now(UTC),
                earliest_announcement_date=min(dates),
                latest_announcement_date=max(dates),
                announcement_count=len(announcements),
                coverage_start=min(dates),
                coverage_end=max(dates),
                source_status="cached",
                document_access_status="links_available",
                cached=True,
            ),
            announcements=announcements,
            data_quality_warnings=[
                "Announcements served from the persisted local historical cache."
            ],
        )
