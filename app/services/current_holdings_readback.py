"""Read participant rows from an exact persisted production snapshot."""

from __future__ import annotations

from datetime import date

from app.storage.history import NormalizedSnapshotRepository


def read_current_participant_holdings(
    repository: NormalizedSnapshotRepository, stock_code: str, holdings_date: date
) -> list[dict[str, object]]:
    """Return persisted rows only; source participant IDs remain source scoped."""
    snapshot = repository.snapshot_on(stock_code, holdings_date, source_id="longbridge")
    if snapshot is None:
        return []
    reference = snapshot.provenance.safe_reference
    return [
        {
            "canonical_security_id": f"security:{snapshot.stock.code}",
            "hk_stock_code": snapshot.stock.code,
            "holdings_date": snapshot.snapshot_date.isoformat(),
            "source_participant_id": holding.participant_id,
            "canonical_participant_id": None,
            "participant_name": holding.participant_name,
            "share_quantity": holding.shares,
            "source_reference": reference,
            "source_id": snapshot.source.source_id,
            "provenance_sha256": snapshot.provenance.checksum_sha256,
        }
        for holding in snapshot.holdings
    ]
