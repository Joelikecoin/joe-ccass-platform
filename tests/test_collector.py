import csv
import json
import logging
import sqlite3
from datetime import datetime

import pytest

import app.services.ccass as service_module
import ccass_core.collector as collector_module
from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.sources.google_drive_csv import GoogleDriveCsvSource
from ccass_core.collector import (
    DEFAULT_COLLECTION_LIMIT,
    DEFAULT_WATCHLIST,
    CollectorConfig,
    SnapshotStore,
    _collector_exit_code,
    collect_watchlist,
    collector_config_from_args,
    configure_logging,
    export_latest_csv,
    parse_watchlist,
)


def test_collector_defaults_to_golden_01592_and_normalizes_watchlist(tmp_path):
    assert DEFAULT_WATCHLIST == ("01592",)
    assert DEFAULT_COLLECTION_LIMIT == 10_000
    assert parse_watchlist("1592, 700,1592") == ("01592", "00700")

    watchlist = tmp_path / "watchlist.txt"
    watchlist.write_text("# offline fixture\n1592\n700\n", encoding="utf-8")
    assert parse_watchlist(str(watchlist)) == ("01592", "00700")


def test_collector_cli_supports_scoped_source_date_and_dry_run():
    config = collector_config_from_args(
        [
            "--stocks",
            "1592,700",
            "--source",
            "google_drive_csv",
            "--date",
            "latest",
            "--dry-run",
            "--limit",
            "250",
        ]
    )

    assert config.watchlist == ("01592", "00700")
    assert config.source_mode == "google_drive_csv"
    assert config.data_date == "latest"
    assert config.dry_run is True
    assert config.effective_collection_limit == 250


def test_collector_exit_code_distinguishes_success_partial_and_error(current_response):
    partial = current_response.model_copy(deep=True)
    partial.holdings = partial.holdings[:1]

    assert _collector_exit_code([current_response], {}) == 0
    assert _collector_exit_code([partial], {}) == 2
    assert _collector_exit_code([current_response], {"00700": "SOURCE_TIMEOUT"}) == 1


def test_collector_suppresses_third_party_request_url_logs():
    configure_logging()

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING


async def test_collector_uses_injected_offline_fetcher_records_run_and_exports_schema(
    tmp_path, current_response
):
    calls = []

    async def fixture_fetcher(code, limit):
        calls.append((code, limit))
        return current_response

    database = tmp_path / "collector.db"
    output = tmp_path / "drive-sync" / "ccass.csv"
    config = CollectorConfig(
        watchlist=("1592",),
        sqlite_path=database,
        csv_output_path=output,
        holdings_limit=50,
    )

    collected, failures = await collect_watchlist(config, fetcher=fixture_fetcher)

    assert calls == [("01592", 50)]
    assert len(collected) == 1
    assert failures == {}
    assert output.exists()
    assert not list(output.parent.glob("*.tmp"))
    parsed = GoogleDriveCsvSource._parse(output.read_bytes())
    assert parsed["01592"].name == "TEST FIXTURE — GOLDEN STOCK"
    with output.open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert datetime.fromisoformat(row["snapshot_fetched_at"]).isoformat() == (
        "2026-07-21T01:00:00+00:00"
    )
    assert row["source_cached"] == "false"
    assert row["snapshot_partial"] == "false"
    assert row["source_identifier"] == "https://fixture.invalid/"
    assert json.loads(row["data_quality_warnings"]) == ["TEST FIXTURE warning"]
    assert row["parser_version"] == "ccass-response-v1"
    assert row["schema_version"] == "1"
    assert "T+2" in row["settlement_note"]

    connection = sqlite3.connect(database)
    try:
        run = connection.execute(
            """
            SELECT status, success_count, partial_count, error_count, safe_details_json
            FROM collector_runs
            """
        ).fetchone()
        item = connection.execute(
            """
            SELECT stock_code, status, partial, snapshot_id, safe_details_json
            FROM collector_run_items
            """
        ).fetchone()
    finally:
        connection.close()
    assert run[:4] == ("SUCCESS", 1, 0, 0)
    assert json.loads(run[4]) == {"date": "latest", "exported": True}
    assert item[:4] == ("01592", "SUCCESS", 0, 1)
    assert json.loads(item[4]) == {"participant_count": 3, "rows": 3}


@pytest.mark.parametrize("source_mode", ["auto", "webbsite", "google_drive_csv"])
async def test_collector_passes_each_existing_source_mode_to_shared_service(
    tmp_path, current_response, monkeypatch, source_mode
):
    constructed = []

    class FixtureService:
        def __init__(self, settings):
            constructed.append(settings.data_source)

        async def get_stock_data(self, code, holdings_limit=15):
            return current_response

    monkeypatch.setattr(collector_module, "CcassService", FixtureService)
    config = CollectorConfig(
        sqlite_path=tmp_path / "must-not-exist.db",
        csv_output_path=tmp_path / "must-not-exist.csv",
        source_mode=source_mode,
        dry_run=True,
    )
    settings = Settings(data_source=source_mode, ccass_csv_url="https://fixture.invalid")

    collected, failures = await collect_watchlist(config, settings=settings)

    assert constructed == [source_mode]
    assert [response.metadata.code for response in collected] == ["01592"]
    assert failures == {}


async def test_csv_only_collector_never_constructs_webbsite_client(
    tmp_path, current_response, monkeypatch
):
    class FixtureCsvSource:
        def __init__(self, settings):
            self.settings = settings

        async def get_holdings(self, code, limit=15):
            assert code == "01592"
            assert limit == DEFAULT_COLLECTION_LIMIT
            return current_response

    def fail_if_constructed(*args, **kwargs):
        raise AssertionError("CSV-only collector must not construct WebbsiteClient")

    monkeypatch.setattr(service_module, "GoogleDriveCsvSource", FixtureCsvSource)
    monkeypatch.setattr(service_module, "WebbsiteClient", fail_if_constructed)
    settings = Settings(
        data_source="google_drive_csv",
        ccass_csv_url="https://drive.google.com/open?id=collector-fixture",
    )
    config = CollectorConfig(
        sqlite_path=tmp_path / "collector.db",
        csv_output_path=tmp_path / "latest.csv",
        source_mode="google_drive_csv",
    )

    collected, failures = await collect_watchlist(config, settings=settings)

    assert [response.metadata.code for response in collected] == ["01592"]
    assert failures == {}


async def test_dry_run_validates_without_database_run_records_or_csv(tmp_path, current_response):
    database = tmp_path / "must-not-exist.db"
    output = tmp_path / "must-not-exist.csv"
    calls = []

    async def fixture_fetcher(code, limit):
        calls.append((code, limit))
        return current_response

    config = CollectorConfig(
        sqlite_path=database,
        csv_output_path=output,
        dry_run=True,
        collection_limit=321,
    )
    collected, failures = await collect_watchlist(config, fetcher=fixture_fetcher)

    assert calls == [("01592", 321)]
    assert len(collected) == 1
    assert failures == {}
    assert not database.exists()
    assert not output.exists()


async def test_partial_collection_is_marked_and_cannot_replace_complete(tmp_path, current_response):
    database = tmp_path / "collector.db"
    output = tmp_path / "latest.csv"
    complete = current_response.model_copy(deep=True)
    partial = current_response.model_copy(deep=True)
    partial.holdings = partial.holdings[:1]
    partial.metadata.fetched_at = partial.metadata.fetched_at.replace(minute=5)
    responses = iter((complete, partial))

    async def fixture_fetcher(code, limit):
        return next(responses)

    config = CollectorConfig(sqlite_path=database, csv_output_path=output)
    await collect_watchlist(config, fetcher=fixture_fetcher)
    collected, failures = await collect_watchlist(config, fetcher=fixture_fetcher)

    assert failures == {}
    assert len(collected[0].holdings) == 1
    assert any("PARTIAL_DATA" in warning for warning in collected[0].data_quality_warnings)
    repository = SnapshotStore(database).repository
    stored = repository.latest("01592")
    assert stored.partial is False
    assert len(stored.holdings) == 3
    assert repository.count_snapshots("01592") == 1

    connection = sqlite3.connect(database)
    try:
        runs = connection.execute(
            "SELECT status, success_count, partial_count, error_count FROM collector_runs ORDER BY id"
        ).fetchall()
        items = connection.execute(
            "SELECT status, partial FROM collector_run_items ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
    assert runs == [("SUCCESS", 1, 0, 0), ("PARTIAL", 0, 1, 0)]
    assert items == [("SUCCESS", 0), ("PARTIAL", 1)]


async def test_mixed_batch_isolated_and_persists_safe_error_metadata(tmp_path, current_response):
    database = tmp_path / "collector.db"
    output = tmp_path / "latest.csv"

    async def fixture_fetcher(code, limit):
        if code == "00700":
            raise PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                "Fixture mirror timed out.",
                retry_recommended=True,
                retry_after_seconds=30,
                status_code=504,
            )
        return current_response

    config = CollectorConfig(
        watchlist=("01592", "00700"),
        sqlite_path=database,
        csv_output_path=output,
    )
    collected, failures = await collect_watchlist(config, fetcher=fixture_fetcher)

    assert [response.metadata.code for response in collected] == ["01592"]
    assert failures == {"00700": "SOURCE_TIMEOUT: Fixture mirror timed out."}
    assert output.exists()
    connection = sqlite3.connect(database)
    try:
        run = connection.execute(
            "SELECT status, success_count, partial_count, error_count FROM collector_runs"
        ).fetchone()
        items = connection.execute(
            "SELECT stock_code, status FROM collector_run_items ORDER BY stock_code"
        ).fetchall()
        error = connection.execute(
            """
            SELECT stock_code, error_code, safe_message, retry_recommended,
                   retry_after_seconds, safe_details_json
            FROM source_errors
            """
        ).fetchone()
    finally:
        connection.close()
    assert run == ("PARTIAL", 1, 0, 1)
    assert items == [("00700", "ERROR"), ("01592", "SUCCESS")]
    assert error[:5] == ("00700", "SOURCE_TIMEOUT", "Fixture mirror timed out.", 1, 30)
    assert json.loads(error[5]) == {}


async def test_duplicate_collection_runs_do_not_duplicate_snapshot(tmp_path, current_response):
    database = tmp_path / "collector.db"
    output = tmp_path / "latest.csv"

    async def fixture_fetcher(code, limit):
        return current_response

    config = CollectorConfig(sqlite_path=database, csv_output_path=output)
    await collect_watchlist(config, fetcher=fixture_fetcher)
    await collect_watchlist(config, fetcher=fixture_fetcher)

    repository = SnapshotStore(database).repository
    assert repository.count_snapshots("01592") == 1
    connection = sqlite3.connect(database)
    try:
        run_count = connection.execute("SELECT COUNT(*) FROM collector_runs").fetchone()[0]
        item_count = connection.execute("SELECT COUNT(*) FROM collector_run_items").fetchone()[0]
    finally:
        connection.close()
    assert run_count == 2
    assert item_count == 2


def test_atomic_export_failure_preserves_previous_good_file(
    tmp_path, current_response, monkeypatch
):
    store = SnapshotStore(tmp_path / "history.db")
    store.save(current_response)
    output = tmp_path / "latest.csv"
    output.write_text("previous-good-export", encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("offline atomic replace failure")

    monkeypatch.setattr("ccass_core.collector.os.replace", fail_replace)
    with pytest.raises(OSError, match="offline atomic replace failure"):
        export_latest_csv(store, output)

    assert output.read_text(encoding="utf-8") == "previous-good-export"
    assert not list(tmp_path.glob("*.tmp"))


def test_snapshot_store_keeps_history_and_exports_latest(
    tmp_path, previous_response, current_response
):
    store = SnapshotStore(tmp_path / "history.db")
    store.save(previous_response)
    store.save(current_response)
    output = tmp_path / "latest.csv"

    export_latest_csv(store, output)

    assert store.latest("01592").metadata.holdings_date.isoformat() == "2026-07-20"
    assert store.previous_for("01592", current_response).metadata.holdings_date.isoformat() == (
        "2026-07-19"
    )
    parsed = GoogleDriveCsvSource._parse(output.read_bytes())
    assert parsed["01592"].holdings_date.isoformat() == "2026-07-20"
