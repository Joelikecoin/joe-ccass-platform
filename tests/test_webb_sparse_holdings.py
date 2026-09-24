import sqlite3
from datetime import date

from app.services.webb_sparse_holdings import (
    UNKNOWN_SOURCE_ANOMALY_STATUS,
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


def _quarantine_schema(connection):
    connection.execute("CREATE TABLE quarantine_windows (issueID TEXT, partID TEXT, anomaly_id TEXT, quarantine_valid_from TEXT, quarantine_valid_to TEXT)")


def test_negative_mid_sequence_is_unknown_and_never_zero():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO dailylog VALUES (?,?)", [
        ("2020-01-01", "7"), ("2020-01-02", "7"), ("2020-01-03", "7"),
    ])
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("1", "7", "100", "2020-01-01"),
        ("1", "7", "-20", "2020-01-02"),
    ])
    windows = [{"issueID": "7", "partID": "1", "anomaly_id": "a1",
                "quarantine_valid_from": "2020-01-02", "quarantine_valid_to": "2020-01-03"}]
    result = reconstruct_issue_at(connection, "7", date(2020, 1, 3), quarantine_windows=windows)
    row = result["participant_rows"][0]
    assert row["position_status"] == UNKNOWN_SOURCE_ANOMALY_STATUS
    assert row["share_quantity"] is None
    assert result["active_share_total"] == 0
    assert result["unknown_source_anomaly_count"] == 1


def test_negative_first_observation_and_repeated_negative_are_unknown():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO dailylog VALUES (?,?)", [
        ("2020-01-01", "7"), ("2020-01-02", "7"), ("2020-01-03", "7"),
    ])
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("1", "7", "-20", "2020-01-01"), ("1", "7", "-20", "2020-01-02"),
        ("1", "7", "50", "2020-01-03"),
    ])
    windows = [{"issueID": "7", "partID": "1", "anomaly_id": "a1",
                "quarantine_valid_from": "2020-01-01", "quarantine_valid_to": "2020-01-02"}]
    first = reconstruct_issue_at(connection, "7", date(2020, 1, 1), quarantine_windows=windows)
    repeated = reconstruct_issue_at(connection, "7", date(2020, 1, 2), quarantine_windows=windows)
    assert first["participant_rows"][0]["share_quantity"] is None
    assert repeated["participant_rows"][0]["share_quantity"] is None


def test_negative_to_zero_and_negative_to_positive_close_quarantine():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO dailylog VALUES (?,?)", [
        ("2020-01-01", "7"), ("2020-01-02", "7"), ("2020-01-03", "7"),
        ("2020-01-04", "7"),
    ])
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("1", "7", "100", "2020-01-01"), ("1", "7", "-20", "2020-01-02"),
        ("1", "7", "0", "2020-01-03"), ("2", "7", "-10", "2020-01-02"),
        ("2", "7", "50", "2020-01-03"),
    ])
    windows = [
        {"issueID": "7", "partID": "1", "anomaly_id": "a1", "quarantine_valid_from": "2020-01-02", "quarantine_valid_to": "2020-01-02"},
        {"issueID": "7", "partID": "2", "anomaly_id": "a2", "quarantine_valid_from": "2020-01-02", "quarantine_valid_to": "2020-01-02"},
    ]
    result = reconstruct_issue_at(connection, "7", date(2020, 1, 3), quarantine_windows=windows)
    rows = {row["source_part_id"]: row for row in result["participant_rows"]}
    assert "1" not in rows
    assert rows["2"]["position_status"] == "VALID" and rows["2"]["share_quantity"] == 50


def test_open_ended_quarantine_and_idempotent_anomaly_rows():
    connection = sqlite3.connect(":memory:")
    _schema(connection)
    connection.executemany("INSERT INTO dailylog VALUES (?,?)", [
        ("2020-01-01", "7"), ("2020-01-02", "7"), ("2020-01-03", "7"),
    ])
    connection.execute("INSERT INTO holdings VALUES (?,?,?,?)", ("1", "7", "-20", "2020-01-01"))
    windows = [{"issueID": "7", "partID": "1", "anomaly_id": "a1",
                "quarantine_valid_from": "2020-01-01", "quarantine_valid_to": "2020-01-03"}]
    result = reconstruct_issue_at(connection, "7", date(2020, 1, 3), quarantine_windows=windows)
    assert result["participant_rows"][0]["share_quantity"] is None
    connection.execute("CREATE TABLE anomaly_rows (anomaly_id TEXT PRIMARY KEY, share_quantity INTEGER, position_status TEXT)")
    value = ("a1", None, UNKNOWN_SOURCE_ANOMALY_STATUS)
    connection.execute("INSERT OR IGNORE INTO anomaly_rows VALUES (?,?,?)", value)
    connection.execute("INSERT OR IGNORE INTO anomaly_rows VALUES (?,?,?)", value)
    assert connection.execute("SELECT COUNT(*) FROM anomaly_rows").fetchone()[0] == 1
