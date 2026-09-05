"""Durable Longbridge snapshot storage with SQLite/PostgreSQL backends."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.models import CcassResponse


CREATE_SQLITE = """
CREATE TABLE IF NOT EXISTS longbridge_holdings (
    code TEXT NOT NULL,
    data_date TEXT NOT NULL,
    ccass_id TEXT NOT NULL,
    participant_name TEXT NOT NULL,
    holding_shares INTEGER NOT NULL,
    pct_of_issued REAL NOT NULL,
    pct_of_ccass REAL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (code, data_date, ccass_id)
)
"""

CREATE_POSTGRES = CREATE_SQLITE.replace("TEXT", "TEXT").replace("INTEGER", "BIGINT")


class LongbridgeSnapshotStore:
    def __init__(self, *, sqlite_path: Path, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.sqlite_path = sqlite_path
        if self.database_url and not self.database_url.startswith(("postgres://", "postgresql://")):
            raise RuntimeError("DATABASE_URL must be a PostgreSQL URL")

    @property
    def external(self) -> bool:
        return bool(self.database_url)

    def _connect_sqlite(self) -> sqlite3.Connection:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.sqlite_path)
        connection.execute(CREATE_SQLITE)
        connection.commit()
        return connection

    def _connect_postgres(self) -> Any:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "DATABASE_URL is set but psycopg is not installed; install psycopg[binary]."
            ) from exc
        connection = psycopg.connect(self.database_url)
        connection.execute(CREATE_POSTGRES)
        connection.commit()
        return connection

    def _connect(self) -> Any:
        return self._connect_postgres() if self.external else self._connect_sqlite()

    def upsert_response(self, response: CcassResponse) -> int:
        code = response.metadata.code
        data_date = response.metadata.holdings_date
        if data_date is None:
            raise ValueError("Longbridge persistence requires a data date")
        rows = [
            (
                code,
                data_date.isoformat(),
                row.participant_id,
                row.participant,
                row.shares,
                row.pct_of_issued,
                row.pct_of_ccass,
                "longbridge",
                response.metadata.fetched_at.isoformat(),
            )
            for row in response.holdings
        ]
        connection = self._connect()
        try:
            if self.external:
                query = """
                INSERT INTO longbridge_holdings
                (code,data_date,ccass_id,participant_name,holding_shares,pct_of_issued,pct_of_ccass,source,fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (code,data_date,ccass_id) DO UPDATE SET
                  participant_name=EXCLUDED.participant_name,
                  holding_shares=EXCLUDED.holding_shares,
                  pct_of_issued=EXCLUDED.pct_of_issued,
                  pct_of_ccass=EXCLUDED.pct_of_ccass,
                  source=EXCLUDED.source,
                  fetched_at=EXCLUDED.fetched_at
                """
            else:
                query = """
                INSERT INTO longbridge_holdings
                (code,data_date,ccass_id,participant_name,holding_shares,pct_of_issued,pct_of_ccass,source,fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(code,data_date,ccass_id) DO UPDATE SET
                  participant_name=excluded.participant_name,
                  holding_shares=excluded.holding_shares,
                  pct_of_issued=excluded.pct_of_issued,
                  pct_of_ccass=excluded.pct_of_ccass,
                  source=excluded.source,
                  fetched_at=excluded.fetched_at
                """
            connection.executemany(query, rows)
            connection.commit()
            return len(rows)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def count(self, *, code: str, data_date: str) -> int:
        connection = self._connect()
        try:
            placeholder = "%s" if self.external else "?"
            row = connection.execute(
                f"SELECT COUNT(*) FROM longbridge_holdings WHERE code={placeholder} AND data_date={placeholder}",
                (code, data_date),
            ).fetchone()
            return int(row[0])
        finally:
            connection.close()
