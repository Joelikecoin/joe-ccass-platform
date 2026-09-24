import sqlite3
from datetime import date

from app.services.webb_sparse_holdings import (
    compare_with_reference_query,
    reconstruct_issue_at,
    reconstruct_issue_dates,
    resolve_issue_snapshot_date,
)


def _schema(connection):
    connection.execute("CREATE TABLE holdings (c1 TEXT, c2 TEXT, c3 TEXT, c4 TEXT)")
    connection.execute("CREATE TABLE dailylog (c1 TEXT, c2 TEXT)")


def test_sparse_changes_carry_forward_and_zero_ends_position():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("P1", "1088", "100", "2013-03-01"),
        ("P2", "1088", "50", "2013-03-02"),
        ("P1", "1088", "0", "2013-03-03"),
        ("P3", "999", "500", "2013-03-03"),
    ])
    connection.execute("INSERT INTO dailylog VALUES (?,?)", ("2013-03-04", "1088"))
    result = reconstruct_issue_at(connection, "1088", date(2013, 3, 4))
    assert result["source_changes_seen"] == 3
    assert result["zero_position_count"] == 1
    assert result["participant_rows"] == [{
        "source_issue_id": "1088", "source_part_id": "P2",
        "share_quantity": 50, "last_change_date": "2013-03-02",
        "holdings_date": "2013-03-04", "source_rowid": 2,
    }]


def test_multi_date_reconstruction_uses_absolute_values_not_deltas():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("1", "7", "100", "2020-01-01"),
        ("1", "7", "125", "2020-01-03"),
        ("2", "7", "50", "2020-01-02"),
    ])
    connection.executemany("INSERT INTO dailylog VALUES (?,?)", [
        ("2020-01-02", "7"), ("2020-01-03", "7"),
    ])
    results = reconstruct_issue_dates(
        connection, "7", [date(2020, 1, 2), date(2020, 1, 3)]
    )
    assert [result["active_share_total"] for result in results] == [150, 175]
    assert [result["source_changes_seen"] for result in results] == [2, 3]
    assert all(result["conflicting_change_keys"] == 0 for result in results)


def test_engine_matches_independent_reference_query():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("1", "7", "100", "2020-01-01"),
        ("2", "7", "50", "2020-01-02"),
        ("1", "7", "0", "2020-01-03"),
    ])
    connection.executemany("INSERT INTO dailylog VALUES (?,?)", [
        ("2020-01-03", "7"), ("2020-01-06", "7"),
    ])
    comparison = compare_with_reference_query(connection, "7", date(2020, 1, 3))
    assert comparison["rows_match"] is True
    assert comparison["engine_rows"] == comparison["reference_rows"] == 1
    assert comparison["engine_share_total"] == comparison["reference_share_total"] == 50


def test_requested_non_trading_date_resolves_to_last_dailylog_date():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.execute("INSERT INTO holdings VALUES (?,?,?,?)", ("1", "7", "100", "2020-01-03"))
    connection.executemany(
        "INSERT INTO dailylog VALUES (?,?)",
        [("2020-01-03", "7"), ("2020-01-06", "7")],
    )
    assert resolve_issue_snapshot_date(connection, "7", date(2020, 1, 5)) == date(2020, 1, 3)
    result = reconstruct_issue_at(connection, "7", date(2020, 1, 5))
    assert result["requested_date"] == "2020-01-05"
    assert result["holdings_date"] == "2020-01-03"


def test_first_observation_zero_close_and_reentry_boundaries():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO dailylog VALUES (?,?)", [
        ("2020-01-01", "7"), ("2020-01-02", "7"), ("2020-01-03", "7"),
        ("2020-01-04", "7"), ("2020-01-05", "7"),
    ])
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("1", "7", "100", "2020-01-02"),
        ("1", "7", "0", "2020-01-04"),
        ("1", "7", "75", "2020-01-05"),
    ])
    results = reconstruct_issue_dates(connection, "7", [
        date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 3),
        date(2020, 1, 4), date(2020, 1, 5),
    ])
    assert [result["active_share_total"] for result in results] == [0, 100, 100, 0, 75]
    assert [result["active_participant_count"] for result in results] == [0, 1, 1, 0, 1]


def test_dates_outside_source_range_do_not_extrapolate():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.execute("INSERT INTO dailylog VALUES (?,?)", ("2020-01-03", "7"))
    connection.execute("INSERT INTO holdings VALUES (?,?,?,?)", ("1", "7", "100", "2020-01-03"))
    before = reconstruct_issue_at(connection, "7", date(2020, 1, 2))
    after = reconstruct_issue_at(connection, "7", date(2020, 1, 4))
    assert before["holdings_date"] is None and before["participant_rows"] == []
    assert after["holdings_date"] is None and after["participant_rows"] == []
