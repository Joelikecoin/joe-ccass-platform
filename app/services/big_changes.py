"""Big Changes product filtering built directly on P1-08 Changes."""

from datetime import date
from functools import lru_cache

from app.config import Settings, get_settings
from app.errors import ErrorCode, PlatformError
from app.models import BigChangesResponse, BigChangesSummary
from app.services.changes import ChangesService, get_changes_service

BIG_CHANGES_VALIDATION_WARNING = "BIG_CHANGES_VALIDATION: COMPLETE"


class BigChangesService:
    """Filter validated P1-08 Changes without recomputing participant comparisons."""

    def __init__(
        self,
        changes_service: ChangesService,
        *,
        default_threshold_shares: int,
    ) -> None:
        if default_threshold_shares < 1:
            raise ValueError("default Big Changes threshold must be positive")
        self.changes_service = changes_service
        self.default_threshold_shares = default_threshold_shares

    def get_big_changes(
        self,
        code: str | int,
        *,
        snapshot_date: date,
        compare_date: date,
        threshold_shares: int | None = None,
    ) -> BigChangesResponse:
        threshold = self.default_threshold_shares if threshold_shares is None else threshold_shares
        if threshold < 1:
            raise PlatformError(
                ErrorCode.INVALID_SCHEMA,
                "Big Changes threshold_shares must be positive.",
                status_code=400,
            )

        changes = self.changes_service.get_changes(
            code,
            snapshot_date=snapshot_date,
            compare_date=compare_date,
        )
        rows = [
            row
            for row in changes.changes
            if row.shares_change != 0 and abs(row.shares_change) >= threshold
        ]
        warnings = list(changes.data_quality_warnings)
        warnings.extend(
            (
                BIG_CHANGES_VALIDATION_WARNING,
                f"BIG_CHANGES_THRESHOLD: absolute shares_change >= {threshold} shares.",
            )
        )
        return BigChangesResponse(
            metadata=changes.metadata,
            summary=BigChangesSummary(
                threshold_shares=threshold,
                participants_compared=changes.summary.participant_count,
                changed_participants_considered=changes.summary.changed_count,
                big_changes_count=len(rows),
                new_count=sum(row.new_participant for row in rows),
                removed_count=sum(row.removed_participant for row in rows),
                increased_count=sum(row.status == "increased" for row in rows),
                decreased_count=sum(row.status == "decreased" for row in rows),
            ),
            big_changes=rows,
            diagnostics=changes.diagnostics,
            data_quality_warnings=list(dict.fromkeys(warnings)),
        )


@lru_cache
def get_big_changes_service() -> BigChangesService:
    settings: Settings = get_settings()
    return BigChangesService(
        get_changes_service(),
        default_threshold_shares=settings.big_changes_threshold_shares,
    )
