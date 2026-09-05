"""Longbridge CCASS detail normalization and persistence.

This module is intentionally isolated from the existing source router and UI.
It adapts the official broker_holding_detail response to Joe's canonical
snapshot repository.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Mapping

from app.domain.history import HistoricalSnapshot
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata
from app.storage.history import NormalizedSnapshotRepository
from app.storage.longbridge_store import LongbridgeSnapshotStore


def normalize_stock_code(code: str) -> str:
    digits = "".join(ch for ch in str(code).strip() if ch.isdigit())
    if not digits or len(digits) > 5:
        raise ValueError(f"invalid HK stock code: {code!r}")
    return digits.zfill(5)


def _value(item: Mapping[str, Any], key: str) -> Any:
    value = item.get(key)
    if isinstance(value, Mapping):
        return value.get("value")
    return value


def build_response(
    payload: Mapping[str, Any],
    *,
    stock_code: str,
    issue_id: int,
    fetched_at: datetime | None = None,
) -> CcassResponse:
    code = normalize_stock_code(stock_code)
    items = payload.get("list") or payload.get("items") or []
    if not isinstance(items, list) or not items:
        raise ValueError("Longbridge broker_holding_detail returned no rows")
    data_date = payload.get("updated_at") or payload.get("data_date") or payload.get("date")
    if not data_date:
        raise ValueError("Longbridge response omitted its authoritative data date")
    snapshot_date = date.fromisoformat(str(data_date).replace(".", "-"))
    fetched = fetched_at or datetime.now(UTC)
    total = sum(int(float(_value(row, "shares") or 0)) for row in items)
    if total <= 0:
        raise ValueError("Longbridge response has no positive total holdings")
    rows: list[HoldingRow] = []
    for rank, item in enumerate(items, start=1):
        participant_id = str(item.get("parti_number") or item.get("broker_id") or "").strip()
        name = str(item.get("name") or item.get("broker_name") or "").strip()
        if not participant_id or not name:
            raise ValueError(f"Longbridge row {rank} omitted participant identity")
        shares = int(float(_value(item, "shares") or 0))
        ratio = float(_value(item, "ratio") or 0.0) * 100.0
        rows.append(
            HoldingRow(
                rank=rank,
                participant_id=participant_id,
                participant=name,
                shares=shares,
                pct_of_issued=ratio,
                pct_of_ccass=round(shares / total * 100.0, 6),
            )
        )
    issued_ratio = sum(row.pct_of_issued for row in rows)
    return CcassResponse(
        metadata=SourceMetadata(
            code=code,
            issue_id=issue_id,
            holdings_date=snapshot_date,
            fetched_at=fetched,
            source_url=f"longbridge://broker_holding_detail/{code}",
            source_name="Longbridge",
            cached=False,
        ),
        holdings_summary=HoldingsSummary(
            total_in_ccass_shares=total,
            total_in_ccass_pct_of_issued=issued_ratio,
            participant_count=len(rows),
        ),
        holdings=rows,
    )


def persist_response(
    response: CcassResponse,
    *,
    db_path: Path,
    source_id: str = "longbridge",
) -> int:
    if __import__("os").getenv("DATABASE_URL"):
        return LongbridgeSnapshotStore(sqlite_path=db_path).upsert_response(response)
    repository = NormalizedSnapshotRepository(db_path)
    return repository.save_response(response, source_id=source_id)


def load_snapshot(*, db_path: Path, stock_code: str, snapshot_date: date) -> HistoricalSnapshot | None:
    repository = NormalizedSnapshotRepository(db_path)
    for snapshot in repository.date_range(
        normalize_stock_code(stock_code),
        date_from=snapshot_date,
        date_to=snapshot_date,
        source_id="longbridge",
    ):
        return snapshot
    return None
