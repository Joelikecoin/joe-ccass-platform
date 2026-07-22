import json
import sqlite3
from pathlib import Path
from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domain.history import (
    CollectorRunItemRecord,
    CollectorRunRecord,
    HistoricalSnapshot,
    SourceErrorRecord,
)
from app.models import CcassResponse
from app.storage.history import NormalizedSnapshotRepository
from app.storage.migrations import MIGRATION_1, Migration, SCHEMA_VERSION, apply_migrations
from ccass_core.collector import SnapshotStore

REQUIRED_TABLES = {
    "schema_migrations",
    "stocks",
    "source_issue_mapping",
    "raw_provenance",
    "ccass_snapshots",
    "ccass_holdings",
    "collector_runs",
    "collector_run_items",
    "source_errors",
    "legacy_snapshot_imports",
}

GOLDEN_FIXTURE = Path("tests/fixtures/01592_ccass_response.json")


def test_migration_creates_required_schema_and_is_idempotent(tmp_path):
    database = tmp_path / "history.db"
    connection = sqlite3.connect(database, isolation_level=None)
    try:
        assert apply_migrations(connection) == SCHEMA_VERSION
        assert apply_migrations(connection) == SCHEMA_VERSION
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        versions = connection.execute("SELECT version, name FROM schema_migrations").fetchall()
    finally:
        connection.close()

    assert REQUIRED_TABLES <= tables
    assert versions == [
        (1, "normalized_historical_foundation"),
        (2, "collector_run_items"),
    ]


def test_version_one_database_upgrades_without_losing_collector_runs(tmp_path):
    connection = sqlite3.connect(tmp_path / "upgrade.db", isolation_level=None)
    try:
        assert apply_migrations(connection, migrations=(MIGRATION_1,)) == 1
        connection.execute(
            """
            INSERT INTO collector_runs(
                started_at, status, source_id, requested_codes_json, safe_details_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime(2026, 7, 22, tzinfo=UTC).isoformat(),
                "RUNNING",
                "auto",
                '["01592"]',
                "{}",
            ),
        )
        assert apply_migrations(connection) == SCHEMA_VERSION
        run = connection.execute(
            "SELECT source_id, requested_codes_json FROM collector_runs"
        ).fetchone()
        table = connection.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'collector_run_items'
            """
        ).fetchone()
    finally:
        connection.close()

    assert run == ("auto", '["01592"]')
    assert table == (1,)


def test_failed_migration_rolls_back_every_statement(tmp_path):
    connection = sqlite3.connect(tmp_path / "rollback.db", isolation_level=None)
    broken = Migration(
        99,
        "broken_test_migration",
        (
            "CREATE TABLE rollback_probe(id INTEGER PRIMARY KEY)",
            "CREATE TABL invalid_sql(id INTEGER)",
        ),
    )
    try:
        with pytest.raises(sqlite3.OperationalError):
            apply_migrations(connection, migrations=(broken,))
        probe = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'rollback_probe'"
        ).fetchone()
        version = connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version = 99"
        ).fetchone()
    finally:
        connection.close()

    assert probe is None
    assert version is None


def test_saved_01592_fixture_is_offline_and_never_claims_live_data(tmp_path):
    fixture_text = GOLDEN_FIXTURE.read_text(encoding="utf-8")
    response = CcassResponse.model_validate_json(fixture_text)
    repository = NormalizedSnapshotRepository(tmp_path / "golden.db")

    repository.save_response(
        response,
        provenance_bytes=fixture_text.encode("utf-8"),
        provenance_reference="fixture:tests/fixtures/01592_ccass_response.json",
    )
    stored = repository.latest("01592")

    assert response.metadata.code == "01592"
    assert "SYNTHETIC" in response.metadata.attribution
    assert "NOT PRODUCTION" in response.metadata.attribution
    assert any("DO NOT USE AS PRODUCTION" in warning for warning in response.data_quality_warnings)
    assert stored.stock.code == "01592"
    assert stored.partial is False
    assert stored.provenance.safe_reference.startswith("fixture:")


def test_repository_round_trip_is_idempotent_and_redacts_query(tmp_path, current_response):
    current_response.metadata.source_url = (
        "https://fixture.invalid/ccass/holdings?code=01592&token=must-not-persist"
    )
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")

    first_id = repository.save_response(
        current_response,
        issued_shares_as_of=date(2026, 7, 20),
    )
    second_id = repository.save_response(
        current_response,
        issued_shares_as_of=date(2026, 7, 20),
    )
    stored = repository.latest("01592")

    assert first_id == second_id
    assert repository.count_snapshots("01592") == 1
    assert stored is not None
    assert stored.issued_shares_as_of == date(2026, 7, 20)
    assert stored.denominator == "issued_shares"
    assert stored.source.safe_identifier == "https://fixture.invalid/ccass/holdings"
    assert stored.source.display_name == current_response.metadata.source_name
    assert stored.holdings[0].pct_of_ccass == 37.5
    round_trip = stored.to_response()
    assert round_trip.metadata.source_url == "https://fixture.invalid/ccass/holdings"
    assert round_trip.model_dump(exclude={"metadata": {"source_url"}}) == (
        current_response.model_dump(exclude={"metadata": {"source_url"}})
    )

    database_bytes = (tmp_path / "history.db").read_bytes()
    assert b"must-not-persist" not in database_bytes


def test_latest_previous_and_date_range_return_source_neutral_snapshots(
    tmp_path, current_response, previous_response
):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    repository.save_response(previous_response)
    repository.save_response(current_response)

    latest = repository.latest("01592")
    previous = repository.previous("01592", before_date=date(2026, 7, 20))
    history = repository.date_range(
        "01592",
        date_from=date(2026, 7, 19),
        date_to=date(2026, 7, 20),
    )

    assert latest.snapshot_date == date(2026, 7, 20)
    assert previous.snapshot_date == date(2026, 7, 19)
    assert [snapshot.snapshot_date for snapshot in history] == [
        date(2026, 7, 19),
        date(2026, 7, 20),
    ]
    assert all(isinstance(snapshot, HistoricalSnapshot) for snapshot in history)


def test_partial_snapshot_keeps_missing_rows_absent_and_cannot_replace_complete(
    tmp_path, current_response
):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    complete_id = repository.save_response(current_response)

    partial_response = current_response.model_copy(deep=True)
    partial_response.holdings = partial_response.holdings[:1]
    partial_response.metadata.fetched_at += timedelta(minutes=5)
    protected_id = repository.save_response(partial_response)

    assert protected_id == complete_id
    protected = repository.latest("01592")
    assert protected.partial is False
    assert len(protected.holdings) == 3

    partial_id = repository.save_response(partial_response, source_id="partial_fixture")
    partial = repository.latest("01592", source_id="partial_fixture")
    assert partial_id != complete_id
    assert partial.partial is True
    assert partial.participant_count == 3
    assert len(partial.holdings) == 1
    assert {row.participant_id for row in partial.holdings} == {"B00001"}
    assert any(
        "partial" in warning.lower() for warning in partial.to_response().data_quality_warnings
    )


def test_participant_rename_is_preserved_per_snapshot(
    tmp_path, current_response, previous_response
):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    previous_response.holdings[1].participant = "BROKER OLD NAME"
    current_response.holdings[0].participant = "BROKER NEW NAME"

    repository.save_response(previous_response)
    repository.save_response(current_response)

    history = repository.date_range(
        "01592",
        date_from=date(2026, 7, 19),
        date_to=date(2026, 7, 20),
    )
    renamed_rows = [
        next(row for row in snapshot.holdings if row.participant_id == "B00001")
        for snapshot in history
    ]
    assert [row.participant_id for row in renamed_rows] == ["B00001", "B00001"]
    assert [row.participant_name for row in renamed_rows] == [
        "BROKER OLD NAME",
        "BROKER NEW NAME",
    ]


def test_duplicate_participant_and_rank_are_rejected_before_persistence(
    current_response,
):
    duplicate_participant = current_response.model_copy(deep=True)
    duplicate_participant.holdings[1].participant_id = "B00001"
    with pytest.raises(ValidationError, match="duplicate participant"):
        HistoricalSnapshot.from_response(duplicate_participant)

    duplicate_rank = current_response.model_copy(deep=True)
    duplicate_rank.holdings[1].rank = 1
    with pytest.raises(ValidationError, match="duplicate ranks"):
        HistoricalSnapshot.from_response(duplicate_rank)


def test_transaction_failure_leaves_no_half_snapshot(tmp_path, current_response, monkeypatch):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")

    def fail_after_snapshot(*args, **kwargs):
        raise RuntimeError("offline rollback fixture")

    monkeypatch.setattr(repository, "_insert_holdings", fail_after_snapshot)

    with pytest.raises(RuntimeError, match="offline rollback fixture"):
        repository.save_response(current_response)

    connection = sqlite3.connect(tmp_path / "history.db")
    try:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "stocks",
                "source_issue_mapping",
                "raw_provenance",
                "ccass_snapshots",
                "ccass_holdings",
            )
        }
    finally:
        connection.close()
    assert counts == {table: 0 for table in counts}


def test_legacy_json_snapshots_are_preserved_and_imported_once(tmp_path, current_response):
    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            """
            CREATE TABLE snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                holdings_date TEXT,
                source_cached INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO snapshots(
                code, fetched_at, holdings_date, source_cached, payload_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "01592",
                current_response.metadata.fetched_at.isoformat(),
                current_response.metadata.holdings_date.isoformat(),
                0,
                current_response.model_dump_json(),
            ),
        )
        connection.commit()
    finally:
        connection.close()

    first = NormalizedSnapshotRepository(database)
    second = NormalizedSnapshotRepository(database)

    assert first.count_snapshots("01592") == 1
    assert second.count_snapshots("01592") == 1
    connection = sqlite3.connect(database)
    try:
        legacy_count = connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        import_row = connection.execute(
            "SELECT status, normalized_snapshot_id FROM legacy_snapshot_imports"
        ).fetchone()
    finally:
        connection.close()
    assert legacy_count == 1
    assert import_row[0] == "IMPORTED"
    assert import_row[1] is not None


def test_legacy_missing_date_remains_readable_for_previous_snapshot(
    tmp_path, current_response, previous_response
):
    database = tmp_path / "legacy_missing_date.db"
    previous_response.metadata.holdings_date = None
    current_response.metadata.holdings_date = None
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            """
            CREATE TABLE snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                holdings_date TEXT,
                source_cached INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        for response in (previous_response, current_response):
            connection.execute(
                """
                INSERT INTO snapshots(
                    code, fetched_at, holdings_date, source_cached, payload_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "01592",
                    response.metadata.fetched_at.isoformat(),
                    None,
                    0,
                    response.model_dump_json(),
                ),
            )
        connection.commit()
    finally:
        connection.close()

    store = SnapshotStore(database)
    previous = store.previous_for("01592", current_response)

    assert previous is not None
    assert previous.metadata.fetched_at == previous_response.metadata.fetched_at
    connection = sqlite3.connect(database)
    try:
        legacy_count = connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        statuses = connection.execute(
            "SELECT status FROM legacy_snapshot_imports ORDER BY legacy_snapshot_id"
        ).fetchall()
    finally:
        connection.close()
    assert legacy_count == 2
    assert statuses == [("PRESERVED_LEGACY_ONLY",), ("PRESERVED_LEGACY_ONLY",)]


def test_percentage_over_100_and_t2_metadata_are_preserved(tmp_path, current_response):
    current_response.holdings_summary.total_in_ccass_pct_of_issued = 120.5
    current_response.data_quality_warnings.append(
        "CCASS percentage exceeds 100%; denominator may be stale."
    )
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")

    repository.save_response(current_response)
    stored = repository.latest("01592")

    assert stored.total_in_ccass_pct_of_issued == 120.5
    assert any("100%" in warning for warning in stored.warnings)
    assert "T+2" in stored.settlement_note


def test_run_and_safe_error_metadata_are_persisted(tmp_path):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    run_id = repository.create_collector_run(
        CollectorRunRecord(
            started_at=datetime(2026, 7, 22, tzinfo=UTC),
            status="RUNNING",
            source_id="webbsite_mirror",
            requested_codes=("01592",),
            safe_details={"mode": "offline-test"},
        )
    )
    error_id = repository.record_source_error(
        SourceErrorRecord(
            run_id=run_id,
            source_id="webbsite_mirror",
            stock_code="01592",
            error_code="SOURCE_TIMEOUT",
            safe_message="Mirror timed out.",
            retry_recommended=True,
            retry_after_seconds=30,
            safe_details={"hostname": "fixture.invalid"},
        )
    )

    connection = sqlite3.connect(tmp_path / "history.db")
    try:
        run = connection.execute(
            "SELECT requested_codes_json, safe_details_json FROM collector_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        error = connection.execute(
            "SELECT error_code, safe_details_json FROM source_errors WHERE id = ?",
            (error_id,),
        ).fetchone()
    finally:
        connection.close()

    assert json.loads(run[0]) == ["01592"]
    assert json.loads(run[1]) == {"mode": "offline-test"}
    assert error[0] == "SOURCE_TIMEOUT"
    assert json.loads(error[1]) == {"hostname": "fixture.invalid"}


def test_collector_result_and_completion_are_persisted(tmp_path):
    repository = NormalizedSnapshotRepository(tmp_path / "runs.db")
    started_at = datetime(2026, 7, 22, tzinfo=UTC)
    run_id = repository.create_collector_run(
        CollectorRunRecord(
            started_at=started_at,
            status="RUNNING",
            source_id="auto",
            requested_codes=("01592",),
        )
    )
    item_id = repository.record_collector_result(
        CollectorRunItemRecord(
            run_id=run_id,
            stock_code="01592",
            status="PARTIAL",
            source_id="webbsite_mirror",
            snapshot_date=date(2026, 7, 21),
            partial=True,
            safe_details={"rows": 1, "participant_count": 3},
        )
    )
    repository.complete_collector_run(
        run_id,
        completed_at=started_at + timedelta(minutes=1),
        status="PARTIAL",
        success_count=0,
        partial_count=1,
        error_count=0,
        safe_details={"exported": True},
    )

    connection = sqlite3.connect(tmp_path / "runs.db")
    try:
        run = connection.execute(
            """
            SELECT status, completed_at, success_count, partial_count, error_count,
                   safe_details_json
            FROM collector_runs WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
        item = connection.execute(
            """
            SELECT id, status, source_id, snapshot_date, partial, safe_details_json
            FROM collector_run_items WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
    finally:
        connection.close()

    assert run[:5] == (
        "PARTIAL",
        (started_at + timedelta(minutes=1)).isoformat(),
        0,
        1,
        0,
    )
    assert json.loads(run[5]) == {"exported": True}
    assert item[:5] == (item_id, "PARTIAL", "webbsite_mirror", "2026-07-21", 1)
    assert json.loads(item[5]) == {"participant_count": 3, "rows": 1}


def test_collector_failure_item_and_error_roll_back_together(tmp_path, monkeypatch):
    repository = NormalizedSnapshotRepository(tmp_path / "runs.db")
    run_id = repository.create_collector_run(
        CollectorRunRecord(
            started_at=datetime(2026, 7, 22, tzinfo=UTC),
            status="RUNNING",
            source_id="auto",
            requested_codes=("01592",),
        )
    )

    def fail_error_insert(*args, **kwargs):
        raise sqlite3.OperationalError("offline error insert failure")

    monkeypatch.setattr(repository, "_insert_source_error", fail_error_insert)
    item = CollectorRunItemRecord(
        run_id=run_id,
        stock_code="01592",
        status="ERROR",
        source_id="auto",
    )
    error = SourceErrorRecord(
        run_id=run_id,
        source_id="auto",
        stock_code="01592",
        error_code="SOURCE_TIMEOUT",
        safe_message="Fixture timeout.",
    )
    with pytest.raises(sqlite3.OperationalError, match="offline error insert failure"):
        repository.record_collector_failure(item, error)

    connection = sqlite3.connect(tmp_path / "runs.db")
    try:
        item_count = connection.execute("SELECT COUNT(*) FROM collector_run_items").fetchone()[0]
        error_count = connection.execute("SELECT COUNT(*) FROM source_errors").fetchone()[0]
    finally:
        connection.close()
    assert item_count == 0
    assert error_count == 0
