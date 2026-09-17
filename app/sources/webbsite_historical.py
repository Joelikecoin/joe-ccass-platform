"""Read-only adapter for the proven Webb-site historical canonical index."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

from app.core.normalizers import normalize_stock_code
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata


WEBB_HISTORICAL_SOURCE_ID = "webbsite_archive"
WEBB_HISTORICAL_SOURCE_NAME = "Webb-site repository archive"
WEBB_HISTORICAL_COVERAGE_END = date(2025, 12, 24)


class WebbHistoricalSqliteSource:
    source_id = WEBB_HISTORICAL_SOURCE_ID
    page_count = 1

    def __init__(self, path: Path) -> None:
        self.path = path

    async def available_dates(self, code: str) -> tuple[date, ...]:
        normalized = normalize_stock_code(code)
        aliases = (normalized, normalized[-4:])
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT snapshot_date FROM historical_snapshot "
                "WHERE stock_code IN (?, ?) ORDER BY snapshot_date",
                aliases,
            ).fetchall()
        return tuple(date.fromisoformat(row[0]) for row in rows)

    async def get_holdings_for_date(
        self,
        code: str,
        requested_date: date,
        *,
        limit: int = 10_000,
    ) -> CcassResponse:
        normalized = normalize_stock_code(code)
        aliases = (normalized, normalized[-4:])
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT issue_id, participant_id, participant_name, holding, "
                "issued_shares, source_record_date "
                "FROM historical_snapshot WHERE stock_code IN (?, ?) AND snapshot_date = ? "
                "ORDER BY holding DESC, participant_id LIMIT ?",
                (*aliases, requested_date.isoformat(), max(1, limit)),
            ).fetchall()
        if not rows:
            raise PlatformError(
                ErrorCode.DATE_UNAVAILABLE,
                f"No Webb-site archive snapshot is available for {normalized} on {requested_date}.",
                status_code=404,
            )
        issue_id = int(rows[0][0])
        issued = int(rows[0][4]) if rows[0][4] is not None else None
        source_record_date = (
            date.fromisoformat(rows[0][5]) if rows[0][5] else requested_date
        )
        holdings = [
            HoldingRow(
                rank=index,
                participant_id=str(row[1]),
                participant=str(row[2]),
                shares=int(row[3]),
                last_change=None,
                pct_of_issued=(float(row[3]) / issued * 100 if issued else 0.0),
                pct_of_ccass=None,
                cumulative_pct_of_issued=None,
                participant_category=None,
            )
            for index, row in enumerate(rows, start=1)
        ]
        total = sum(row.shares for row in holdings)
        top5 = sum(row.shares for row in holdings[:5])
        top10 = sum(row.shares for row in holdings[:10])
        return CcassResponse(
            metadata=SourceMetadata(
                code=normalized,
                issue_id=issue_id,
                holdings_date=requested_date,
                fetched_at=datetime.now(UTC),
                source_url=f"webbsite-archive://{issue_id}/{requested_date.isoformat()}",
                source_name=WEBB_HISTORICAL_SOURCE_NAME,
                attribution=(
                    "David Webb original Webb-site repository archive; "
                    "coverage through 2025-12-24"
                ),
            ),
            holdings_summary=HoldingsSummary(
                total_in_ccass_shares=total,
                total_in_ccass_pct_of_issued=(total / issued * 100 if issued else None),
                issued_shares=issued,
                issued_shares_as_of=source_record_date,
                non_ccass_shares=(max(issued - total, 0) if issued else None),
                non_ccass_pct_of_issued=(max(issued - total, 0) / issued * 100 if issued else None),
                participant_count=len(holdings),
                top5_pct_of_issued=(top5 / issued * 100 if issued else None),
                top10_pct_of_issued=(top10 / issued * 100 if issued else None),
            ),
            holdings=holdings,
            data_quality_warnings=(
                "HISTORICAL_COVERAGE_END=2025-12-24",
            ),
        )

    def _connect(self) -> sqlite3.Connection:
        if not self.path.exists():
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                "The configured Webb historical archive index is unavailable.",
                status_code=503,
            )
        connection = sqlite3.connect(f"{self.path.resolve().as_uri()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        return connection
