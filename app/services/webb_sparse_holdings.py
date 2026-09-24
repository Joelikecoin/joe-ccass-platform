"""Reconstruct an exact issue state from Webb's sparse holding changes."""

from __future__ import annotations

from datetime import date
from sqlite3 import Connection


def reconstruct_issue_at(connection: Connection, issue_id: str, as_of: date) -> dict[str, object]:
    """Carry each participant's latest source value forward through ``as_of``.

    The source stores changed holdings only. A zero value ends that participant's
    active position; absence of a change on a date does not mean zero.
    """
    cutoff = as_of.isoformat()
    latest: dict[str, tuple[str, int]] = {}
    changes_seen = 0
    duplicate_keys = 0
    conflicts = 0
    for part_id, holding_raw, change_date in connection.execute(
        "SELECT c1, c3, c4 FROM holdings WHERE c2 = ? AND c4 <= ?",
        (issue_id, cutoff),
    ):
        part_id = str(part_id)
        holding = int(holding_raw)
        change_date = str(change_date)
        changes_seen += 1
        prior = latest.get(part_id)
        if prior is None or change_date > prior[0]:
            latest[part_id] = (change_date, holding)
        elif change_date == prior[0]:
            duplicate_keys += 1
            if holding != prior[1]:
                conflicts += 1
    rows = [
        {"source_issue_id": issue_id, "source_part_id": part_id,
         "share_quantity": holding, "last_change_date": change_date,
         "holdings_date": cutoff}
        for part_id, (change_date, holding) in latest.items()
        if holding > 0
    ]
    rows.sort(key=lambda row: row["source_part_id"])
    return {
        "issue_id": issue_id,
        "holdings_date": cutoff,
        "source_changes_seen": changes_seen,
        "participant_rows": rows,
        "zero_position_count": sum(holding == 0 for _, holding in latest.values()),
        "duplicate_change_keys": duplicate_keys,
        "conflicting_change_keys": conflicts,
    }
