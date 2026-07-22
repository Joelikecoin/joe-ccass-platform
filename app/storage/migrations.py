import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    statements: tuple[str, ...]


MIGRATION_1 = Migration(
    version=1,
    name="normalized_historical_foundation",
    statements=(
        """
        CREATE TABLE stocks (
            code TEXT PRIMARY KEY CHECK(length(code) = 5),
            current_name TEXT,
            market TEXT NOT NULL DEFAULT 'HK',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE source_issue_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL REFERENCES stocks(code),
            source_id TEXT NOT NULL,
            issue_id TEXT NOT NULL,
            first_verified_at TEXT NOT NULL,
            last_verified_at TEXT NOT NULL,
            evidence_identifier TEXT NOT NULL,
            UNIQUE(stock_code, source_id, issue_id)
        )
        """,
        """
        CREATE TABLE raw_provenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            safe_reference TEXT NOT NULL,
            checksum_sha256 TEXT NOT NULL CHECK(length(checksum_sha256) = 64),
            fetched_at TEXT NOT NULL,
            content_type TEXT NOT NULL,
            byte_size INTEGER NOT NULL CHECK(byte_size >= 0),
            UNIQUE(source_id, checksum_sha256)
        )
        """,
        """
        CREATE TABLE ccass_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL REFERENCES stocks(code),
            snapshot_date TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_identifier TEXT NOT NULL,
            issue_id INTEGER NOT NULL,
            fetched_at TEXT NOT NULL,
            source_name TEXT NOT NULL,
            cached INTEGER NOT NULL CHECK(cached IN (0, 1)),
            stale INTEGER NOT NULL CHECK(stale IN (0, 1)),
            partial INTEGER NOT NULL CHECK(partial IN (0, 1)),
            parser_version TEXT NOT NULL,
            schema_version INTEGER NOT NULL CHECK(schema_version >= 1),
            warnings_json TEXT NOT NULL,
            issued_shares INTEGER CHECK(issued_shares IS NULL OR issued_shares >= 0),
            issued_shares_as_of TEXT,
            denominator TEXT NOT NULL,
            total_in_ccass_shares INTEGER,
            total_in_ccass_pct_of_issued REAL,
            non_ccass_shares INTEGER,
            non_ccass_pct_of_issued REAL,
            participant_count INTEGER NOT NULL CHECK(participant_count >= 0),
            top5_pct_of_issued REAL,
            top10_pct_of_issued REAL,
            top5_pct_of_ccass REAL,
            top10_pct_of_ccass REAL,
            settlement_note TEXT NOT NULL,
            attribution TEXT NOT NULL,
            provenance_id INTEGER NOT NULL REFERENCES raw_provenance(id),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(stock_code, snapshot_date, source_id)
        )
        """,
        """
        CREATE TABLE ccass_holdings (
            snapshot_id INTEGER NOT NULL REFERENCES ccass_snapshots(id) ON DELETE CASCADE,
            participant_id TEXT NOT NULL,
            participant_name TEXT NOT NULL,
            rank INTEGER NOT NULL CHECK(rank > 0),
            shares INTEGER NOT NULL CHECK(shares >= 0),
            last_change TEXT,
            pct_of_issued REAL NOT NULL CHECK(pct_of_issued >= 0),
            pct_of_ccass REAL CHECK(pct_of_ccass IS NULL OR pct_of_ccass >= 0),
            cumulative_pct_of_issued REAL,
            participant_category TEXT,
            PRIMARY KEY(snapshot_id, participant_id),
            UNIQUE(snapshot_id, rank)
        )
        """,
        """
        CREATE TABLE collector_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            source_id TEXT NOT NULL,
            requested_codes_json TEXT NOT NULL,
            success_count INTEGER NOT NULL DEFAULT 0,
            partial_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            safe_details_json TEXT NOT NULL DEFAULT '{}'
        )
        """,
        """
        CREATE TABLE source_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER REFERENCES collector_runs(id),
            source_id TEXT NOT NULL,
            stock_code TEXT,
            occurred_at TEXT NOT NULL,
            error_code TEXT NOT NULL,
            safe_message TEXT NOT NULL,
            retry_recommended INTEGER NOT NULL CHECK(retry_recommended IN (0, 1)),
            retry_after_seconds INTEGER,
            safe_details_json TEXT NOT NULL DEFAULT '{}'
        )
        """,
        """
        CREATE TABLE legacy_snapshot_imports (
            legacy_snapshot_id INTEGER PRIMARY KEY,
            normalized_snapshot_id INTEGER REFERENCES ccass_snapshots(id),
            imported_at TEXT NOT NULL,
            status TEXT NOT NULL,
            safe_error TEXT
        )
        """,
        "CREATE INDEX idx_ccass_snapshots_code_date "
        "ON ccass_snapshots(stock_code, snapshot_date DESC)",
        "CREATE INDEX idx_ccass_holdings_participant "
        "ON ccass_holdings(participant_id, snapshot_id)",
        "CREATE INDEX idx_source_errors_source_time ON source_errors(source_id, occurred_at DESC)",
    ),
)

MIGRATION_2 = Migration(
    version=2,
    name="collector_run_items",
    statements=(
        """
        CREATE TABLE collector_run_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL REFERENCES collector_runs(id) ON DELETE CASCADE,
            stock_code TEXT NOT NULL CHECK(length(stock_code) = 5),
            status TEXT NOT NULL CHECK(status IN ('SUCCESS', 'PARTIAL', 'ERROR')),
            source_id TEXT NOT NULL,
            snapshot_id INTEGER REFERENCES ccass_snapshots(id) ON DELETE SET NULL,
            snapshot_date TEXT,
            partial INTEGER NOT NULL CHECK(partial IN (0, 1)),
            safe_details_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            UNIQUE(run_id, stock_code)
        )
        """,
        "CREATE INDEX idx_collector_run_items_run_status ON collector_run_items(run_id, status)",
    ),
)


MIGRATIONS: tuple[Migration, ...] = (MIGRATION_1, MIGRATION_2)
SCHEMA_VERSION = MIGRATIONS[-1].version


def apply_migrations(
    connection: sqlite3.Connection,
    *,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> int:
    """Apply additive SQLite migrations transactionally and return the schema version."""
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    applied = {
        row[0] for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    }
    for migration in migrations:
        if migration.version in applied:
            continue
        _apply_one(connection, migration)
        applied.add(migration.version)
    return max(applied, default=0)


def _apply_one(connection: sqlite3.Connection, migration: Migration) -> None:
    try:
        connection.execute("BEGIN IMMEDIATE")
        for statement in migration.statements:
            connection.execute(statement)
        connection.execute(
            "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
            (migration.version, migration.name, datetime.now(UTC).isoformat()),
        )
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
