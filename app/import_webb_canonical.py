"""One-shot, idempotent import of the prepared Webb historical index.

The source SQLite file is read-only input.  Writes go through the existing
NormalizedSnapshotRepository, which selects Turso when the production
credentials are present and local SQLite otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import UTC, date, datetime, time
from pathlib import Path

from app.domain.history import (
    HistoricalSnapshot,
    NormalizedHolding,
    RawProvenance,
    SourceIdentity,
    StockIdentity,
)
from app.storage.history import NormalizedSnapshotRepository


SOURCE_ID = "webbsite_archive"
SOURCE_NAME = "Webb-site repository archive"
COVERAGE_END = date(2025, 12, 24)
PARSER_VERSION = "webb-canonical-import-v1"


def _normalize_code(value: str) -> str:
    return str(value).strip().zfill(5)


def _load_snapshots(source_path: Path) -> list[HistoricalSnapshot]:
    grouped: dict[tuple[str, date, int], list[dict[str, object]]] = defaultdict(list)
    with sqlite3.connect(f"{source_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT stock_code, issue_id, snapshot_date, participant_id, "
            "participant_name, holding, issued_shares, source_record_date, "
            "provenance_metadata FROM historical_snapshot "
            "ORDER BY stock_code, snapshot_date, holding DESC, participant_id"
        ).fetchall()
    for row in rows:
        code = _normalize_code(row["stock_code"])
        snapshot_date = date.fromisoformat(str(row["snapshot_date"]))
        grouped[(code, snapshot_date, int(row["issue_id"]))].append(dict(row))

    snapshots: list[HistoricalSnapshot] = []
    for (code, snapshot_date, issue_id), rows in grouped.items():
        rows.sort(key=lambda item: (-int(float(item["holding"])), str(item["participant_id"])))
        issued = int(float(rows[0]["issued_shares"])) if rows[0]["issued_shares"] is not None else None
        source_record_date = (
            date.fromisoformat(str(rows[0]["source_record_date"]))
            if rows[0]["source_record_date"]
            else snapshot_date
        )
        fetched_at = datetime.combine(source_record_date, time.min, tzinfo=UTC)
        holdings = tuple(
            NormalizedHolding(
                participant_id=str(item["participant_id"]),
                participant_name=str(item["participant_name"]),
                rank=rank,
                shares=int(float(item["holding"])),
                pct_of_issued=(
                    round(int(float(item["holding"])) / issued * 100, 6)
                    if issued
                    else 0.0
                ),
            )
            for rank, item in enumerate(rows, start=1)
        )
        total = sum(row.shares for row in holdings)
        top5 = sum(row.shares for row in holdings[:5])
        top10 = sum(row.shares for row in holdings[:10])
        provenance_rows = [
            {
                "stock_code": code,
                "issue_id": issue_id,
                "snapshot_date": snapshot_date.isoformat(),
                "participant_id": row.participant_id,
                "holding": row.shares,
            }
            for row in holdings
        ]
        payload = json.dumps(provenance_rows, separators=(",", ":"), sort_keys=True).encode()
        snapshots.append(
            HistoricalSnapshot(
                stock=StockIdentity(code=code, market="HK"),
                source=SourceIdentity(
                    source_id=SOURCE_ID,
                    safe_identifier=f"webbsite-archive://{issue_id}/{snapshot_date.isoformat()}",
                    issue_id=issue_id,
                    display_name=SOURCE_NAME,
                ),
                snapshot_date=snapshot_date,
                fetched_at=fetched_at,
                warnings=(f"HISTORICAL_COVERAGE_END={COVERAGE_END.isoformat()}",),
                parser_version=PARSER_VERSION,
                issued_shares=issued,
                issued_shares_as_of=source_record_date,
                total_in_ccass_shares=total,
                total_in_ccass_pct_of_issued=(round(total / issued * 100, 6) if issued else None),
                non_ccass_shares=(max(issued - total, 0) if issued else None),
                non_ccass_pct_of_issued=(
                    round(max(issued - total, 0) / issued * 100, 6) if issued else None
                ),
                participant_count=len(holdings),
                top5_pct_of_issued=(round(top5 / issued * 100, 6) if issued else None),
                top10_pct_of_issued=(round(top10 / issued * 100, 6) if issued else None),
                top5_pct_of_ccass=(round(top5 / total * 100, 6) if total else None),
                top10_pct_of_ccass=(round(top10 / total * 100, 6) if total else None),
                settlement_note="Historical Webb-site archive snapshot; coverage ends 2025-12-24.",
                attribution=(
                    "David Webb original Webb-site repository archive; "
                    "coverage through 2025-12-24"
                ),
                holdings=holdings,
                provenance=RawProvenance(
                    source_id=SOURCE_ID,
                    safe_reference=f"webbsite-archive://{issue_id}/{snapshot_date.isoformat()}",
                    checksum_sha256=hashlib.sha256(payload).hexdigest(),
                    fetched_at=fetched_at,
                    content_type="application/vnd.joe-ccass.webb-canonical+json",
                    byte_size=len(payload),
                ),
            )
        )
    return snapshots


def import_canonical(source_path: Path, target_path: Path) -> tuple[int, int]:
    snapshots = _load_snapshots(source_path)
    repository = NormalizedSnapshotRepository(target_path)
    for snapshot in snapshots:
        repository.save(snapshot)
    return len(snapshots), sum(len(snapshot.holdings) for snapshot in snapshots)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import prepared Webb canonical snapshots")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, default=Path("data/ccass_snapshots.db"))
    args = parser.parse_args()
    snapshot_count, row_count = import_canonical(args.source, args.target)
    print(
        json.dumps(
            {
                "source": SOURCE_ID,
                "coverage_end": COVERAGE_END.isoformat(),
                "snapshot_count": snapshot_count,
                "row_count": row_count,
                "idempotent": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
