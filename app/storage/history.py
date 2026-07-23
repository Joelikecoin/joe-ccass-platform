import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

from app.domain.history import (
    BackfillRunItemRecord,
    BackfillRunRecord,
    CollectorRunItemRecord,
    CollectorRunRecord,
    HistoricalSnapshot,
    NormalizedHolding,
    RawProvenance,
    SourceErrorRecord,
    SourceIdentity,
    StockIdentity,
)
from app.models import CcassResponse
from app.storage.migrations import apply_migrations


class NormalizedSnapshotRepository:
    """Transactional source-neutral CCASS snapshot persistence."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            apply_migrations(connection)
        self._migrate_legacy_snapshots()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def save_response(
        self,
        response: CcassResponse,
        *,
        source_id: str | None = None,
        stale: bool = False,
        partial: bool | None = None,
        parser_version: str = "ccass-response-v1",
        issued_shares_as_of: date | None = None,
        provenance_bytes: bytes | None = None,
        provenance_reference: str | None = None,
    ) -> int:
        snapshot = HistoricalSnapshot.from_response(
            response,
            source_id=source_id,
            stale=stale,
            partial=partial,
            parser_version=parser_version,
            issued_shares_as_of=issued_shares_as_of,
            provenance_bytes=provenance_bytes,
            provenance_reference=provenance_reference,
        )
        return self.save(snapshot)

    def save(self, snapshot: HistoricalSnapshot) -> int:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = datetime.now(UTC).isoformat()
            self._upsert_stock(connection, snapshot.stock, now)
            self._upsert_source_mapping(connection, snapshot, now)
            existing = connection.execute(
                """
                SELECT id, partial
                FROM ccass_snapshots
                WHERE stock_code = ? AND snapshot_date = ? AND source_id = ?
                """,
                (
                    snapshot.stock.code,
                    snapshot.snapshot_date.isoformat(),
                    snapshot.source.source_id,
                ),
            ).fetchone()
            if existing and not bool(existing["partial"]) and snapshot.partial:
                connection.commit()
                return int(existing["id"])

            provenance_id = self._upsert_provenance(connection, snapshot.provenance)
            snapshot_id = self._upsert_snapshot(
                connection,
                snapshot,
                provenance_id=provenance_id,
                now=now,
            )
            connection.execute(
                "DELETE FROM ccass_holdings WHERE snapshot_id = ?",
                (snapshot_id,),
            )
            self._insert_holdings(connection, snapshot_id, snapshot.holdings)
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
            return snapshot_id
        finally:
            connection.close()

    def latest(
        self,
        code: str,
        *,
        source_id: str | None = None,
        include_partial: bool = True,
    ) -> HistoricalSnapshot | None:
        clauses = ["stock_code = ?"]
        parameters: list[object] = [code]
        if source_id:
            clauses.append("source_id = ?")
            parameters.append(source_id)
        if not include_partial:
            clauses.append("partial = 0")
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT *
                FROM ccass_snapshots
                WHERE {" AND ".join(clauses)}
                ORDER BY snapshot_date DESC, fetched_at DESC, id DESC
                LIMIT 1
                """,
                parameters,
            ).fetchone()
            return self._load_snapshot(connection, row) if row else None

    def previous(
        self,
        code: str,
        *,
        before_date: date,
        source_id: str | None = None,
        include_partial: bool = True,
    ) -> HistoricalSnapshot | None:
        clauses = ["stock_code = ?", "snapshot_date < ?"]
        parameters: list[object] = [code, before_date.isoformat()]
        if source_id:
            clauses.append("source_id = ?")
            parameters.append(source_id)
        if not include_partial:
            clauses.append("partial = 0")
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT *
                FROM ccass_snapshots
                WHERE {" AND ".join(clauses)}
                ORDER BY snapshot_date DESC, fetched_at DESC, id DESC
                LIMIT 1
                """,
                parameters,
            ).fetchone()
            return self._load_snapshot(connection, row) if row else None

    def date_range(
        self,
        code: str,
        *,
        date_from: date,
        date_to: date,
        source_id: str | None = None,
        include_partial: bool = True,
    ) -> list[HistoricalSnapshot]:
        if date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        clauses = ["stock_code = ?", "snapshot_date BETWEEN ? AND ?"]
        parameters: list[object] = [code, date_from.isoformat(), date_to.isoformat()]
        if source_id:
            clauses.append("source_id = ?")
            parameters.append(source_id)
        if not include_partial:
            clauses.append("partial = 0")
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM ccass_snapshots
                WHERE {" AND ".join(clauses)}
                ORDER BY snapshot_date, fetched_at, id
                """,
                parameters,
            ).fetchall()
            return [self._load_snapshot(connection, row) for row in rows]

    def latest_all(self) -> list[HistoricalSnapshot]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM ccass_snapshots
                ORDER BY stock_code, snapshot_date DESC, fetched_at DESC, id DESC
                """
            ).fetchall()
            latest_rows: list[sqlite3.Row] = []
            seen: set[str] = set()
            for row in rows:
                code = str(row["stock_code"])
                if code not in seen:
                    latest_rows.append(row)
                    seen.add(code)
            return [self._load_snapshot(connection, row) for row in latest_rows]

    def count_snapshots(self, code: str | None = None) -> int:
        with self._connect() as connection:
            if code is None:
                row = connection.execute("SELECT COUNT(*) FROM ccass_snapshots").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) FROM ccass_snapshots WHERE stock_code = ?",
                    (code,),
                ).fetchone()
        return int(row[0])

    def create_collector_run(self, run: CollectorRunRecord) -> int:
        with self._transaction() as connection:
            cursor = connection.execute(
                """
                INSERT INTO collector_runs(
                    started_at, completed_at, status, source_id, requested_codes_json,
                    success_count, partial_count, error_count, safe_details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.started_at.isoformat(),
                    run.completed_at.isoformat() if run.completed_at else None,
                    run.status,
                    run.source_id,
                    _json(run.requested_codes),
                    run.success_count,
                    run.partial_count,
                    run.error_count,
                    _json(run.safe_details),
                ),
            )
            return int(cursor.lastrowid)

    def complete_collector_run(
        self,
        run_id: int,
        *,
        completed_at: datetime,
        status: str,
        success_count: int,
        partial_count: int,
        error_count: int,
        safe_details: dict[str, str | int | bool | None],
    ) -> None:
        if status not in {"SUCCESS", "PARTIAL", "ERROR"}:
            raise ValueError("collector run status is invalid")
        with self._transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE collector_runs
                SET completed_at = ?, status = ?, success_count = ?, partial_count = ?,
                    error_count = ?, safe_details_json = ?
                WHERE id = ?
                """,
                (
                    completed_at.isoformat(),
                    status,
                    success_count,
                    partial_count,
                    error_count,
                    _json(safe_details),
                    run_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("collector run does not exist")

    def record_collector_result(self, item: CollectorRunItemRecord) -> int:
        with self._transaction() as connection:
            return self._upsert_collector_run_item(connection, item)

    def record_collector_failure(
        self, item: CollectorRunItemRecord, error: SourceErrorRecord
    ) -> tuple[int, int]:
        if error.run_id != item.run_id:
            raise ValueError("collector item and source error run IDs must match")
        with self._transaction() as connection:
            item_id = self._upsert_collector_run_item(connection, item)
            error_id = self._insert_source_error(connection, error)
            return item_id, error_id

    def record_source_error(self, error: SourceErrorRecord) -> int:
        with self._transaction() as connection:
            return self._insert_source_error(connection, error)

    def _upsert_collector_run_item(
        self, connection: sqlite3.Connection, item: CollectorRunItemRecord
    ) -> int:
        connection.execute(
            """
            INSERT INTO collector_run_items(
                run_id, stock_code, status, source_id, snapshot_id, snapshot_date,
                partial, safe_details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, stock_code) DO UPDATE SET
                status = excluded.status,
                source_id = excluded.source_id,
                snapshot_id = excluded.snapshot_id,
                snapshot_date = excluded.snapshot_date,
                partial = excluded.partial,
                safe_details_json = excluded.safe_details_json
            """,
            (
                item.run_id,
                item.stock_code,
                item.status,
                item.source_id,
                item.snapshot_id,
                item.snapshot_date.isoformat() if item.snapshot_date else None,
                int(item.partial),
                _json(item.safe_details),
                datetime.now(UTC).isoformat(),
            ),
        )
        row = connection.execute(
            "SELECT id FROM collector_run_items WHERE run_id = ? AND stock_code = ?",
            (item.run_id, item.stock_code),
        ).fetchone()
        return int(row["id"])

    @staticmethod
    def _insert_source_error(connection: sqlite3.Connection, error: SourceErrorRecord) -> int:
        cursor = connection.execute(
            """
            INSERT INTO source_errors(
                run_id, source_id, stock_code, occurred_at, error_code, safe_message,
                retry_recommended, retry_after_seconds, safe_details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                error.run_id,
                error.source_id,
                error.stock_code,
                error.occurred_at.isoformat(),
                error.error_code,
                error.safe_message,
                int(error.retry_recommended),
                error.retry_after_seconds,
                _json(error.safe_details),
            ),
        )
        return int(cursor.lastrowid)

    def snapshot_on(
        self,
        code: str,
        snapshot_date: date,
        *,
        source_id: str,
    ) -> HistoricalSnapshot | None:
        snapshots = self.date_range(
            code,
            date_from=snapshot_date,
            date_to=snapshot_date,
            source_id=source_id,
        )
        return snapshots[-1] if snapshots else None

    def snapshot_id_on(
        self,
        code: str,
        snapshot_date: date,
        *,
        source_id: str,
    ) -> int | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id FROM ccass_snapshots
                WHERE stock_code = ? AND snapshot_date = ? AND source_id = ?
                """,
                (code, snapshot_date.isoformat(), source_id),
            ).fetchone()
        return int(row["id"]) if row else None

    def create_backfill_run(self, run: BackfillRunRecord) -> int:
        with self._transaction() as connection:
            cursor = connection.execute(
                """
                INSERT INTO backfill_runs(
                    stock_code, source_id, requested_from, requested_to, latest_count,
                    requested_dates_json, cursor_date, started_at, completed_at, status,
                    success_count, partial_count, error_count, skipped_count, safe_details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.stock_code,
                    run.source_id,
                    run.requested_from.isoformat() if run.requested_from else None,
                    run.requested_to.isoformat() if run.requested_to else None,
                    run.latest_count,
                    _json([value.isoformat() for value in run.requested_dates]),
                    run.cursor_date.isoformat() if run.cursor_date else None,
                    run.started_at.isoformat(),
                    run.completed_at.isoformat() if run.completed_at else None,
                    run.status,
                    run.success_count,
                    run.partial_count,
                    run.error_count,
                    run.skipped_count,
                    _json(run.safe_details),
                ),
            )
            return int(cursor.lastrowid)

    def resume_backfill_run(self, run_id: int) -> None:
        with self._transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE backfill_runs
                SET status = 'RUNNING', completed_at = NULL
                WHERE id = ?
                """,
                (run_id,),
            )
            if cursor.rowcount != 1:
                raise ValueError("backfill run does not exist")

    def complete_backfill_run(
        self,
        run_id: int,
        *,
        completed_at: datetime,
        status: str,
        success_count: int,
        partial_count: int,
        error_count: int,
        skipped_count: int,
        safe_details: dict[str, str | int | bool | None],
    ) -> None:
        if status not in {"SUCCESS", "PARTIAL", "ERROR"}:
            raise ValueError("backfill run status is invalid")
        with self._transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE backfill_runs
                SET completed_at = ?, status = ?, success_count = ?, partial_count = ?,
                    error_count = ?, skipped_count = ?, safe_details_json = ?
                WHERE id = ?
                """,
                (
                    completed_at.isoformat(),
                    status,
                    success_count,
                    partial_count,
                    error_count,
                    skipped_count,
                    _json(safe_details),
                    run_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("backfill run does not exist")

    def record_backfill_result(self, item: BackfillRunItemRecord) -> int:
        now = datetime.now(UTC).isoformat()
        with self._transaction() as connection:
            connection.execute(
                """
                INSERT INTO backfill_run_items(
                    run_id, requested_date, status, source_id, snapshot_id, partial,
                    error_code, safe_message, retry_recommended, safe_details_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, requested_date) DO UPDATE SET
                    status = excluded.status,
                    source_id = excluded.source_id,
                    snapshot_id = excluded.snapshot_id,
                    partial = excluded.partial,
                    error_code = excluded.error_code,
                    safe_message = excluded.safe_message,
                    retry_recommended = excluded.retry_recommended,
                    safe_details_json = excluded.safe_details_json,
                    updated_at = excluded.updated_at
                """,
                (
                    item.run_id,
                    item.requested_date.isoformat(),
                    item.status,
                    item.source_id,
                    item.snapshot_id,
                    int(item.partial),
                    item.error_code,
                    item.safe_message,
                    int(item.retry_recommended),
                    _json(item.safe_details),
                    now,
                    now,
                ),
            )
            connection.execute(
                "UPDATE backfill_runs SET cursor_date = ? WHERE id = ?",
                (item.requested_date.isoformat(), item.run_id),
            )
            row = connection.execute(
                "SELECT id FROM backfill_run_items WHERE run_id = ? AND requested_date = ?",
                (item.run_id, item.requested_date.isoformat()),
            ).fetchone()
            return int(row["id"])

    def get_backfill_items(self, run_id: int) -> list[BackfillRunItemRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM backfill_run_items
                WHERE run_id = ? ORDER BY requested_date
                """,
                (run_id,),
            ).fetchall()
        return [
            BackfillRunItemRecord(
                run_id=int(row["run_id"]),
                requested_date=date.fromisoformat(row["requested_date"]),
                status=row["status"],
                source_id=row["source_id"],
                snapshot_id=row["snapshot_id"],
                partial=bool(row["partial"]),
                error_code=row["error_code"],
                safe_message=row["safe_message"],
                retry_recommended=bool(row["retry_recommended"]),
                safe_details=json.loads(row["safe_details_json"]),
            )
            for row in rows
        ]

    def get_resumable_backfill_run(
        self,
        stock_code: str,
        *,
        source_id: str,
    ) -> BackfillRunRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT runs.*
                FROM backfill_runs AS runs
                WHERE runs.stock_code = ? AND runs.source_id = ?
                  AND (
                    runs.status = 'RUNNING'
                    OR EXISTS (
                        SELECT 1 FROM backfill_run_items AS items
                        WHERE items.run_id = runs.id AND items.status = 'ERROR'
                    )
                  )
                ORDER BY runs.id DESC
                LIMIT 1
                """,
                (stock_code, source_id),
            ).fetchone()
        return self._load_backfill_run(row) if row else None

    @staticmethod
    def _load_backfill_run(row: sqlite3.Row) -> BackfillRunRecord:
        return BackfillRunRecord(
            run_id=int(row["id"]),
            stock_code=row["stock_code"],
            source_id=row["source_id"],
            requested_from=(
                date.fromisoformat(row["requested_from"]) if row["requested_from"] else None
            ),
            requested_to=(date.fromisoformat(row["requested_to"]) if row["requested_to"] else None),
            latest_count=row["latest_count"],
            requested_dates=tuple(
                date.fromisoformat(value) for value in json.loads(row["requested_dates_json"])
            ),
            cursor_date=date.fromisoformat(row["cursor_date"]) if row["cursor_date"] else None,
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
            ),
            status=row["status"],
            success_count=int(row["success_count"]),
            partial_count=int(row["partial_count"]),
            error_count=int(row["error_count"]),
            skipped_count=int(row["skipped_count"]),
            safe_details=json.loads(row["safe_details_json"]),
        )

    def legacy_latest_responses(self) -> list[CcassResponse]:
        if not self._has_legacy_table():
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT snapshots.payload_json
                FROM snapshots
                JOIN (
                    SELECT code, MAX(id) AS latest_id
                    FROM snapshots
                    GROUP BY code
                ) latest ON snapshots.id = latest.latest_id
                ORDER BY snapshots.code
                """
            ).fetchall()
        responses: list[CcassResponse] = []
        for row in rows:
            try:
                responses.append(CcassResponse.model_validate_json(row["payload_json"]))
            except ValueError:
                continue
        return responses

    def legacy_responses(self, code: str | None = None) -> list[CcassResponse]:
        if not self._has_legacy_table():
            return []
        query = "SELECT payload_json FROM snapshots"
        parameters: tuple[object, ...] = ()
        if code is not None:
            query += " WHERE code = ?"
            parameters = (code,)
        query += " ORDER BY id"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        responses: list[CcassResponse] = []
        for row in rows:
            try:
                responses.append(CcassResponse.model_validate_json(row["payload_json"]))
            except ValueError:
                continue
        return responses

    def _upsert_stock(self, connection: sqlite3.Connection, stock: StockIdentity, now: str) -> None:
        connection.execute(
            """
            INSERT INTO stocks(code, current_name, market, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                current_name = COALESCE(excluded.current_name, stocks.current_name),
                market = excluded.market,
                updated_at = excluded.updated_at
            """,
            (stock.code, stock.name, stock.market, now, now),
        )

    def _upsert_source_mapping(
        self, connection: sqlite3.Connection, snapshot: HistoricalSnapshot, now: str
    ) -> None:
        connection.execute(
            """
            INSERT INTO source_issue_mapping(
                stock_code, source_id, issue_id, first_verified_at, last_verified_at,
                evidence_identifier
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(stock_code, source_id, issue_id) DO UPDATE SET
                last_verified_at = excluded.last_verified_at,
                evidence_identifier = excluded.evidence_identifier
            """,
            (
                snapshot.stock.code,
                snapshot.source.source_id,
                str(snapshot.source.issue_id),
                now,
                now,
                snapshot.source.safe_identifier,
            ),
        )

    def _upsert_provenance(self, connection: sqlite3.Connection, provenance: RawProvenance) -> int:
        connection.execute(
            """
            INSERT INTO raw_provenance(
                source_id, safe_reference, checksum_sha256, fetched_at, content_type, byte_size
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id, checksum_sha256) DO UPDATE SET
                safe_reference = excluded.safe_reference,
                fetched_at = excluded.fetched_at,
                content_type = excluded.content_type,
                byte_size = excluded.byte_size
            """,
            (
                provenance.source_id,
                provenance.safe_reference,
                provenance.checksum_sha256,
                provenance.fetched_at.isoformat(),
                provenance.content_type,
                provenance.byte_size,
            ),
        )
        row = connection.execute(
            "SELECT id FROM raw_provenance WHERE source_id = ? AND checksum_sha256 = ?",
            (provenance.source_id, provenance.checksum_sha256),
        ).fetchone()
        return int(row["id"])

    def _upsert_snapshot(
        self,
        connection: sqlite3.Connection,
        snapshot: HistoricalSnapshot,
        *,
        provenance_id: int,
        now: str,
    ) -> int:
        values = {
            "stock_code": snapshot.stock.code,
            "snapshot_date": snapshot.snapshot_date.isoformat(),
            "source_id": snapshot.source.source_id,
            "source_name": snapshot.source.display_name,
            "source_identifier": snapshot.source.safe_identifier,
            "issue_id": snapshot.source.issue_id,
            "fetched_at": snapshot.fetched_at.isoformat(),
            "cached": int(snapshot.cached),
            "stale": int(snapshot.stale),
            "partial": int(snapshot.partial),
            "parser_version": snapshot.parser_version,
            "schema_version": snapshot.schema_version,
            "warnings_json": _json(snapshot.warnings),
            "issued_shares": snapshot.issued_shares,
            "issued_shares_as_of": (
                snapshot.issued_shares_as_of.isoformat() if snapshot.issued_shares_as_of else None
            ),
            "denominator": snapshot.denominator,
            "total_in_ccass_shares": snapshot.total_in_ccass_shares,
            "total_in_ccass_pct_of_issued": snapshot.total_in_ccass_pct_of_issued,
            "non_ccass_shares": snapshot.non_ccass_shares,
            "non_ccass_pct_of_issued": snapshot.non_ccass_pct_of_issued,
            "participant_count": snapshot.participant_count,
            "top5_pct_of_issued": snapshot.top5_pct_of_issued,
            "top10_pct_of_issued": snapshot.top10_pct_of_issued,
            "top5_pct_of_ccass": snapshot.top5_pct_of_ccass,
            "top10_pct_of_ccass": snapshot.top10_pct_of_ccass,
            "settlement_note": snapshot.settlement_note,
            "attribution": snapshot.attribution,
            "provenance_id": provenance_id,
            "created_at": now,
            "updated_at": now,
        }
        columns = tuple(values)
        placeholders = ", ".join(f":{column}" for column in columns)
        updates = ", ".join(
            f"{column} = excluded.{column}"
            for column in columns
            if column not in {"stock_code", "snapshot_date", "source_id", "created_at"}
        )
        connection.execute(
            f"""
            INSERT INTO ccass_snapshots({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(stock_code, snapshot_date, source_id) DO UPDATE SET {updates}
            """,
            values,
        )
        row = connection.execute(
            """
            SELECT id FROM ccass_snapshots
            WHERE stock_code = ? AND snapshot_date = ? AND source_id = ?
            """,
            (
                snapshot.stock.code,
                snapshot.snapshot_date.isoformat(),
                snapshot.source.source_id,
            ),
        ).fetchone()
        return int(row["id"])

    def _insert_holdings(
        self,
        connection: sqlite3.Connection,
        snapshot_id: int,
        holdings: tuple[NormalizedHolding, ...],
    ) -> None:
        connection.executemany(
            """
            INSERT INTO ccass_holdings(
                snapshot_id, participant_id, participant_name, rank, shares, last_change,
                pct_of_issued, pct_of_ccass, cumulative_pct_of_issued, participant_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    snapshot_id,
                    row.participant_id,
                    row.participant_name,
                    row.rank,
                    row.shares,
                    row.last_change.isoformat() if row.last_change else None,
                    row.pct_of_issued,
                    row.pct_of_ccass,
                    row.cumulative_pct_of_issued,
                    row.participant_category,
                )
                for row in holdings
            ],
        )

    def _load_snapshot(
        self, connection: sqlite3.Connection, row: sqlite3.Row
    ) -> HistoricalSnapshot:
        holding_rows = connection.execute(
            "SELECT * FROM ccass_holdings WHERE snapshot_id = ? ORDER BY rank",
            (row["id"],),
        ).fetchall()
        provenance_row = connection.execute(
            "SELECT * FROM raw_provenance WHERE id = ?",
            (row["provenance_id"],),
        ).fetchone()
        return HistoricalSnapshot(
            stock=StockIdentity(
                code=row["stock_code"],
                name=connection.execute(
                    "SELECT current_name FROM stocks WHERE code = ?",
                    (row["stock_code"],),
                ).fetchone()["current_name"],
            ),
            source=SourceIdentity(
                source_id=row["source_id"],
                display_name=row["source_name"],
                safe_identifier=row["source_identifier"],
                issue_id=row["issue_id"],
            ),
            snapshot_date=date.fromisoformat(row["snapshot_date"]),
            fetched_at=datetime.fromisoformat(row["fetched_at"]),
            cached=bool(row["cached"]),
            stale=bool(row["stale"]),
            partial=bool(row["partial"]),
            warnings=tuple(json.loads(row["warnings_json"])),
            parser_version=row["parser_version"],
            schema_version=row["schema_version"],
            issued_shares=row["issued_shares"],
            issued_shares_as_of=(
                date.fromisoformat(row["issued_shares_as_of"])
                if row["issued_shares_as_of"]
                else None
            ),
            denominator=row["denominator"],
            total_in_ccass_shares=row["total_in_ccass_shares"],
            total_in_ccass_pct_of_issued=row["total_in_ccass_pct_of_issued"],
            non_ccass_shares=row["non_ccass_shares"],
            non_ccass_pct_of_issued=row["non_ccass_pct_of_issued"],
            participant_count=row["participant_count"],
            top5_pct_of_issued=row["top5_pct_of_issued"],
            top10_pct_of_issued=row["top10_pct_of_issued"],
            top5_pct_of_ccass=row["top5_pct_of_ccass"],
            top10_pct_of_ccass=row["top10_pct_of_ccass"],
            settlement_note=row["settlement_note"],
            attribution=row["attribution"],
            holdings=tuple(
                NormalizedHolding(
                    participant_id=holding["participant_id"],
                    participant_name=holding["participant_name"],
                    rank=holding["rank"],
                    shares=holding["shares"],
                    last_change=(
                        date.fromisoformat(holding["last_change"])
                        if holding["last_change"]
                        else None
                    ),
                    pct_of_issued=holding["pct_of_issued"],
                    pct_of_ccass=holding["pct_of_ccass"],
                    cumulative_pct_of_issued=holding["cumulative_pct_of_issued"],
                    participant_category=holding["participant_category"],
                )
                for holding in holding_rows
            ),
            provenance=RawProvenance(
                source_id=provenance_row["source_id"],
                safe_reference=provenance_row["safe_reference"],
                checksum_sha256=provenance_row["checksum_sha256"],
                fetched_at=datetime.fromisoformat(provenance_row["fetched_at"]),
                content_type=provenance_row["content_type"],
                byte_size=provenance_row["byte_size"],
            ),
        )

    def _migrate_legacy_snapshots(self) -> None:
        if not self._has_legacy_table():
            return
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT snapshots.id, snapshots.payload_json
                FROM snapshots
                LEFT JOIN legacy_snapshot_imports
                    ON legacy_snapshot_imports.legacy_snapshot_id = snapshots.id
                WHERE legacy_snapshot_imports.legacy_snapshot_id IS NULL
                ORDER BY snapshots.id
                """
            ).fetchall()
        for row in rows:
            normalized_id: int | None = None
            status = "IMPORTED"
            safe_error: str | None = None
            try:
                response = CcassResponse.model_validate_json(row["payload_json"])
                normalized_id = self.save_response(
                    response,
                    provenance_bytes=row["payload_json"].encode("utf-8"),
                    provenance_reference=f"legacy:snapshots:{row['id']}",
                )
            except (ValueError, sqlite3.Error) as exc:
                status = "PRESERVED_LEGACY_ONLY"
                safe_error = type(exc).__name__
            with self._transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO legacy_snapshot_imports(
                        legacy_snapshot_id, normalized_snapshot_id, imported_at, status, safe_error
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        normalized_id,
                        datetime.now(UTC).isoformat(),
                        status,
                        safe_error,
                    ),
                )

    def _has_legacy_table(self) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'snapshots'"
            ).fetchone()
        return row is not None

    def _transaction(self) -> "_Transaction":
        return _Transaction(self._connect)


class _Transaction:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self._connect = connect
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        self.connection = self._connect()
        self.connection.execute("BEGIN IMMEDIATE")
        return self.connection

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.connection is None:
            return
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
