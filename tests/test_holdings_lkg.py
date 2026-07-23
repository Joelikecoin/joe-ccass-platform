import csv
import json
import sqlite3
from datetime import date, timedelta

import pytest

import app.services.ccass as service_module
from app.config import Settings
from app.domain.history import HistoricalSnapshot
from app.errors import ErrorCode, PlatformError
from app.services.holdings_lkg import (
    FreshnessStatus,
    PersistentLatestHoldingsSource,
    freshness_status,
)
from app.sources.registry import WEBBSITE_SOURCE_ID, build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.collector import CollectorConfig, collect_watchlist


class FixtureSource:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    async def get_holdings(self, code, limit=15):
        self.calls.append((code, limit))
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome.model_copy(deep=True)


def _settings(**changes) -> Settings:
    return Settings(data_source="webbsite", **changes)


def _webbsite_response(current_response):
    response = current_response.model_copy(deep=True)
    response.metadata.source_name = "Webb-site mirror"
    response.metadata.source_url = "https://webbsite.example.invalid/ccass/choldings.asp"
    return response


def _wrapper(source, repository, settings, now):
    definitions = build_source_registry(settings).select_holdings("webbsite")
    return PersistentLatestHoldingsSource(
        source,
        repository=repository,
        definitions=definitions,
        clock=lambda: now,
    )


async def test_verified_fresh_snapshot_persists_and_survives_restart(
    tmp_path, current_response
):
    settings = _settings()
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    fresh = _webbsite_response(current_response)
    served_at = fresh.metadata.fetched_at + timedelta(hours=1)
    source = FixtureSource(fresh)

    response = await _wrapper(source, repository, settings, served_at).get_holdings(
        "01592", limit=2
    )

    assert source.calls == [("01592", 10_000)]
    assert freshness_status(response) == FreshnessStatus.FRESH
    assert len(response.holdings) == 2
    assert repository.count_snapshots("01592") == 1
    stored = repository.latest("01592", source_id=WEBBSITE_SOURCE_ID)
    assert stored is not None
    assert len(stored.holdings) == stored.participant_count == 3
    assert stored.issued_shares_as_of == date(2026, 7, 20)
    assert stored.holdings[0].pct_of_ccass == 45.454545

    timeout = PlatformError(
        ErrorCode.SOURCE_TIMEOUT,
        "Offline latest Holdings timeout.",
        retry_recommended=True,
        retry_after_seconds=30,
        status_code=504,
    )
    restarted = _wrapper(
        FixtureSource(timeout),
        NormalizedSnapshotRepository(tmp_path / "history.db"),
        settings,
        served_at + timedelta(days=1),
    )
    stale = await restarted.get_holdings("01592", limit=1)

    assert freshness_status(stale) == FreshnessStatus.STALE_LKG
    assert stale.metadata.cached is True
    assert stale.metadata.holdings_date == fresh.metadata.holdings_date
    assert stale.metadata.fetched_at == fresh.metadata.fetched_at
    assert len(stale.holdings) == 1
    rendered = "\n".join(stale.data_quality_warnings)
    assert "SOURCE_ERROR_CODE: SOURCE_TIMEOUT" in rendered
    assert "SOURCE_ERROR_MESSAGE: Offline latest Holdings timeout." in rendered
    assert "SOURCE_ERROR_RETRY_RECOMMENDED: true" in rendered
    assert "SOURCE_ERROR_RETRY_AFTER_SECONDS: 30" in rendered
    assert f"LKG_RETRIEVED_AT: {fresh.metadata.fetched_at.isoformat()}" in rendered
    assert "LKG_AGE_SECONDS: 90000" in rendered
    assert repository.count_snapshots("01592") == 1


@pytest.mark.parametrize(
    "error_code",
    [
        ErrorCode.DATA_SOURCE_ERROR,
        ErrorCode.SOURCE_CHANGED,
        ErrorCode.PARSE_ERROR,
        ErrorCode.NOT_FOUND,
        ErrorCode.SOURCE_DISABLED,
        ErrorCode.DATE_UNAVAILABLE,
    ],
)
async def test_integrity_and_non_transient_errors_never_use_lkg(
    tmp_path, current_response, error_code
):
    settings = _settings()
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    fresh = _webbsite_response(current_response)
    definition = build_source_registry(settings).get(WEBBSITE_SOURCE_ID)
    repository.save(
        HistoricalSnapshot.from_response(
            fresh,
            source_id=WEBBSITE_SOURCE_ID,
            parser_version=definition.parser_version,
        )
    )
    error = PlatformError(error_code, "Offline prohibited fallback fixture.")

    with pytest.raises(PlatformError) as caught:
        await _wrapper(
            FixtureSource(error),
            repository,
            settings,
            fresh.metadata.fetched_at + timedelta(hours=1),
        ).get_holdings("01592")

    assert caught.value.code == error_code
    assert caught.value.message.startswith("UNAVAILABLE:")


async def test_missing_expired_and_incompatible_lkg_fail_loudly(
    tmp_path, current_response
):
    settings = _settings(holdings_lkg_max_age_seconds=60)
    fresh = _webbsite_response(current_response)
    timeout = PlatformError(ErrorCode.SOURCE_TIMEOUT, "Offline timeout.")
    empty = NormalizedSnapshotRepository(tmp_path / "empty.db")
    with pytest.raises(PlatformError) as missing:
        await _wrapper(
            FixtureSource(timeout),
            empty,
            settings,
            fresh.metadata.fetched_at + timedelta(seconds=30),
        ).get_holdings("01592")
    assert missing.value.code == ErrorCode.SOURCE_TIMEOUT
    assert missing.value.message.startswith("UNAVAILABLE:")

    expired_repo = NormalizedSnapshotRepository(tmp_path / "expired.db")
    definition = build_source_registry(settings).get(WEBBSITE_SOURCE_ID)
    expired_repo.save(
        HistoricalSnapshot.from_response(
            fresh,
            source_id=WEBBSITE_SOURCE_ID,
            parser_version=definition.parser_version,
        )
    )
    with pytest.raises(PlatformError) as expired:
        await _wrapper(
            FixtureSource(timeout),
            expired_repo,
            settings,
            fresh.metadata.fetched_at + timedelta(seconds=61),
        ).get_holdings("01592")
    assert expired.value.code == ErrorCode.DATA_STALE

    incompatible_repo = NormalizedSnapshotRepository(tmp_path / "incompatible.db")
    incompatible_repo.save(
        HistoricalSnapshot.from_response(
            fresh,
            source_id=WEBBSITE_SOURCE_ID,
            parser_version="obsolete-parser",
        )
    )
    with pytest.raises(PlatformError) as incompatible:
        await _wrapper(
            FixtureSource(timeout),
            incompatible_repo,
            settings,
            fresh.metadata.fetched_at + timedelta(seconds=30),
        ).get_holdings("01592")
    assert incompatible.value.code == ErrorCode.SOURCE_CHANGED


async def test_partial_or_failed_persistence_never_promotes_bad_lkg(
    tmp_path, current_response, monkeypatch
):
    settings = _settings()
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    partial = _webbsite_response(current_response)
    partial.holdings = partial.holdings[:1]
    served_at = partial.metadata.fetched_at + timedelta(hours=1)

    response = await _wrapper(
        FixtureSource(partial), repository, settings, served_at
    ).get_holdings("01592")
    assert freshness_status(response) == FreshnessStatus.FRESH
    assert repository.count_snapshots("01592") == 0

    complete = _webbsite_response(current_response)

    def fail_transaction(snapshot):
        raise sqlite3.OperationalError("offline transaction fixture")

    monkeypatch.setattr(repository, "save", fail_transaction)
    response = await _wrapper(
        FixtureSource(complete), repository, settings, served_at
    ).get_holdings("01592")
    assert freshness_status(response) == FreshnessStatus.FRESH
    assert any(
        warning.startswith("LKG_PERSISTENCE_ERROR:")
        for warning in response.data_quality_warnings
    )
    assert repository.count_snapshots("01592") == 0


async def test_collector_records_stale_lkg_without_rewriting_snapshot_or_csv_date(
    tmp_path, current_response, monkeypatch
):
    response = _webbsite_response(current_response)
    outcomes = iter(
        (
            response,
            PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                "Offline collector timeout.",
                retry_recommended=True,
                status_code=504,
            ),
        )
    )

    class SequencedWebbsite:
        def __init__(self, settings):
            self.outcome = next(outcomes)

        async def get_holdings(self, code, limit=15):
            if isinstance(self.outcome, Exception):
                raise self.outcome
            return self.outcome.model_copy(deep=True)

    monkeypatch.setattr(service_module, "WebbsiteClient", SequencedWebbsite)
    database = tmp_path / "collector.db"
    output = tmp_path / "latest.csv"
    config = CollectorConfig(
        sqlite_path=database,
        csv_output_path=output,
        source_mode="webbsite",
    )
    settings = _settings()

    await collect_watchlist(config, settings=settings)
    collected, failures = await collect_watchlist(config, settings=settings)

    assert failures == {}
    assert freshness_status(collected[0]) == FreshnessStatus.STALE_LKG
    repository = NormalizedSnapshotRepository(database)
    assert repository.count_snapshots("01592") == 1
    with output.open(encoding="utf-8-sig", newline="") as handle:
        exported = next(csv.DictReader(handle))
    assert exported["holdings_date"] == response.metadata.holdings_date.isoformat()
    assert exported["snapshot_fetched_at"] == response.metadata.fetched_at.isoformat()
    assert "STALE_LKG" in exported["data_quality_warnings"]

    connection = sqlite3.connect(database)
    try:
        runs = connection.execute(
            "SELECT status, success_count, partial_count, error_count "
            "FROM collector_runs ORDER BY id"
        ).fetchall()
        item = connection.execute(
            "SELECT status, snapshot_id, safe_details_json "
            "FROM collector_run_items ORDER BY id DESC LIMIT 1"
        ).fetchone()
        error = connection.execute(
            "SELECT error_code, safe_message, retry_recommended, "
            "retry_after_seconds, safe_details_json "
            "FROM source_errors ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        connection.close()
    assert runs == [("SUCCESS", 1, 0, 0), ("PARTIAL", 0, 1, 0)]
    assert item[0:2] == ("PARTIAL", 1)
    assert json.loads(item[2])["freshness"] == "STALE_LKG"
    assert error[0:4] == ("SOURCE_TIMEOUT", "Offline collector timeout.", 1, None)
    assert json.loads(error[4]) == {"served_lkg": True}
