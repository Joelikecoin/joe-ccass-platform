"""Product service for exact, complete CCASS snapshot changes."""

from collections.abc import Sequence
from datetime import date
from functools import lru_cache

from app.config import Settings, get_settings
from app.domain.history import HistoricalSnapshot
from app.errors import ErrorCode, PlatformError
from app.models import (
    ChangeRow,
    ChangesDiagnostics,
    ChangesMetadata,
    ChangesResponse,
    ChangesSourceMetadata,
    ChangesSummary,
)
from app.services.latest_holdings import (
    finalize_latest_holdings,
    latest_holdings_is_complete,
)
from app.sources.registry import SourceDefinition, build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.normalize import normalize_stock_code

CHANGES_VALIDATION_WARNING = "CHANGES_VALIDATION: COMPLETE"
CHANGES_COMPLETENESS_WARNING = "SNAPSHOT_COMPLETENESS: compare=COMPLETE snapshot=COMPLETE"
CHANGES_PERCENTAGE_BASIS_WARNING = (
    "PERCENTAGE_BASIS: percent_before and percent_after use each snapshot's "
    "verified issued_shares denominator; percent_change is percentage-point change."
)


class ChangesService:
    """Compare two exact persisted snapshots from one approved active source."""

    def __init__(
        self,
        repository: NormalizedSnapshotRepository,
        sources: Sequence[SourceDefinition],
    ) -> None:
        self.repository = repository
        self.sources = tuple(sources)
        if not self.sources:
            raise ValueError("ChangesService requires at least one approved active source")

    def get_changes(
        self,
        code: str | int,
        *,
        snapshot_date: date,
        compare_date: date,
    ) -> ChangesResponse:
        normalized = normalize_stock_code(code)
        if compare_date >= snapshot_date:
            raise PlatformError(
                ErrorCode.INVALID_SCHEMA,
                "compare_date must be earlier than snapshot_date.",
                status_code=400,
            )

        for source in self.sources:
            snapshot = self.repository.snapshot_on(
                normalized,
                snapshot_date,
                source_id=source.source_id,
            )
            compare = self.repository.snapshot_on(
                normalized,
                compare_date,
                source_id=source.source_id,
            )
            if snapshot is not None and compare is not None:
                return _build_changes(
                    snapshot,
                    compare,
                    requested_code=normalized,
                    requested_snapshot_date=snapshot_date,
                    requested_compare_date=compare_date,
                    source=source,
                )

        raise PlatformError(
            ErrorCode.NOT_FOUND,
            "No approved active source has both requested exact CCASS snapshots.",
            status_code=404,
        )


def _build_changes(
    snapshot: HistoricalSnapshot,
    compare: HistoricalSnapshot,
    *,
    requested_code: str,
    requested_snapshot_date: date,
    requested_compare_date: date,
    source: SourceDefinition,
) -> ChangesResponse:
    _validate_snapshot(
        snapshot,
        requested_code=requested_code,
        requested_date=requested_snapshot_date,
        source=source,
        label="snapshot",
    )
    _validate_snapshot(
        compare,
        requested_code=requested_code,
        requested_date=requested_compare_date,
        source=source,
        label="compare",
    )
    if snapshot.source.issue_id != compare.source.issue_id:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            "Changes identity validation failed: snapshot issue IDs do not match.",
            status_code=502,
        )

    after_by_id = {row.participant_id: row for row in snapshot.holdings}
    before_by_id = {row.participant_id: row for row in compare.holdings}
    rows = [
        _change_row(after_by_id.get(participant_id), before_by_id.get(participant_id))
        for participant_id in sorted(set(after_by_id) | set(before_by_id))
    ]
    rows.sort(key=lambda row: (-abs(row.shares_change), row.participant_id))

    warnings = [
        CHANGES_VALIDATION_WARNING,
        CHANGES_COMPLETENESS_WARNING,
        CHANGES_PERCENTAGE_BASIS_WARNING,
    ]
    warnings.extend(f"COMPARE_SNAPSHOT_WARNING: {warning}" for warning in compare.warnings)
    warnings.extend(f"SNAPSHOT_WARNING: {warning}" for warning in snapshot.warnings)
    if snapshot.issued_shares != compare.issued_shares:
        warnings.append(
            "DENOMINATOR_CHANGED: issued_shares differs between the requested snapshots; "
            "source values are preserved without event attribution."
        )
    changed_names = sorted(
        participant_id
        for participant_id in set(after_by_id) & set(before_by_id)
        if after_by_id[participant_id].participant_name
        != before_by_id[participant_id].participant_name
    )
    warnings.extend(
        f"PARTICIPANT_NAME_CHANGED: {participant_id} has different source names across snapshots."
        for participant_id in changed_names
    )

    return ChangesResponse(
        metadata=ChangesMetadata(
            code=requested_code,
            name=snapshot.stock.name,
            issue_id=snapshot.source.issue_id,
            compare_date=compare.snapshot_date,
            snapshot_date=snapshot.snapshot_date,
            compare_source=_source_metadata(compare),
            snapshot_source=_source_metadata(snapshot),
            settlement_note=snapshot.settlement_note,
        ),
        summary=_summary(rows),
        changes=rows,
        diagnostics=ChangesDiagnostics(),
        data_quality_warnings=list(dict.fromkeys(warnings)),
    )


def _validate_snapshot(
    snapshot: HistoricalSnapshot,
    *,
    requested_code: str,
    requested_date: date,
    source: SourceDefinition,
    label: str,
) -> None:
    if snapshot.stock.code != requested_code or snapshot.snapshot_date != requested_date:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            f"Changes {label} identity or exact-date validation failed.",
            status_code=502,
        )
    if snapshot.source.source_id != source.source_id:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            f"Changes {label} source identity validation failed.",
            status_code=502,
        )
    if snapshot.stale:
        raise PlatformError(
            ErrorCode.DATA_STALE,
            f"Changes {label} is stale and cannot be used as product data.",
            status_code=409,
        )
    if snapshot.partial:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            f"Changes {label} is partial; missing participants cannot be treated as zero.",
            status_code=422,
        )

    response = finalize_latest_holdings(
        snapshot.to_response(),
        requested_code=requested_code,
    )
    if not latest_holdings_is_complete(response):
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            f"Changes {label} failed complete-snapshot product validation.",
            status_code=422,
        )


def _change_row(after, before) -> ChangeRow:
    shares_before = before.shares if before is not None else 0
    shares_after = after.shares if after is not None else 0
    percent_before = before.pct_of_issued if before is not None else 0.0
    percent_after = after.pct_of_issued if after is not None else 0.0
    shares_change = shares_after - shares_before
    new_participant = before is None
    removed_participant = after is None
    if new_participant:
        status = "new"
        participant = after.participant_name
    elif removed_participant:
        status = "removed"
        participant = before.participant_name
    elif shares_change > 0:
        status = "increased"
        participant = after.participant_name
    elif shares_change < 0:
        status = "decreased"
        participant = after.participant_name
    else:
        status = "unchanged"
        participant = after.participant_name
    relative_change = round(shares_change / shares_before * 100, 6) if shares_before else None
    return ChangeRow(
        participant_id=(after or before).participant_id,
        participant=participant,
        shares_before=shares_before,
        shares_after=shares_after,
        shares_change=shares_change,
        percent_before=percent_before,
        percent_after=percent_after,
        percent_change=round(percent_after - percent_before, 6),
        relative_change_percent=relative_change,
        new_participant=new_participant,
        removed_participant=removed_participant,
        status=status,
    )


def _summary(rows: list[ChangeRow]) -> ChangesSummary:
    return ChangesSummary(
        participant_count=len(rows),
        changed_count=sum(row.status != "unchanged" for row in rows),
        new_count=sum(row.new_participant for row in rows),
        removed_count=sum(row.removed_participant for row in rows),
        increased_count=sum(row.status == "increased" for row in rows),
        decreased_count=sum(row.status == "decreased" for row in rows),
        unchanged_count=sum(row.status == "unchanged" for row in rows),
    )


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
def get_changes_service() -> ChangesService:
    settings: Settings = get_settings()
    registry = build_source_registry(settings)
    return ChangesService(
        NormalizedSnapshotRepository(settings.ccass_sqlite_path),
        registry.select_holdings(settings.data_source),
    )
