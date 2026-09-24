"""Deterministic point-in-time reconstruction for Webb CCASS holdings.

Imported columns: c1=partID, c2=issueID, c3=absolute holding, c4=atDate.
Webb writes a row only when an absolute participant holding changes.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from sqlite3 import Connection

WEBB_CHANGE_KEY = ("issue_id", "part_id", "change_date")


def _participant_sort_key(row: dict[str, object]) -> tuple[int, int | str, str]:
    part_id = str(row["source_part_id"])
    return (0, int(part_id), part_id) if part_id.isdigit() else (1, part_id, part_id)


def _ordered_changes(connection: Connection, issue_id: str, cutoff: str):
    query = """
        SELECT rowid, c1, c3, c4 FROM holdings
        WHERE c2 = ? AND c4 <= ?
        ORDER BY c4, CAST(c1 AS INTEGER), c1, rowid
    """
    for rowid, part_id, holding, change_date in connection.execute(
        query, (str(issue_id), cutoff)
    ):
        yield int(rowid), str(part_id), int(holding), str(change_date)


def resolve_issue_snapshot_date(
    connection: Connection, issue_id: str, requested_date: date
) -> date | None:
    """Resolve to Webb's latest dailylog date at or before the request."""
    row = connection.execute(
        "SELECT MAX(c1) FROM dailylog WHERE c2 = ? AND c1 <= ?",
        (str(issue_id), requested_date.isoformat()),
    ).fetchone()
    return date.fromisoformat(str(row[0])) if row and row[0] else None


def reconstruct_issue_at(
    connection: Connection, issue_id: str, as_of: date, *, resolve_source_date: bool = True
) -> dict[str, object]:
    """Carry each participant's latest source value forward through ``as_of``.

    The source stores changed holdings only. A zero value ends that participant's
    active position; absence of a change on a date does not mean zero.
    """
    effective = (
        resolve_issue_snapshot_date(connection, str(issue_id), as_of)
        if resolve_source_date else as_of
    )
    if effective is None:
        return {
            "issue_id": str(issue_id), "requested_date": as_of.isoformat(),
            "holdings_date": None, "position_semantics": "no source snapshot on or before date",
            "natural_change_key": WEBB_CHANGE_KEY, "source_changes_seen": 0,
            "participant_rows": [], "active_participant_count": 0,
            "active_share_total": 0, "zero_position_count": 0,
            "negative_value_count": 0, "duplicate_change_keys": 0,
            "conflicting_change_keys": 0,
        }
    cutoff = effective.isoformat()
    latest: dict[str, tuple[str, int, int]] = {}
    changes_seen = 0
    duplicate_keys = 0
    conflicts = 0
    negative_values = 0
    for rowid, part_id, holding, change_date in _ordered_changes(
        connection, str(issue_id), cutoff
    ):
        changes_seen += 1
        negative_values += holding < 0
        prior = latest.get(part_id)
        if prior is not None and change_date == prior[0]:
            duplicate_keys += 1
            if holding != prior[1]:
                conflicts += 1
            continue
        latest[part_id] = (change_date, holding, rowid)
    rows = [
        {"source_issue_id": issue_id, "source_part_id": part_id,
         "share_quantity": holding, "last_change_date": change_date,
         "holdings_date": cutoff, "source_rowid": rowid}
        for part_id, (change_date, holding, rowid) in latest.items()
        if holding > 0
    ]
    rows.sort(key=_participant_sort_key)
    return {
        "issue_id": str(issue_id),
        "requested_date": as_of.isoformat(),
        "holdings_date": cutoff,
        "position_semantics": "latest absolute holding at or before date",
        "natural_change_key": WEBB_CHANGE_KEY,
        "source_changes_seen": changes_seen,
        "participant_rows": rows,
        "active_participant_count": len(rows),
        "active_share_total": sum(int(row["share_quantity"]) for row in rows),
        "zero_position_count": sum(holding == 0 for _, holding, _ in latest.values()),
        "negative_value_count": negative_values,
        "duplicate_change_keys": duplicate_keys,
        "conflicting_change_keys": conflicts,
    }


def reconstruct_issue_dates(
    connection: Connection, issue_id: str, dates: Iterable[date], *,
    resolve_source_dates: bool = True,
) -> list[dict[str, object]]:
    """Reconstruct several dates in one ordered pass over an issue's changes."""
    requested = sorted(set(dates))
    if not requested:
        return []
    if resolve_source_dates:
        daily_dates = [
            date.fromisoformat(str(row[0])) for row in connection.execute(
                "SELECT c1 FROM dailylog WHERE c2 = ? AND c1 <= ? ORDER BY c1",
                (str(issue_id), requested[-1].isoformat()),
            )
        ]
        effective_dates: list[date | None] = []
        daily_cursor = 0
        latest_daily: date | None = None
        for requested_date in requested:
            while daily_cursor < len(daily_dates) and daily_dates[daily_cursor] <= requested_date:
                latest_daily = daily_dates[daily_cursor]
                daily_cursor += 1
            effective_dates.append(latest_daily)
    else:
        effective_dates = list(requested)
    valid_dates = [item for item in effective_dates if item is not None]
    changes = list(_ordered_changes(
        connection, str(issue_id), max(valid_dates).isoformat()
    )) if valid_dates else []
    state: dict[str, tuple[str, int, int]] = {}
    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys = conflicts = negative_values = cursor = 0
    output: list[dict[str, object]] = []
    for requested_date, effective_date in zip(requested, effective_dates, strict=True):
        if effective_date is None:
            output.append({
                "issue_id": str(issue_id), "requested_date": requested_date.isoformat(),
                "holdings_date": None, "position_semantics": "no source snapshot on or before date",
                "natural_change_key": WEBB_CHANGE_KEY, "source_changes_seen": 0,
                "participant_rows": [], "active_participant_count": 0,
                "active_share_total": 0, "zero_position_count": 0,
                "negative_value_count": 0, "duplicate_change_keys": 0,
                "conflicting_change_keys": 0,
            })
            continue
        cutoff = effective_date.isoformat()
        while cursor < len(changes) and changes[cursor][3] <= cutoff:
            rowid, part_id, holding, change_date = changes[cursor]
            cursor += 1
            key = (part_id, change_date)
            if key in seen_keys:
                duplicate_keys += 1
                prior = state.get(part_id)
                conflicts += bool(prior and prior[0] == change_date and prior[1] != holding)
                continue
            seen_keys.add(key)
            negative_values += holding < 0
            state[part_id] = (change_date, holding, rowid)
        rows = [
            {"source_issue_id": str(issue_id), "source_part_id": part_id,
             "share_quantity": holding, "last_change_date": change_date,
             "holdings_date": cutoff, "source_rowid": rowid}
            for part_id, (change_date, holding, rowid) in state.items() if holding > 0
        ]
        rows.sort(key=_participant_sort_key)
        output.append({
            "issue_id": str(issue_id), "requested_date": requested_date.isoformat(),
            "holdings_date": cutoff,
            "position_semantics": "latest absolute holding at or before date",
            "natural_change_key": WEBB_CHANGE_KEY, "source_changes_seen": cursor,
            "participant_rows": rows, "active_participant_count": len(rows),
            "active_share_total": sum(int(row["share_quantity"]) for row in rows),
            "zero_position_count": sum(value == 0 for _, value, _ in state.values()),
            "negative_value_count": negative_values,
            "duplicate_change_keys": duplicate_keys,
            "conflicting_change_keys": conflicts,
        })
    return output


def reference_issue_at(
    connection: Connection, issue_id: str, as_of: date, *, resolve_source_date: bool = True
) -> list[tuple[str, int, str]]:
    """Independent SQL equivalent of Webb's ``choldings.asp`` query."""
    effective = (
        resolve_issue_snapshot_date(connection, str(issue_id), as_of)
        if resolve_source_date else as_of
    )
    if effective is None:
        return []
    rows = connection.execute(
        """
        SELECT h.c1, CAST(h.c3 AS INTEGER), h.c4 FROM holdings h
        JOIN (
            SELECT c1 AS part_id, MAX(c4) AS max_date FROM holdings
            WHERE c2 = ? AND c4 <= ? GROUP BY c1
        ) latest ON h.c1 = latest.part_id AND h.c4 = latest.max_date
        WHERE h.c2 = ? AND CAST(h.c3 AS INTEGER) > 0
        ORDER BY CAST(h.c1 AS INTEGER), h.c1
        """, (str(issue_id), effective.isoformat(), str(issue_id))
    ).fetchall()
    return [(str(part_id), int(holding), str(change_date))
            for part_id, holding, change_date in rows]


def compare_with_reference_query(
    connection: Connection, issue_id: str, as_of: date
) -> dict[str, object]:
    rebuilt = reconstruct_issue_at(connection, issue_id, as_of)
    engine = [(str(row["source_part_id"]), int(row["share_quantity"]),
               str(row["last_change_date"])) for row in rebuilt["participant_rows"]]
    reference = reference_issue_at(connection, issue_id, as_of)
    return {
        "issue_id": str(issue_id), "holdings_date": as_of.isoformat(),
        "engine_rows": len(engine), "reference_rows": len(reference),
        "engine_share_total": sum(row[1] for row in engine),
        "reference_share_total": sum(row[1] for row in reference),
        "rows_match": engine == reference,
        "duplicate_change_keys": rebuilt["duplicate_change_keys"],
        "conflicting_change_keys": rebuilt["conflicting_change_keys"],
        "negative_value_count": rebuilt["negative_value_count"],
    }
