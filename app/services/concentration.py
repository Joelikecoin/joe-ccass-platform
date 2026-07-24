"""Concentration product derived from one exact, complete CCASS snapshot."""

from collections.abc import Sequence
from datetime import date
from functools import lru_cache

from app.config import Settings, get_settings
from app.domain.history import HistoricalSnapshot
from app.errors import ErrorCode, PlatformError
from app.models import (
    ChangesSourceMetadata,
    ConcentrationDiagnostics,
    ConcentrationMetadata,
    ConcentrationResponse,
    ConcentrationSummary,
    HoldingRow,
)
from app.services.latest_holdings import (
    finalize_latest_holdings,
    latest_holdings_is_complete,
)
from app.sources.registry import SourceDefinition, build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.normalize import normalize_stock_code

CONCENTRATION_VALIDATION_WARNING = "CONCENTRATION_VALIDATION: COMPLETE"
CONCENTRATION_PERCENTAGE_BASIS_WARNING = (
    "CONCENTRATION_BASIS: issued percentages use verified issued_shares; "
    "CCASS percentages use total_in_ccass_shares."
)


class ConcentrationService:
    """Calculate objective concentration measures from one persisted snapshot."""

    def __init__(
        self,
        repository: NormalizedSnapshotRepository,
        sources: Sequence[SourceDefinition],
    ) -> None:
        self.repository = repository
        self.sources = tuple(sources)
        if not self.sources:
            raise ValueError("ConcentrationService requires at least one approved active source")

    def get_concentration(
        self,
        code: str | int,
        *,
        snapshot_date: date,
        top_holders_limit: int = 10,
    ) -> ConcentrationResponse:
        if top_holders_limit < 1:
            raise PlatformError(
                ErrorCode.INVALID_SCHEMA,
                "Concentration top_holders_limit must be positive.",
                status_code=400,
            )
        normalized = normalize_stock_code(code)
        for source in self.sources:
            snapshot = self.repository.snapshot_on(
                normalized,
                snapshot_date,
                source_id=source.source_id,
            )
            if snapshot is not None:
                return _build_concentration(
                    snapshot,
                    requested_code=normalized,
                    requested_date=snapshot_date,
                    source=source,
                    top_holders_limit=top_holders_limit,
                )
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            "No approved active source has the requested exact CCASS snapshot.",
            status_code=404,
        )


def _build_concentration(
    snapshot: HistoricalSnapshot,
    *,
    requested_code: str,
    requested_date: date,
    source: SourceDefinition,
    top_holders_limit: int,
) -> ConcentrationResponse:
    response = _validate_snapshot(
        snapshot,
        requested_code=requested_code,
        requested_date=requested_date,
        source=source,
    )
    rows = response.holdings
    issued_shares = response.holdings_summary.issued_shares
    ccass_shares = response.holdings_summary.total_in_ccass_shares
    assert issued_shares is not None and ccass_shares is not None
    top1 = rows[:1]
    top5 = rows[:5]
    top10 = rows[:10]
    warnings = list(response.data_quality_warnings)
    warnings.extend(
        (
            CONCENTRATION_VALIDATION_WARNING,
            CONCENTRATION_PERCENTAGE_BASIS_WARNING,
            "CONCENTRATION_INTERPRETATION: objective snapshot concentration only; "
            "no market meaning or cause is inferred.",
        )
    )
    return ConcentrationResponse(
        metadata=ConcentrationMetadata(
            code=requested_code,
            name=snapshot.stock.name,
            issue_id=snapshot.source.issue_id,
            snapshot_date=snapshot.snapshot_date,
            snapshot_source=_source_metadata(snapshot),
            settlement_note=snapshot.settlement_note,
        ),
        summary=ConcentrationSummary(
            participant_count=len(rows),
            total_tracked_shares=sum(row.shares for row in rows),
            total_tracked_pct_of_issued=_percentage(rows, issued_shares),
            total_tracked_pct_of_ccass=_percentage(rows, ccass_shares),
            top1_pct_of_issued=_percentage(top1, issued_shares),
            top1_pct_of_ccass=_percentage(top1, ccass_shares),
            top5_pct_of_issued=_percentage(top5, issued_shares),
            top5_pct_of_ccass=_percentage(top5, ccass_shares),
            top10_pct_of_issued=_percentage(top10, issued_shares),
            top10_pct_of_ccass=_percentage(top10, ccass_shares),
        ),
        participant_ranking=rows,
        top_holders=rows[:top_holders_limit],
        diagnostics=ConcentrationDiagnostics(),
        data_quality_warnings=list(dict.fromkeys(warnings)),
    )


def _validate_snapshot(
    snapshot: HistoricalSnapshot,
    *,
    requested_code: str,
    requested_date: date,
    source: SourceDefinition,
):
    if snapshot.stock.code != requested_code or snapshot.snapshot_date != requested_date:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            "Concentration snapshot identity or exact-date validation failed.",
            status_code=502,
        )
    if snapshot.source.source_id != source.source_id:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            "Concentration snapshot source identity validation failed.",
            status_code=502,
        )
    if snapshot.stale:
        raise PlatformError(
            ErrorCode.DATA_STALE,
            "Concentration snapshot is stale and cannot be used as product data.",
            status_code=409,
        )
    if snapshot.partial:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            "Concentration snapshot is partial; missing participants cannot be ranked.",
            status_code=422,
        )
    response = finalize_latest_holdings(
        snapshot.to_response(),
        requested_code=requested_code,
    )
    if not latest_holdings_is_complete(response):
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            "Concentration snapshot failed complete-snapshot product validation.",
            status_code=422,
        )
    return response


def _percentage(rows: Sequence[HoldingRow], denominator: int) -> float:
    return round(sum(row.shares for row in rows) / denominator * 100, 6)


def _source_metadata(snapshot: HistoricalSnapshot) -> ChangesSourceMetadata:
    return ChangesSourceMetadata(
        source_id=snapshot.source.source_id,
        source_name=snapshot.source.display_name,
        safe_identifier=snapshot.source.safe_identifier,
        issue_id=snapshot.source.issue_id,
        fetched_at=snapshot.fetched_at,
        parser_version=snapshot.parser_version,
        schema_version=snapshot.schema_version,
        checksum_sha256=snapshot.provenance.checksum_sha256,
        attribution=snapshot.attribution,
        issued_shares=snapshot.issued_shares,
        issued_shares_as_of=snapshot.issued_shares_as_of,
        cached=snapshot.cached,
        stale=snapshot.stale,
        partial=snapshot.partial,
    )


@lru_cache
def get_concentration_service() -> ConcentrationService:
    settings: Settings = get_settings()
    registry = build_source_registry(settings)
    return ConcentrationService(
        NormalizedSnapshotRepository(settings.ccass_sqlite_path),
        registry.select_holdings(settings.data_source),
    )