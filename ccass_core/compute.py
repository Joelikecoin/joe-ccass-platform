from dataclasses import dataclass, field

from app.models import CcassResponse, HoldingRow


@dataclass(frozen=True, slots=True)
class HoldingChange:
    participant_id: str
    participant: str
    previous_shares: int
    current_shares: int
    share_change: int
    previous_pct_of_issued: float
    current_pct_of_issued: float
    pct_point_change: float
    status: str


@dataclass(frozen=True, slots=True)
class TransferPattern:
    from_participant: str
    to_participant: str
    approximate_shares: int
    difference: int


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    changes: tuple[HoldingChange, ...] = ()
    big_changes: tuple[HoldingChange, ...] = ()
    transfer_patterns: tuple[TransferPattern, ...] = ()
    warnings: tuple[str, ...] = ()
    previous_available: bool = False
    big_change_threshold: int = 0
    concentration: dict[str, float | int | None] = field(default_factory=dict)


def compute_analysis(
    current: CcassResponse,
    previous: CcassResponse | None = None,
    *,
    big_change_threshold: int = 1_000_000,
    transfer_tolerance: float = 0.02,
) -> AnalysisResult:
    """Compute deterministic changes and concentration without inventing unavailable data."""
    threshold = max(0, int(big_change_threshold))
    warnings = list(current.data_quality_warnings)
    if current.metadata.cached:
        warnings.append("The current result came from a cached or snapshot data source.")
    if current.metadata.holdings_date is None:
        warnings.append("The holdings date is unavailable.")

    concentration = {
        "participant_count": current.holdings_summary.participant_count,
        "top5_pct_of_issued": current.holdings_summary.top5_pct_of_issued,
        "top10_pct_of_issued": current.holdings_summary.top10_pct_of_issued,
        "top5_pct_of_ccass": current.holdings_summary.top5_pct_of_ccass,
        "top10_pct_of_ccass": current.holdings_summary.top10_pct_of_ccass,
    }
    if previous is None:
        warnings.append("Change analysis is unavailable because no previous snapshot was supplied.")
        return AnalysisResult(
            warnings=tuple(_deduplicate(warnings)),
            big_change_threshold=threshold,
            concentration=concentration,
        )

    current_by_id = {row.participant_id: row for row in current.holdings}
    previous_by_id = {row.participant_id: row for row in previous.holdings}
    changes = tuple(
        _holding_change(current_by_id.get(participant_id), previous_by_id.get(participant_id))
        for participant_id in sorted(set(current_by_id) | set(previous_by_id))
    )
    ordered_changes = tuple(
        sorted(changes, key=lambda change: (-abs(change.share_change), change.participant_id))
    )
    big_changes = tuple(
        change
        for change in ordered_changes
        if change.share_change != 0 and abs(change.share_change) >= threshold
    )
    transfers = _detect_transfer_patterns(ordered_changes, tolerance=transfer_tolerance)
    return AnalysisResult(
        changes=ordered_changes,
        big_changes=big_changes,
        transfer_patterns=transfers,
        warnings=tuple(_deduplicate(warnings)),
        previous_available=True,
        big_change_threshold=threshold,
        concentration=concentration,
    )


def _holding_change(current: HoldingRow | None, previous: HoldingRow | None) -> HoldingChange:
    current_shares = current.shares if current else 0
    previous_shares = previous.shares if previous else 0
    current_pct = current.pct_of_issued if current else 0.0
    previous_pct = previous.pct_of_issued if previous else 0.0
    if previous is None:
        status = "new"
        participant_id = current.participant_id
        participant = current.participant
    elif current is None:
        status = "exited"
        participant_id = previous.participant_id
        participant = previous.participant
    else:
        participant_id = current.participant_id
        participant = current.participant
        delta = current_shares - previous_shares
        status = "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"
    return HoldingChange(
        participant_id=participant_id,
        participant=participant,
        previous_shares=previous_shares,
        current_shares=current_shares,
        share_change=current_shares - previous_shares,
        previous_pct_of_issued=previous_pct,
        current_pct_of_issued=current_pct,
        pct_point_change=round(current_pct - previous_pct, 6),
        status=status,
    )


def _detect_transfer_patterns(
    changes: tuple[HoldingChange, ...], *, tolerance: float
) -> tuple[TransferPattern, ...]:
    increases = [change for change in changes if change.share_change > 0]
    decreases = [change for change in changes if change.share_change < 0]
    patterns: list[TransferPattern] = []
    used_increases: set[str] = set()
    for decrease in decreases:
        amount = abs(decrease.share_change)
        candidates = [
            increase
            for increase in increases
            if increase.participant_id not in used_increases
            and abs(increase.share_change - amount) <= max(1, round(amount * tolerance))
        ]
        if not candidates:
            continue
        increase = min(candidates, key=lambda item: abs(item.share_change - amount))
        used_increases.add(increase.participant_id)
        patterns.append(
            TransferPattern(
                from_participant=decrease.participant,
                to_participant=increase.participant,
                approximate_shares=min(amount, increase.share_change),
                difference=abs(increase.share_change - amount),
            )
        )
    return tuple(patterns)


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
