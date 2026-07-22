import argparse
import asyncio
import csv
import logging
import os
import tempfile
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.errors import PlatformError
from app.models import CcassResponse
from app.sources.webbsite import WebbsiteClient
from ccass_core.fetch_webb import fetch_webb_holdings
from app.storage.history import NormalizedSnapshotRepository
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
    """Compatibility facade backed by the normalized historical repository."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.repository = NormalizedSnapshotRepository(path)

    def save(self, response: CcassResponse) -> None:
        self.repository.save_response(response)

    def latest(self, code: str) -> CcassResponse | None:
        snapshot = self.repository.latest(code)
        if snapshot:
            return snapshot.to_response()
        return next(
            (
                response
                for response in self.repository.legacy_latest_responses()
                if response.metadata.code == code
            ),
            None,
        )

    def latest_all(self) -> list[CcassResponse]:
        by_code = {
            snapshot.stock.code: snapshot.to_response()
            for snapshot in self.repository.latest_all()
        }
        for response in self.repository.legacy_latest_responses():
            by_code.setdefault(response.metadata.code, response)
        return [by_code[code] for code in sorted(by_code)]

    def previous_for(
        self, code: str, current: CcassResponse
    ) -> CcassResponse | None:
        if current.metadata.holdings_date:
            snapshot = self.repository.previous(
                code,
                before_date=current.metadata.holdings_date,
            )
            if snapshot:
                return snapshot.to_response()
        candidates = [
            response
            for response in self.repository.legacy_responses(code)
            if response.metadata.code == code
            and response.metadata.fetched_at < current.metadata.fetched_at
        ]
        if candidates:
            return max(candidates, key=lambda response: response.metadata.fetched_at)
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
