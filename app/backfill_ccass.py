import argparse
import asyncio
import json
import logging
import os
import sqlite3
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal, Protocol

from pydantic import ValidationError

from app.config import Settings
from app.domain.history import BackfillRunItemRecord, BackfillRunRecord, HistoricalSnapshot
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse
from app.sources.google_drive_csv import GoogleDriveCsvSource
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.normalize import normalize_stock_code

logger = logging.getLogger(__name__)

DEFAULT_DATABASE = Path("data/ccass_snapshots.db")
DEFAULT_COLLECTION_LIMIT = 10_000


class HistoricalSource(Protocol):
    source_id: str
    page_count: int

    async def available_dates(self, code: str) -> tuple[date, ...]: ...

    async def get_holdings_for_date(
        self,
        code: str,
        requested_date: date,
        *,
        limit: int = DEFAULT_COLLECTION_LIMIT,
    ) -> CcassResponse: ...


@dataclass(frozen=True, slots=True)
class BackfillConfig:
    stock_code: str
    sqlite_path: Path = DEFAULT_DATABASE
    source_mode: Literal["auto", "webbsite", "google_drive_csv"] = "auto"
    date_from: date | None = None
    date_to: date | None = None
    latest_count: int | None = None
    resume: bool = False
    dry_run: bool = False
    max_dates: int = 366
    max_pages: int = 1
    request_sleep_seconds: float = 1.0
    retry_attempts: int = 2
    collection_limit: int = DEFAULT_COLLECTION_LIMIT


@dataclass(frozen=True, slots=True)
class BackfillResult:
    run_id: int | None
    status: Literal["SUCCESS", "PARTIAL", "ERROR"]
    success_count: int
    partial_count: int
    error_count: int
    skipped_count: int


async def run_backfill(
    config: BackfillConfig,
    *,
    settings: Settings | None = None,
    source: HistoricalSource | None = None,
    repository: NormalizedSnapshotRepository | None = None,
    sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> BackfillResult:
    normalized_code = normalize_stock_code(config.stock_code)
    _validate_config(config)
    source_settings = settings or Settings(data_source=config.source_mode)
    selected_source = source or _historical_source(source_settings, config.source_mode)
    source_id = selected_source.source_id
    if selected_source.page_count > config.max_pages:
        raise PlatformError(
            ErrorCode.TOO_LARGE,
            "Historical source page count exceeds the configured backfill bound.",
            status_code=400,
        )

    write_repository = repository
    if write_repository is None and not config.dry_run:
        write_repository = NormalizedSnapshotRepository(config.sqlite_path)

    resumed_run: BackfillRunRecord | None = None
    existing_items: list[BackfillRunItemRecord] = []
    if config.resume:
        if write_repository is not None:
            resumed_run = write_repository.get_resumable_backfill_run(
                normalized_code,
                source_id=source_id,
            )
            if resumed_run:
                existing_items = write_repository.get_backfill_items(resumed_run.run_id or 0)
        else:
            resumed_run, existing_items = _read_resume_state(
                config.sqlite_path,
                normalized_code,
                source_id,
            )
        if resumed_run is None:
            raise PlatformError(
                ErrorCode.DATE_UNAVAILABLE,
                f"No resumable backfill run exists for {normalized_code} and {source_id}.",
                status_code=404,
            )
        requested_dates = resumed_run.requested_dates
    elif config.latest_count is not None:
        available_dates = await _call_with_retry(
            lambda: selected_source.available_dates(normalized_code),
            retry_attempts=config.retry_attempts,
            sleeper=sleeper,
            retry_sleep=config.request_sleep_seconds,
        )
        if not available_dates:
            raise PlatformError(
                ErrorCode.DATE_UNAVAILABLE,
                f"No verified historical dates are available for {normalized_code}.",
                status_code=404,
            )
        requested_dates = tuple(sorted(set(available_dates))[-config.latest_count :])
    else:
        requested_dates = _date_range(config.date_from, config.date_to)

    if len(requested_dates) > config.max_dates:
        raise PlatformError(
            ErrorCode.TOO_LARGE,
            "Requested backfill date count exceeds the configured bound.",
            status_code=400,
        )

    run_id: int | None = resumed_run.run_id if resumed_run else None
    if write_repository is not None:
        if resumed_run:
            write_repository.resume_backfill_run(run_id or 0)
        else:
            run_id = write_repository.create_backfill_run(
                BackfillRunRecord(
                    stock_code=normalized_code,
                    source_id=source_id,
                    requested_from=config.date_from,
                    requested_to=config.date_to,
                    latest_count=config.latest_count,
                    requested_dates=requested_dates,
                    started_at=datetime.now(UTC),
                    safe_details={
                        "max_dates": config.max_dates,
                        "max_pages": config.max_pages,
                        "retry_attempts": config.retry_attempts,
                    },
                )
            )

    prior_by_date = {item.requested_date: item for item in existing_items}
    dry_items: dict[date, BackfillRunItemRecord] = dict(prior_by_date)
    request_count = 0
    for requested_date in requested_dates:
        prior = prior_by_date.get(requested_date)
        if prior and prior.status in {"SUCCESS", "PARTIAL", "SKIPPED"}:
            continue

        existing_snapshot = _existing_snapshot(
            write_repository,
            config.sqlite_path,
            normalized_code,
            requested_date,
            source_id,
        )
        if existing_snapshot:
            item = BackfillRunItemRecord(
                run_id=run_id or 1,
                requested_date=requested_date,
                status="SKIPPED",
                source_id=source_id,
                snapshot_id=existing_snapshot,
                safe_details={"reason": "snapshot_exists"},
            )
            _store_item(write_repository, item, dry_items)
            continue

        if request_count:
            await sleeper(config.request_sleep_seconds)
        request_count += 1
        try:
            response = await _call_with_retry(
                lambda value=requested_date: selected_source.get_holdings_for_date(
                    normalized_code,
                    value,
                    limit=config.collection_limit,
                ),
                retry_attempts=config.retry_attempts,
                sleeper=sleeper,
                retry_sleep=config.request_sleep_seconds,
            )
            snapshot = _validated_snapshot(
                response,
                requested_code=normalized_code,
                requested_date=requested_date,
                source_id=source_id,
            )
        except PlatformError as exc:
            status: Literal["ERROR", "SKIPPED"] = (
                "SKIPPED" if exc.code == ErrorCode.DATE_UNAVAILABLE else "ERROR"
            )
            logger.warning(
                "Backfill date failed code=%s date=%s source=%s error_type=%s",
                normalized_code,
                requested_date.isoformat(),
                source_id,
                exc.code,
            )
            item = BackfillRunItemRecord(
                run_id=run_id or 1,
                requested_date=requested_date,
                status=status,
                source_id=source_id,
                error_code=str(exc.code),
                safe_message=_safe_error_message(exc),
                retry_recommended=exc.retry_recommended,
                safe_details={"reason": "date_unavailable" if status == "SKIPPED" else "source"},
            )
            _store_item(write_repository, item, dry_items)
            continue
        except Exception as exc:
            logger.warning(
                "Backfill source failed code=%s date=%s source=%s error_type=%s",
                normalized_code,
                requested_date.isoformat(),
                source_id,
                type(exc).__name__,
            )
            item = BackfillRunItemRecord(
                run_id=run_id or 1,
                requested_date=requested_date,
                status="ERROR",
                source_id=source_id,
                error_code="SOURCE_ERROR",
                safe_message="Historical source request failed.",
                retry_recommended=False,
                safe_details={"reason": "source", "error_type": type(exc).__name__},
            )
            _store_item(write_repository, item, dry_items)
            continue

        try:
            snapshot_id = write_repository.save(snapshot) if write_repository else None
        except Exception as exc:
            logger.warning(
                "Backfill storage failed code=%s date=%s source=%s error_type=%s",
                normalized_code,
                requested_date.isoformat(),
                source_id,
                type(exc).__name__,
            )
            item = BackfillRunItemRecord(
                run_id=run_id or 1,
                requested_date=requested_date,
                status="ERROR",
                source_id=source_id,
                error_code="STORAGE_ERROR",
                safe_message="Historical snapshot storage failed.",
                retry_recommended=True,
                safe_details={"reason": "storage", "error_type": type(exc).__name__},
            )
            _store_item(write_repository, item, dry_items)
            continue

        item = BackfillRunItemRecord(
            run_id=run_id or 1,
            requested_date=requested_date,
            status="PARTIAL" if snapshot.partial else "SUCCESS",
            source_id=source_id,
            snapshot_id=snapshot_id,
            partial=snapshot.partial,
            safe_details={
                "rows": len(snapshot.holdings),
                "participant_count": snapshot.participant_count,
            },
        )
        _store_item(write_repository, item, dry_items)

    final_items = (
        write_repository.get_backfill_items(run_id or 0)
        if write_repository is not None
        else list(dry_items.values())
    )
    counts = _counts(final_items)
    status = _batch_status(**counts)
    if write_repository is not None:
        write_repository.complete_backfill_run(
            run_id or 0,
            completed_at=datetime.now(UTC),
            status=status,
            safe_details={"requested_dates": len(requested_dates), "dry_run": False},
            **counts,
        )
    return BackfillResult(run_id=run_id, status=status, **counts)


def _historical_source(settings: Settings, source_mode: str) -> HistoricalSource:
    if source_mode in {"auto", "google_drive_csv"} and settings.ccass_csv_url.strip():
        return GoogleDriveCsvSource(settings)
    raise PlatformError(
        ErrorCode.DATE_UNAVAILABLE,
        f"Source mode {source_mode} cannot provide a verified requested-date snapshot.",
        status_code=400,
    )


def _validate_config(config: BackfillConfig) -> None:
    if config.max_dates < 1 or config.max_pages < 1:
        raise ValueError("backfill bounds must be positive")
    if config.request_sleep_seconds < 0 or config.retry_attempts < 1:
        raise ValueError("backfill sleep/retry settings are invalid")
    if config.collection_limit < 1:
        raise ValueError("backfill collection limit must be positive")
    range_selected = config.date_from is not None or config.date_to is not None
    selection_count = (
        int(range_selected) + int(config.latest_count is not None) + int(config.resume)
    )
    if selection_count != 1:
        raise ValueError("select exactly one of date range, latest, or resume")
    if range_selected:
        if config.date_from is None or config.date_to is None:
            raise ValueError("both date_from and date_to are required")
        if config.date_from > config.date_to:
            raise ValueError("date_from must not be after date_to")
        if (config.date_to - config.date_from).days + 1 > config.max_dates:
            raise ValueError("requested date range exceeds max_dates")
    if config.latest_count is not None:
        if config.latest_count < 1 or config.latest_count > config.max_dates:
            raise ValueError("latest_count must be within max_dates")


def _date_range(date_from: date | None, date_to: date | None) -> tuple[date, ...]:
    if date_from is None or date_to is None:
        raise ValueError("date range is incomplete")
    return tuple(
        date_from + timedelta(days=offset) for offset in range((date_to - date_from).days + 1)
    )


async def _call_with_retry(
    call: Callable[[], Awaitable[object]],
    *,
    retry_attempts: int,
    sleeper: Callable[[float], Awaitable[None]],
    retry_sleep: float,
):
    for attempt in range(1, retry_attempts + 1):
        try:
            return await call()
        except PlatformError as exc:
            if not exc.retry_recommended or attempt == retry_attempts:
                raise
            await sleeper(retry_sleep)
    raise RuntimeError("bounded retry loop exhausted")


def _validated_snapshot(
    response: CcassResponse,
    *,
    requested_code: str,
    requested_date: date,
    source_id: str,
) -> HistoricalSnapshot:
    if (
        response.metadata.code != requested_code
        or response.metadata.holdings_date != requested_date
    ):
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "Historical source returned a different stock code or snapshot date.",
            status_code=502,
        )
    try:
        partial = len(response.holdings) != response.holdings_summary.participant_count or any(
            warning.startswith("PARTIAL_DATA:") for warning in response.data_quality_warnings
        )
        return HistoricalSnapshot.from_response(response, source_id=source_id, partial=partial)
    except (ValueError, ValidationError) as exc:
        raise PlatformError(
            ErrorCode.PARSE_ERROR,
            "Historical source returned an invalid snapshot.",
            status_code=502,
        ) from exc


def _safe_error_message(error: PlatformError) -> str:
    if error.code == ErrorCode.DATE_UNAVAILABLE:
        return "Verified snapshot is unavailable for the requested date."
    return "Historical source request failed."


def _store_item(
    repository: NormalizedSnapshotRepository | None,
    item: BackfillRunItemRecord,
    dry_items: dict[date, BackfillRunItemRecord],
) -> None:
    dry_items[item.requested_date] = item
    if repository is not None:
        repository.record_backfill_result(item)


def _existing_snapshot(
    repository: NormalizedSnapshotRepository | None,
    path: Path,
    code: str,
    snapshot_date: date,
    source_id: str,
) -> int | None:
    if repository is not None:
        return repository.snapshot_id_on(code, snapshot_date, source_id=source_id)
    if not path.exists():
        return None
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        row = connection.execute(
            """
            SELECT id FROM ccass_snapshots
            WHERE stock_code = ? AND snapshot_date = ? AND source_id = ?
            """,
            (code, snapshot_date.isoformat(), source_id),
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        if "connection" in locals():
            connection.close()
    return int(row[0]) if row else None


def _read_resume_state(
    path: Path,
    stock_code: str,
    source_id: str,
) -> tuple[BackfillRunRecord | None, list[BackfillRunItemRecord]]:
    if not path.exists():
        return None, []
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT runs.* FROM backfill_runs AS runs
            WHERE runs.stock_code = ? AND runs.source_id = ?
              AND (runs.status = 'RUNNING' OR EXISTS (
                SELECT 1 FROM backfill_run_items AS items
                WHERE items.run_id = runs.id AND items.status = 'ERROR'
              ))
            ORDER BY runs.id DESC LIMIT 1
            """,
            (stock_code, source_id),
        ).fetchone()
        if row is None:
            return None, []
        run = _run_from_row(row)
        item_rows = connection.execute(
            "SELECT * FROM backfill_run_items WHERE run_id = ? ORDER BY requested_date",
            (run.run_id,),
        ).fetchall()
        items = [_item_from_row(value) for value in item_rows]
        return run, items
    except sqlite3.Error:
        return None, []
    finally:
        if "connection" in locals():
            connection.close()


def _run_from_row(row: sqlite3.Row) -> BackfillRunRecord:
    return BackfillRunRecord(
        run_id=int(row["id"]),
        stock_code=row["stock_code"],
        source_id=row["source_id"],
        requested_from=date.fromisoformat(row["requested_from"]) if row["requested_from"] else None,
        requested_to=date.fromisoformat(row["requested_to"]) if row["requested_to"] else None,
        latest_count=row["latest_count"],
        requested_dates=tuple(
            date.fromisoformat(value) for value in json.loads(row["requested_dates_json"])
        ),
        cursor_date=date.fromisoformat(row["cursor_date"]) if row["cursor_date"] else None,
        started_at=datetime.fromisoformat(row["started_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        status=row["status"],
        success_count=int(row["success_count"]),
        partial_count=int(row["partial_count"]),
        error_count=int(row["error_count"]),
        skipped_count=int(row["skipped_count"]),
        safe_details=json.loads(row["safe_details_json"]),
    )


def _item_from_row(row: sqlite3.Row) -> BackfillRunItemRecord:
    return BackfillRunItemRecord(
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


def _counts(items: Sequence[BackfillRunItemRecord]) -> dict[str, int]:
    return {
        "success_count": sum(item.status == "SUCCESS" for item in items),
        "partial_count": sum(item.status == "PARTIAL" for item in items),
        "error_count": sum(item.status == "ERROR" for item in items),
        "skipped_count": sum(item.status == "SKIPPED" for item in items),
    }


def _batch_status(
    *,
    success_count: int,
    partial_count: int,
    error_count: int,
    skipped_count: int,
) -> Literal["SUCCESS", "PARTIAL", "ERROR"]:
    if error_count and not (success_count or partial_count or skipped_count):
        return "ERROR"
    if error_count or partial_count or skipped_count:
        return "PARTIAL"
    return "SUCCESS"


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("dates must use YYYY-MM-DD") from exc


def backfill_config_from_args(argv: Sequence[str] | None = None) -> BackfillConfig:
    defaults = Settings()
    parser = argparse.ArgumentParser(description="Resumable source-neutral CCASS backfill")
    parser.add_argument("--stock", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--latest", type=int, dest="latest_count")
    selection.add_argument("--resume", action="store_true")
    selection.add_argument("--from", type=_parse_date, dest="date_from")
    parser.add_argument("--to", type=_parse_date, dest="date_to")
    parser.add_argument(
        "--source",
        choices=("auto", "webbsite", "google_drive_csv"),
        default=defaults.data_source,
    )
    parser.add_argument(
        "--sqlite",
        default=os.getenv("CCASS_SQLITE_PATH", str(DEFAULT_DATABASE)),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-dates", type=int, default=defaults.backfill_max_dates)
    parser.add_argument("--max-pages", type=int, default=defaults.backfill_max_pages)
    parser.add_argument(
        "--sleep",
        type=float,
        dest="request_sleep_seconds",
        default=defaults.backfill_request_sleep_seconds,
    )
    parser.add_argument(
        "--retry-attempts",
        type=int,
        default=defaults.backfill_retry_attempts,
    )
    args = parser.parse_args(argv)
    config = BackfillConfig(
        stock_code=args.stock,
        sqlite_path=Path(args.sqlite),
        source_mode=args.source,
        date_from=args.date_from,
        date_to=args.date_to,
        latest_count=args.latest_count,
        resume=args.resume,
        dry_run=args.dry_run,
        max_dates=args.max_dates,
        max_pages=args.max_pages,
        request_sleep_seconds=args.request_sleep_seconds,
        retry_attempts=args.retry_attempts,
    )
    try:
        normalize_stock_code(config.stock_code)
        _validate_config(config)
    except (PlatformError, ValueError) as exc:
        parser.error(str(exc))
    return config


def _exit_code(result: BackfillResult) -> int:
    if result.error_count:
        return 1
    if result.partial_count or result.skipped_count:
        return 2
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    config = backfill_config_from_args(argv)
    try:
        result = asyncio.run(run_backfill(config))
    except PlatformError as exc:
        logger.error("Backfill failed error_type=%s", exc.code)
        return 1
    logger.info(
        "Backfill completed status=%s success=%s partial=%s error=%s skipped=%s dry_run=%s",
        result.status,
        result.success_count,
        result.partial_count,
        result.error_count,
        result.skipped_count,
        config.dry_run,
    )
    return _exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
