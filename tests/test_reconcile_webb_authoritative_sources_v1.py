from __future__ import annotations

import sqlite3

from scripts import reconcile_webb_authoritative_sources_v1 as reconciliation
from scripts.validate_webb_authoritative_batch_v1 import validate
from scripts.webb_quarantine_staged_backfill_sql_v1 import SCHEMA, _insert_select, _source_counts


def test_inspect_uses_preverified_hash_and_matches_exact_negative_ledger(tmp_path, monkeypatch):
    source = tmp_path / "webb.sqlite"
    with sqlite3.connect(source) as database:
        database.executescript(
            """
            CREATE TABLE holdings(c1 TEXT, c2 TEXT, c3 INTEGER, c4 TEXT);
            CREATE TABLE shortnames(c1 TEXT);
            CREATE TABLE participants(c1 TEXT);
            INSERT INTO holdings VALUES
              ('participant-1','issue-1',100,'2007-06-26'),
              ('participant-2','issue-2',-25,'2025-12-24');
            INSERT INTO shortnames VALUES ('issue-1'),('issue-2');
            INSERT INTO participants VALUES ('participant-1'),('participant-2');
            """
        )

    def unexpected_hash(_path):
        raise AssertionError("preverified hash must avoid a second full-file read")

    monkeypatch.setattr(reconciliation, "sha256", unexpected_hash)
    expected_hash = "A" * 64
    report = reconciliation.inspect(
        source,
        expected_hash,
        {("issue-2", "participant-2", "2025-12-24"): -25},
        preverified_hash=expected_hash,
    )

    assert report["status"] == "PASS"
    assert report["hash_match"] is True
    assert report["sqlite_integrity_status"] == "ok"
    assert report["total_source_rows"] == 2
    assert report["date_min"] == "2007-06-26"
    assert report["date_max"] == "2025-12-24"
    assert report["yearly_row_counts"]["2007"] == 1
    assert report["yearly_row_counts"]["2025"] == 1
    assert report["negative_row_count"] == 1
    assert report["negative_ledger_match_count"] == 1
    assert report["negative_ledger_missing_count"] == 0
    assert report["negative_ledger_value_mismatch_count"] == 0
    assert report["negative_rows_not_in_ledger"] == 0


def test_inspect_reports_missing_candidate_without_opening_it(tmp_path):
    report = reconciliation.inspect(
        tmp_path / "missing.sqlite",
        "B" * 64,
        {},
    )

    assert report == {
        "path": str(tmp_path / "missing.sqlite"),
        "present": False,
        "expected_sha256": "B" * 64,
        "status": "MISSING",
    }


def test_source_counts_separates_raw_rows_from_canonical_eligible_rows():
    with sqlite3.connect(":memory:") as database:
        database.execute("ATTACH DATABASE ':memory:' AS source")
        database.execute("CREATE TABLE source.holdings(c1 TEXT,c2 TEXT,c3 INTEGER,c4 TEXT)")
        database.executemany(
            "INSERT INTO source.holdings VALUES (?,?,?,?)",
            [
                ("p1", "i1", 10, "2025-01-02"),
                ("p1", "i1", 0, "2025-01-03"),
                ("p2", "i2", -5, "2025-01-04"),
            ],
        )
        counts = _source_counts(database, "2025-01-01", "2026-01-01")

    assert counts["raw_source_rows"] == 3
    assert counts["source_rows"] == 2
    assert counts["valid_source_rows"] == 1
    assert counts["raw_negative_rows"] == 1
    assert counts["zero_source_rows"] == 1


def test_set_based_insert_is_resumable_and_idempotent():
    with sqlite3.connect(":memory:") as database:
        database.executescript(SCHEMA)
        database.execute("ATTACH DATABASE ':memory:' AS source")
        database.executescript(
            """
            CREATE TABLE source.holdings(c1 TEXT,c2 TEXT,c3 INTEGER,c4 TEXT);
            INSERT INTO source.holdings VALUES
              ('p1','i1',10,'2025-01-02'),
              ('p1','i1',0,'2025-01-03');
            CREATE TABLE issue_identity(
              source_issue_id TEXT PRIMARY KEY, canonical_security_id TEXT,
              hk_stock_codes TEXT, mapping_status TEXT
            );
            CREATE TABLE participant_identity(
              source_participant_id TEXT PRIMARY KEY, canonical_participant_id TEXT,
              participant_name TEXT, identity_status TEXT
            );
            CREATE TABLE quarantine_windows(
              issueID TEXT, partID TEXT, quarantine_valid_from TEXT,
              quarantine_valid_to TEXT, anomaly_ids TEXT
            );
            """
        )
        first = _insert_select(database, "2025-01-01", "2026-01-01", "A" * 64, "test")
        second = _insert_select(database, "2025-01-01", "2026-01-01", "A" * 64, "test")
        readback = database.execute("SELECT COUNT(*) FROM canonical_historical_holdings").fetchone()[0]

    assert first == 1
    assert second == 0
    assert readback == 1


def test_fast_batch_validator_checks_hard_gates(tmp_path):
    target = tmp_path / "batch.sqlite"
    source_hash = "C" * 64
    with sqlite3.connect(target) as database:
        database.executescript(SCHEMA)
        database.execute("ATTACH DATABASE ':memory:' AS source")
        database.executescript(
            """
            CREATE TABLE source.holdings(c1 TEXT,c2 TEXT,c3 INTEGER,c4 TEXT);
            INSERT INTO source.holdings VALUES ('p1','i1',10,'2025-01-02');
            CREATE TABLE issue_identity(
              source_issue_id TEXT PRIMARY KEY, canonical_security_id TEXT,
              hk_stock_codes TEXT, mapping_status TEXT
            );
            CREATE TABLE participant_identity(
              source_participant_id TEXT PRIMARY KEY, canonical_participant_id TEXT,
              participant_name TEXT, identity_status TEXT
            );
            CREATE TABLE quarantine_windows(
              issueID TEXT, partID TEXT, quarantine_valid_from TEXT,
              quarantine_valid_to TEXT, anomaly_ids TEXT
            );
            """
        )
        assert _insert_select(database, "2025-01-01", "2026-01-01", source_hash, "test") == 1

    report = validate(target, "BATCH_TEST", source_hash, 1, 1, 0)

    assert report["pass"] is True
    assert report["row_reconciliation_pass"] is True
    assert report["duplicate_conflict_safety_pass"] is True
    assert report["canonical_data_safety_pass"] is True
    assert report["readback_checkpoint_pass"] is True
    assert report["idempotent_repeat_additional_rows"] == 0
