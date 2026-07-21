import csv
from datetime import datetime

from app.sources.google_drive_csv import GoogleDriveCsvSource
from ccass_core.collector import (
    DEFAULT_WATCHLIST,
    CollectorConfig,
    SnapshotStore,
    collect_watchlist,
    export_latest_csv,
    parse_watchlist,
)


def test_collector_defaults_to_golden_01592_and_normalizes_watchlist():
    assert DEFAULT_WATCHLIST == ("01592",)
    assert parse_watchlist("1592, 700") == ("01592", "00700")


async def test_collector_uses_injected_offline_fetcher_and_exports_schema(
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
    assert "T+2" in row["settlement_note"]


def test_snapshot_store_keeps_history_and_exports_latest(tmp_path, previous_response, current_response):
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
