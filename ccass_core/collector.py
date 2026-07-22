import argparse
import asyncio
import csv
import json
import logging
import os
import sqlite3
import tempfile
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.errors import PlatformError
from app.models import CcassResponse
from app.sources.webbsite import WebbsiteClient
from ccass_core.fetch_webb import fetch_webb_holdings
from ccass_core.normalize import normalize_stock_code

logger = logging.getLogger(__name__)

DEFAULT_WATCHLIST = ("01592",)
CSV_COLUMNS = (
    "code",
    "name",
    "issue_id",
    "holdings_date",
    "rank",
    "participant_id",
    "participant",
    "shares",
    "last_change",
    "pct_of_issued",
    "cumulative_pct_of_issued",
    "participant_category",
    "total_in_ccass_shares",
    "total_in_ccass_pct_of_issued",
    "issued_shares",
    "non_ccass_shares",
    "non_ccass_pct_of_issued",
    "snapshot_fetched_at",
    "source_cached",
    "settlement_note",
)


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    watchlist: tuple[str, ...] = DEFAULT_WATCHLIST
    sqlite_path: Path = Path("data/ccass_snapshots.db")
    csv_output_path: Path = Path("data/ccass_snapshot.csv")
    holdings_limit: int = 100


class SnapshotStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    holdings_date TEXT,
                    source_cached INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_code_id ON snapshots(code, id DESC)"
            )

    def save(self, response: CcassResponse) -> None:
        metadata = response.metadata
        payload = response.model_dump(mode="json")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO snapshots(code, fetched_at, holdings_date, source_cached, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    metadata.code,
                    metadata.fetched_at.isoformat(),
                    metadata.holdings_date.isoformat() if metadata.holdings_date else None,
                    int(metadata.cached),
                    json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                ),
            )

    def latest(self, code: str) -> CcassResponse | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM snapshots WHERE code = ? ORDER BY id DESC LIMIT 1",
                (code,),
            ).fetchone()
        return CcassResponse.model_validate_json(row["payload_json"]) if row else None

    def latest_all(self) -> list[CcassResponse]:
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
        return [CcassResponse.model_validate_json(row["payload_json"]) for row in rows]

    def previous_for(
        self, code: str, current: CcassResponse
    ) -> CcassResponse | None:
        """Return the newest stored snapshot that predates the current snapshot."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM snapshots WHERE code = ? ORDER BY id DESC",
                (code,),
            ).fetchall()
        for row in rows:
            candidate = CcassResponse.model_validate_json(row["payload_json"])
            if candidate.metadata.holdings_date and current.metadata.holdings_date:
                if candidate.metadata.holdings_date < current.metadata.holdings_date:
                    return candidate
                continue
            if candidate.metadata.fetched_at < current.metadata.fetched_at:
                return candidate
        return None


async def collect_watchlist(
    config: CollectorConfig,
    *,
    settings: Settings | None = None,
    fetcher: Callable[[str, int], Awaitable[CcassResponse]] | None = None,
) -> tuple[list[CcassResponse], dict[str, str]]:
    """Run one low-frequency collection pass; scheduling is intentionally external."""
    store = SnapshotStore(config.sqlite_path)
    source_settings = settings or Settings()
    mirror_client = WebbsiteClient(source_settings) if fetcher is None else None

    async def default_fetcher(code: str, limit: int) -> CcassResponse:
        return await fetch_webb_holdings(
            code,
            limit=limit,
            settings=source_settings,
            client=mirror_client,
        )

    selected_fetcher = fetcher or default_fetcher
    collected: list[CcassResponse] = []
    failures: dict[str, str] = {}
    for raw_code in config.watchlist:
        code = normalize_stock_code(raw_code)
        try:
            response = await selected_fetcher(code, config.holdings_limit)
        except PlatformError as exc:
            failures[code] = f"{exc.code}: {exc.message}"
            logger.warning("Collector fetch failed code=%s error_type=%s", code, exc.code)
            continue
        store.save(response)
        collected.append(response)

    if store.latest_all():
        export_latest_csv(store, config.csv_output_path)
    return collected, failures


def export_latest_csv(store: SnapshotStore, output_path: Path) -> None:
    """Atomically export each stock's latest snapshot using the Google Drive CSV schema."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for response in store.latest_all():
                for row in response.holdings:
                    writer.writerow(_csv_row(response, row.model_dump(mode="python")))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def _csv_row(response: CcassResponse, holding: dict) -> dict[str, object]:
    metadata = response.metadata
    summary = response.holdings_summary
    return {
        "code": metadata.code,
        "name": metadata.name or "DATA NOT AVAILABLE",
        "issue_id": metadata.issue_id,
        "holdings_date": metadata.holdings_date.isoformat() if metadata.holdings_date else "",
        "rank": holding["rank"],
        "participant_id": holding["participant_id"],
        "participant": holding["participant"],
        "shares": holding["shares"],
        "last_change": holding["last_change"].isoformat() if holding["last_change"] else "",
        "pct_of_issued": holding["pct_of_issued"],
        "cumulative_pct_of_issued": _csv_optional(holding["cumulative_pct_of_issued"]),
        "participant_category": holding["participant_category"] or "",
        "total_in_ccass_shares": _csv_optional(summary.total_in_ccass_shares),
        "total_in_ccass_pct_of_issued": _csv_optional(
            summary.total_in_ccass_pct_of_issued
        ),
        "issued_shares": _csv_optional(summary.issued_shares),
        "non_ccass_shares": _csv_optional(summary.non_ccass_shares),
        "non_ccass_pct_of_issued": _csv_optional(summary.non_ccass_pct_of_issued),
        "snapshot_fetched_at": metadata.fetched_at.isoformat(),
        "source_cached": str(metadata.cached).lower(),
        "settlement_note": metadata.settlement_note,
    }


def _csv_optional(value: object | None) -> object:
    return "" if value is None else value


def parse_watchlist(value: str) -> tuple[str, ...]:
    values = [item.strip() for item in value.split(",") if item.strip()]
    return tuple(normalize_stock_code(item) for item in values) or DEFAULT_WATCHLIST


def collector_config_from_args(argv: Sequence[str] | None = None) -> CollectorConfig:
    parser = argparse.ArgumentParser(description="Low-frequency CCASS mirror snapshot collector")
    parser.add_argument(
        "--watchlist",
        default=os.getenv("CCASS_WATCHLIST", ",".join(DEFAULT_WATCHLIST)),
        help="Comma-separated HK stock codes; default: 01592",
    )
    parser.add_argument(
        "--sqlite",
        default=os.getenv("CCASS_SQLITE_PATH", "data/ccass_snapshots.db"),
    )
    parser.add_argument(
        "--output",
        default=os.getenv("CCASS_CSV_OUTPUT_PATH", "data/ccass_snapshot.csv"),
        help="CSV path, which may be inside a local Google Drive sync folder",
    )
    parser.add_argument("--limit", type=int, default=100, choices=range(1, 101))
    args = parser.parse_args(argv)
    return CollectorConfig(
        watchlist=parse_watchlist(args.watchlist),
        sqlite_path=Path(args.sqlite),
        csv_output_path=Path(args.output),
        holdings_limit=args.limit,
    )


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    config = collector_config_from_args(argv)
    collected, failures = asyncio.run(collect_watchlist(config))
    logger.info("Collector completed collected=%s failed=%s", len(collected), len(failures))
    return 1 if failures else 0


def configure_logging() -> None:
    """Keep collector status visible without logging third-party request URLs or parameters."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


if __name__ == "__main__":
    raise SystemExit(main())
