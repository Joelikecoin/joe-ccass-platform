"""Latest Holdings product validation and additive public-field enrichment."""

from collections.abc import Sequence
from datetime import UTC

from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse

PRODUCT_VALIDATION_PREFIX = "PRODUCT_VALIDATION:"
SNAPSHOT_COMPLETENESS_PREFIX = "SNAPSHOT_COMPLETENESS:"
PERCENTAGE_BASIS_WARNING = (
    "PERCENTAGE_BASIS: pct_of_issued uses issued_shares; "
    "pct_of_ccass uses total_in_ccass_shares."
)


def finalize_latest_holdings(
    response: CcassResponse,
    *,
    requested_code: str,
    holdings_limit: int | None = None,
) -> CcassResponse:
    """Validate a full latest snapshot, enrich public fields, then optionally slice rows."""
    if holdings_limit is not None and holdings_limit < 1:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            "holdings_limit must be at least 1.",
            status_code=400,
        )

    metadata = response.metadata
    summary = response.holdings_summary
    if metadata.code != requested_code:
        raise _invalid("source returned another stock identity")
    if metadata.holdings_date is None:
        raise _invalid("latest Holdings requires a verified holdings_date")
    if metadata.fetched_at.tzinfo is None or metadata.fetched_at.utcoffset() is None:
        raise _invalid("fetched_at must be timezone-aware")
    metadata.fetched_at.astimezone(UTC)
    if not response.holdings:
        raise _invalid("latest Holdings contains no participant rows")

    ranks = [row.rank for row in response.holdings]
    participant_ids = [row.participant_id for row in response.holdings]
    if len(ranks) != len(set(ranks)):
        raise _invalid("latest Holdings contains duplicate ranks")
    if len(participant_ids) != len(set(participant_ids)):
        raise _invalid("latest Holdings contains duplicate participant IDs")
    if ranks != list(range(1, len(ranks) + 1)):
        raise _invalid("latest Holdings ranks must be contiguous and ordered from 1")
    if summary.participant_count < len(response.holdings):
        raise _invalid("participant_count is smaller than the returned participant rows")
    if (
        summary.issued_shares_as_of is not None
        and summary.issued_shares_as_of > metadata.holdings_date
    ):
        raise _invalid("issued_shares_as_of is later than holdings_date")

    result = response.model_copy(deep=True)
    warnings = _without_product_diagnostics(result.data_quality_warnings)
    partial_reasons: list[str] = []

    if summary.participant_count != len(result.holdings):
        partial_reasons.append(
            "PARTIAL_DATA: participant_count does not match the available participant rows."
        )
    if summary.total_in_ccass_shares is None or summary.total_in_ccass_shares <= 0:
        partial_reasons.append(
            "DENOMINATOR_MISSING: total_in_ccass_shares is unavailable; "
            "pct_of_ccass cannot be calculated."
        )
    if summary.issued_shares is None or summary.issued_shares <= 0:
        partial_reasons.append(
            "DENOMINATOR_MISSING: issued_shares is unavailable."
        )
    if summary.issued_shares is not None and summary.issued_shares_as_of is None:
        partial_reasons.append(
            "ISSUED_SHARES_AS_OF_MISSING: issued-share denominator date is unverified."
        )
    if (
        summary.participant_count == len(result.holdings)
        and summary.total_in_ccass_shares is not None
        and sum(row.shares for row in result.holdings) != summary.total_in_ccass_shares
    ):
        partial_reasons.append(
            "SUMMARY_MISMATCH: complete participant rows do not sum to "
            "total_in_ccass_shares."
        )
    if (
        summary.issued_shares is not None
        and summary.total_in_ccass_shares is not None
        and summary.non_ccass_shares is not None
        and summary.total_in_ccass_shares + summary.non_ccass_shares
        != summary.issued_shares
    ):
        partial_reasons.append(
            "SUMMARY_MISMATCH: CCASS and non-CCASS shares do not sum to issued_shares."
        )
    if _percentage_invariants_mismatch(result):
        partial_reasons.append(
            "PERCENTAGE_MISMATCH: source percentages do not match the published "
            "share denominators or cumulative ranking."
        )
    if (
        summary.issued_shares_as_of is not None
        and summary.issued_shares_as_of < metadata.holdings_date
    ):
        partial_reasons.append(
            "CORPORATE_ACTION_RISK: issued_shares_as_of predates holdings_date; "
            "percentage denominators may not reflect the snapshot date."
        )
    if any(
        row.last_change is not None and row.last_change > metadata.holdings_date
        for row in result.holdings
    ):
        partial_reasons.append(
            "SOURCE_DATE_MISMATCH: a participant last_change date is later than holdings_date."
        )
    if _has_over_100_percentage(result):
        partial_reasons.append(
            "CORPORATE_ACTION_RISK: a source percentage exceeds 100%; "
            "source values are preserved and the denominator requires review."
        )

    total = summary.total_in_ccass_shares
    for row in result.holdings:
        row.pct_of_ccass = round(row.shares / total * 100, 6) if total else None

    warnings.extend(partial_reasons)
    complete = not partial_reasons
    warnings.extend(
        (
            PERCENTAGE_BASIS_WARNING,
            f"{SNAPSHOT_COMPLETENESS_PREFIX} {'COMPLETE' if complete else 'PARTIAL'}",
            f"{PRODUCT_VALIDATION_PREFIX} {'COMPLETE' if complete else 'PARTIAL'}",
        )
    )
    result.data_quality_warnings = list(dict.fromkeys(warnings))
    if holdings_limit is not None:
        result.holdings = result.holdings[:holdings_limit]
    return result


def latest_holdings_is_complete(response: CcassResponse) -> bool:
    statuses = [
        warning
        for warning in response.data_quality_warnings
        if warning.startswith(PRODUCT_VALIDATION_PREFIX)
    ]
    if statuses:
        return statuses[-1] == f"{PRODUCT_VALIDATION_PREFIX} COMPLETE"
    return (
        len(response.holdings) == response.holdings_summary.participant_count
        and not any("partial" in warning.lower() for warning in response.data_quality_warnings)
    )


def _invalid(reason: str) -> PlatformError:
    return PlatformError(
        ErrorCode.INVALID_SCHEMA,
        f"Latest Holdings product validation failed: {reason}.",
        status_code=502,
    )


def _has_over_100_percentage(response: CcassResponse) -> bool:
    summary = response.holdings_summary
    values = (
        summary.total_in_ccass_pct_of_issued,
        summary.non_ccass_pct_of_issued,
        summary.top5_pct_of_issued,
        summary.top10_pct_of_issued,
        summary.top5_pct_of_ccass,
        summary.top10_pct_of_ccass,
    )
    return any(value is not None and value > 100 for value in values) or any(
        row.pct_of_issued > 100
        or (
            row.cumulative_pct_of_issued is not None
            and row.cumulative_pct_of_issued > 100
        )
        for row in response.holdings
    )


def _percentage_invariants_mismatch(response: CcassResponse) -> bool:
    summary = response.holdings_summary
    issued = summary.issued_shares
    total = summary.total_in_ccass_shares
    tolerance = 0.02
    if issued:
        expected_total = total / issued * 100 if total is not None else None
        expected_non_ccass = (
            summary.non_ccass_shares / issued * 100
            if summary.non_ccass_shares is not None
            else None
        )
        if _different(summary.total_in_ccass_pct_of_issued, expected_total, tolerance):
            return True
        if _different(summary.non_ccass_pct_of_issued, expected_non_ccass, tolerance):
            return True
        if any(
            _different(row.pct_of_issued, row.shares / issued * 100, tolerance)
            for row in response.holdings
        ):
            return True

    cumulative = 0.0
    for row in response.holdings:
        cumulative += row.pct_of_issued
        if _different(row.cumulative_pct_of_issued, cumulative, tolerance):
            return True
    top5 = response.holdings[:5]
    top10 = response.holdings[:10]
    if _different(
        summary.top5_pct_of_issued,
        sum(row.pct_of_issued for row in top5),
        tolerance,
    ) or _different(
        summary.top10_pct_of_issued,
        sum(row.pct_of_issued for row in top10),
        tolerance,
    ):
        return True
    if total:
        if _different(
            summary.top5_pct_of_ccass,
            sum(row.shares for row in top5) / total * 100,
            tolerance,
        ) or _different(
            summary.top10_pct_of_ccass,
            sum(row.shares for row in top10) / total * 100,
            tolerance,
        ):
            return True
    return False


def _different(actual: float | None, expected: float | None, tolerance: float) -> bool:
    return actual is None or expected is None or abs(actual - expected) > tolerance


def _without_product_diagnostics(warnings: Sequence[str]) -> list[str]:
    prefixes = (
        PRODUCT_VALIDATION_PREFIX,
        SNAPSHOT_COMPLETENESS_PREFIX,
        "PERCENTAGE_BASIS:",
    )
    return [warning for warning in warnings if not warning.startswith(prefixes)]
