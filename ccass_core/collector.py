import argparse
import asyncio
import csv
import json
import logging
import os
import re
import tempfile
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from app.config import Settings
from app.domain.history import (
    CollectorRunItemRecord,
    CollectorRunRecord,
    HistoricalSnapshot,
    SourceErrorRecord,
)
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse
from app.services.ccass import CcassService
from app.services.holdings_lkg import (
    LKG_AGE_SECONDS_PREFIX,
    SOURCE_ERROR_CODE_PREFIX,
    SOURCE_ERROR_MESSAGE_PREFIX,
    SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX,
    SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX,
    FreshnessStatus,
    freshness_detail,
    freshness_status,
)
from app.sources.registry import build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.normalize import normalize_stock_code

logger = logging.getLogger(__name__)

DEFAULT_WATCHLIST = ("01592",)
DEFAULT_COLLECTION_LIMIT = 10_000
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
    "participant_count",
    "total_in_ccass_pct_of_issued",
    "issued_shares",
    "non_ccass_shares",
    "non_ccass_pct_of_issued",
    "snapshot_fetched_at",
    "source_cached",
    "settlement_note",
    "source_id",
    "source_name",
    "source_identifier",
    "snapshot_partial",
    "data_quality_warnings",
    "parser_version",
    "schema_version",
)


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    watchlist: tuple[str, ...] = DEFAULT_WATCHLIST
    sqlite_path: Path = Path("data/ccass_snapshots.db")
    csv_output_path: Path = Path("data/ccass_snapshot.csv")
    collection_limit: int = DEFAULT_COLLECTION_LIMIT
    source_mode: Literal["auto", "webbsite", "google_drive_csv"] = "auto"
    data_date: Literal["latest"] = "latest"
    dry_run: bool = False
    # Compatibility for callers that constructed the pre-P1-02 dataclass directly.
    holdings_limit: int | None = None

    @property
    def effective_collection_limit(self) -> int:
        value = self.holdings_limit if self.holdings_limit is not None else self.collection_limit
        if value < 1:
            raise ValueError("collection limit must be positive")
        return value


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
            snapshot.stock.code: snapshot.to_response() for snapshot in self.repository.latest_all()
        }
        for response in self.repository.legacy_latest_responses():
            by_code.setdefault(response.metadata.code, response)
        return [by_code[code] for code in sorted(by_code)]

    def previous_for(self, code: str, current: CcassResponse) -> CcassResponse | None:
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
    """Run one source-neutral, low-frequency collection pass."""
    codes = _normalize_codes(config.watchlist)
    source_settings = settings or Settings(data_source=config.source_mode)
    store = None if config.dry_run else SnapshotStore(config.sqlite_path)
    repository = store.repository if store else None
    if fetcher is None:
        service = (
            CcassService(settings=source_settings, lkg_repository=repository)
            if repository is not None
            else CcassService(settings=source_settings)
        )
    else:
        service = None

    async def default_fetcher(code: str, limit: int) -> CcassResponse:
        if service is None:  # pragma: no cover - guarded by selected_fetcher
            raise RuntimeError("collector service was not initialized")
        return await service.get_stock_data(code, holdings_limit=limit)

    selected_fetcher = fetcher or default_fetcher
    run_id = None
    if repository is not None:
        run_id = repository.create_collector_run(
            CollectorRunRecord(
                started_at=datetime.now(UTC),
                status="RUNNING",
                source_id=source_settings.data_source,
                requested_codes=codes,
                safe_details={"date": config.data_date, "dry_run": False},
            )
        )

    collected: list[CcassResponse] = []
    failures: dict[str, str] = {}
    success_count = 0
    partial_count = 0
    error_count = 0
    for code in codes:
        try:
            response = await selected_fetcher(code, config.effective_collection_limit)
            snapshot = _validated_snapshot(
                response,
                requested_code=code,
                settings=source_settings,
            )
        except PlatformError as exc:
            error_count += 1
            failures[code] = f"{exc.code}: {exc.message}"
            logger.warning("Collector fetch failed code=%s error_type=%s", code, exc.code)
            if repository is not None and run_id is not None:
                _persist_failure(
                    repository,
                    run_id=run_id,
                    code=code,
                    source_id=source_settings.data_source,
                    error=exc,
                )
            continue
        except ValueError:
            error = PlatformError(
                ErrorCode.PARSE_ERROR,
                f"Collector validation failed for stock code {code}.",
                status_code=502,
            )
            error_count += 1
            failures[code] = f"{error.code}: {error.message}"
            logger.warning("Collector validation failed code=%s error_type=%s", code, error.code)
            if repository is not None and run_id is not None:
                _persist_failure(
                    repository,
                    run_id=run_id,
                    code=code,
                    source_id=source_settings.data_source,
                    error=error,
                )
            continue

        current_freshness = freshness_status(response)
        if current_freshness == FreshnessStatus.STALE_LKG:
            partial_count += 1
            if repository is not None and run_id is not None:
                source_error_code = (
                    freshness_detail(response, SOURCE_ERROR_CODE_PREFIX)
                    or ErrorCode.SOURCE_UNAVAILABLE.value
                )
                source_error_message = (
                    freshness_detail(response, SOURCE_ERROR_MESSAGE_PREFIX)
                    or "Latest Holdings source failed; persistent LKG was served."
                )
                source_retry_recommended = (
                    freshness_detail(
                        response,
                        SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX,
                    )
                    == "true"
                )
                source_retry_after = freshness_detail(
                    response,
                    SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX,
                )
                snapshot_id = repository.snapshot_id_on(
                    code,
                    snapshot.snapshot_date,
                    source_id=snapshot.source.source_id,
                )
                repository.record_collector_result(
                    CollectorRunItemRecord(
                        run_id=run_id,
                        stock_code=code,
                        status="PARTIAL",
                        source_id=snapshot.source.source_id,
                        snapshot_id=snapshot_id,
                        snapshot_date=snapshot.snapshot_date,
                        safe_details={
                            "freshness": current_freshness.value,
                            "lkg_age_seconds": freshness_detail(
                                response,
                                LKG_AGE_SECONDS_PREFIX,
                            ),
                            "source_error_code": source_error_code,
                        },
                    )
                )
                repository.record_source_error(
                    SourceErrorRecord(
                        run_id=run_id,
                        source_id=snapshot.source.source_id,
                        stock_code=code,
                        error_code=source_error_code,
                        safe_message=source_error_message,
                        retry_recommended=source_retry_recommended,
                        retry_after_seconds=(
                            int(source_retry_after)
                            if source_retry_after and source_retry_after != "none"
                            else None
                        ),
                        safe_details={"served_lkg": True},
                    )
                )
            collected.append(response)
            continue

        if snapshot.partial:
            _append_partial_warning(response)
            snapshot = HistoricalSnapshot.from_response(response)
            partial_count += 1
            result_status: Literal["SUCCESS", "PARTIAL"] = "PARTIAL"
        else:
            success_count += 1
            result_status = "SUCCESS"

        if repository is not None and run_id is not None:
            snapshot_id = repository.save(snapshot)
            repository.record_collector_result(
                CollectorRunItemRecord(
                    run_id=run_id,
                    stock_code=code,
                    status=result_status,
                    source_id=snapshot.source.source_id,
                    snapshot_id=snapshot_id,
                    snapshot_date=snapshot.snapshot_date,
                    partial=snapshot.partial,
                    safe_details={
                        "rows": len(snapshot.holdings),
                        "participant_count": snapshot.participant_count,
                    },
                )
            )
        collected.append(response)

    exported = False
    if store is not None and store.latest_all():
        try:
            export_latest_csv(store, config.csv_output_path, responses=collected)
            exported = True
        except Exception as exc:
            if repository is not None and run_id is not None:
                repository.complete_collector_run(
                    run_id,
                    completed_at=datetime.now(UTC),
                    status="ERROR",
                    success_count=success_count,
                    partial_count=partial_count,
                    error_count=error_count + 1,
                    safe_details={
                        "date": config.data_date,
                        "export_error": type(exc).__name__,
                    },
                )
            raise

    if repository is not None and run_id is not None:
        repository.complete_collector_run(
            run_id,
            completed_at=datetime.now(UTC),
            status=_batch_status(success_count, partial_count, error_count),
            success_count=success_count,
            partial_count=partial_count,
            error_count=error_count,
            safe_details={"date": config.data_date, "exported": exported},
        )
    return collected, failures


def export_latest_csv(
    store: SnapshotStore,
    output_path: Path,
    *,
    responses: Sequence[CcassResponse] = (),
) -> None:
    """Atomically export each stock's latest snapshot using a compatible CSV schema."""
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
            latest = {response.metadata.code: response for response in store.latest_all()}
            latest.update({response.metadata.code: response for response in responses})
            for response in (latest[code] for code in sorted(latest)):
                partial = _response_is_partial(response)
                for row in response.holdings:
                    writer.writerow(
                        _csv_row(
                            response,
                            row.model_dump(mode="python"),
                            partial=partial,
                        )
                    )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def _csv_row(response: CcassResponse, holding: dict, *, partial: bool) -> dict[str, object]:
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
        "participant_count": summary.participant_count,
        "total_in_ccass_pct_of_issued": _csv_optional(summary.total_in_ccass_pct_of_issued),
        "issued_shares": _csv_optional(summary.issued_shares),
        "non_ccass_shares": _csv_optional(summary.non_ccass_shares),
        "non_ccass_pct_of_issued": _csv_optional(summary.non_ccass_pct_of_issued),
        "snapshot_fetched_at": metadata.fetched_at.isoformat(),
        "source_cached": str(metadata.cached).lower(),
        "settlement_note": metadata.settlement_note,
        "source_id": _source_id(metadata.source_name),
        "source_name": metadata.source_name,
        "source_identifier": _safe_identifier(metadata.source_url),
        "snapshot_partial": str(partial).lower(),
        "data_quality_warnings": json.dumps(
            response.data_quality_warnings,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "parser_version": "ccass-response-v1",
        "schema_version": 1,
    }


def _validated_snapshot(
    response: CcassResponse,
    *,
    requested_code: str,
    settings: Settings | None = None,
) -> HistoricalSnapshot:
    if response.metadata.code != requested_code:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            f"Collector requested {requested_code} but the source returned another stock code.",
            status_code=502,
        )
    source_id = None
    parser_version = "ccass-response-v1"
    if settings is not None:
        for diagnostic in build_source_registry(settings).diagnostics():
            if diagnostic["display_name"] == response.metadata.source_name:
                source_id = str(diagnostic["source_id"])
                parser_version = str(diagnostic["parser_version"])
                break
    return HistoricalSnapshot.from_response(
        response,
        source_id=source_id,
        parser_version=parser_version,
    )


def _persist_failure(
    repository: NormalizedSnapshotRepository,
    *,
    run_id: int,
    code: str,
    source_id: str,
    error: PlatformError,
) -> None:
    repository.record_collector_failure(
        CollectorRunItemRecord(
            run_id=run_id,
            stock_code=code,
            status="ERROR",
            source_id=source_id,
            safe_details={"error_code": str(error.code)},
        ),
        SourceErrorRecord(
            run_id=run_id,
            source_id=source_id,
            stock_code=code,
            error_code=str(error.code),
            safe_message=error.message,
            retry_recommended=error.retry_recommended,
            retry_after_seconds=error.retry_after_seconds,
        ),
    )


def _append_partial_warning(response: CcassResponse) -> None:
    if not any("partial" in warning.lower() for warning in response.data_quality_warnings):
        response.data_quality_warnings.append(
            "PARTIAL_DATA: participant rows are truncated or incomplete; missing rows remain absent."
        )


def _response_is_partial(response: CcassResponse) -> bool:
    return len(response.holdings) != response.holdings_summary.participant_count


def _batch_status(success_count: int, partial_count: int, error_count: int) -> str:
    if error_count and not (success_count or partial_count):
        return "ERROR"
    if error_count or partial_count:
        return "PARTIAL"
    return "SUCCESS"


def _source_id(source_name: str) -> str:
    lowered = source_name.strip().lower()
    if lowered == "google drive csv":
        return "google_drive_csv"
    if "webb-site" in lowered or "webbsite" in lowered:
        return "webbsite_mirror"
    normalized = re.sub(r"[^a-z0-9_-]+", "_", lowered).strip("_")
    return normalized[:64] or "unknown_source"


def _safe_identifier(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))
    return value.split("?", 1)[0][:512]


def _csv_optional(value: object | None) -> object:
    return "" if value is None else value


def _normalize_codes(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(normalize_stock_code(item) for item in values))


def parse_watchlist(value: str) -> tuple[str, ...]:
    text = value
    candidate = Path(value)
    try:
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8-sig")
    except OSError:
        text = value
    values = [
        item.strip()
        for item in re.split(r"[,\r\n]+", text)
        if item.strip() and not item.strip().startswith("#")
    ]
    return _normalize_codes(values) if values else DEFAULT_WATCHLIST


def _positive_collection_limit(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("collection limit must be positive")
    return parsed


def collector_config_from_args(argv: Sequence[str] | None = None) -> CollectorConfig:
    defaults = Settings()
    parser = argparse.ArgumentParser(description="Low-frequency CCASS snapshot collector")
    stock_group = parser.add_mutually_exclusive_group()
    stock_group.add_argument(
        "--stocks",
        help="Comma-separated HK stock codes",
    )
    stock_group.add_argument(
        "--watchlist",
        default=os.getenv("CCASS_WATCHLIST", ",".join(DEFAULT_WATCHLIST)),
        help="Comma-separated codes or a UTF-8 watchlist file; default: 01592",
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
    parser.add_argument(
        "--source",
        choices=("auto", "webbsite", "google_drive_csv"),
        default=defaults.data_source,
    )
    parser.add_argument("--date", choices=("latest",), default="latest")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--limit",
        type=_positive_collection_limit,
        default=DEFAULT_COLLECTION_LIMIT,
        help="Collector row safety cap; truncated responses are marked partial",
    )
    args = parser.parse_args(argv)
    stock_input = args.stocks if args.stocks is not None else args.watchlist
    return CollectorConfig(
        watchlist=parse_watchlist(stock_input),
        sqlite_path=Path(args.sqlite),
        csv_output_path=Path(args.output),
        collection_limit=args.limit,
        source_mode=args.source,
        data_date=args.date,
        dry_run=args.dry_run,
    )


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    config = collector_config_from_args(argv)
    settings = Settings(data_source=config.source_mode)
    collected, failures = asyncio.run(collect_watchlist(config, settings=settings))
    partial_count = sum(_response_is_partial(response) for response in collected)
    logger.info(
        "Collector completed collected=%s partial=%s failed=%s dry_run=%s",
        len(collected),
        partial_count,
        len(failures),
        config.dry_run,
    )
    return _collector_exit_code(collected, failures)


def _collector_exit_code(collected: Sequence[CcassResponse], failures: dict[str, str]) -> int:
    if failures:
        return 1
    if any(
        _response_is_partial(response)
        or freshness_status(response) == FreshnessStatus.STALE_LKG
        for response in collected
    ):
        return 2
    return 0


def configure_logging() -> None:
    """Keep collector status visible without logging third-party request URLs or parameters."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


if __name__ == "__main__":
    raise SystemExit(main())
