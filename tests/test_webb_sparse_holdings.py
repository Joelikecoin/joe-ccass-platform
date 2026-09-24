import sqlite3
from datetime import date

from app.services.webb_sparse_holdings import reconstruct_issue_at


def test_sparse_changes_carry_forward_and_zero_ends_position():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE holdings (c1 TEXT, c2 TEXT, c3 TEXT, c4 TEXT)")
    connection.executemany("INSERT INTO holdings VALUES (?,?,?,?)", [
        ("P1", "1088", "100", "2013-03-01"),
        ("P2", "1088", "50", "2013-03-02"),
        ("P1", "1088", "0", "2013-03-03"),
        ("P3", "999", "500", "2013-03-03"),
    ])
    result = reconstruct_issue_at(connection, "1088", date(2013, 3, 4))
    assert result["source_changes_seen"] == 3
    assert result["zero_position_count"] == 1
    assert result["participant_rows"] == [{
        "source_issue_id": "1088", "source_part_id": "P2",
        "share_quantity": 50, "last_change_date": "2013-03-02",
        "holdings_date": "2013-03-04",
    }]
