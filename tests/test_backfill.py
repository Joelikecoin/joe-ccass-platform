import logging
import sqlite3
from datetime import date

import pytest

from app.backfill_ccass import BackfillConfig, _exit_code, backfill_config_from_args, run_backfill
from app.domain.history import HistoricalSnapshot
from app.errors import ErrorCode, PlatformError
from app.storage.history import NormalizedSnapshotRepository


class FakeHistory:
    source_id = "google_drive_csv"
    page_count = 1

    def __init__(self, responses, *, failures=None, available=None):
        self.responses = responses
        self.failures = failures or {}
        self.available = available or tuple(sorted(responses))
        self.calls = []
        self.available_calls = 0

    async def available_dates(self, code):
        self.available_calls += 1
        return self.available

    async def get_holdings_for_date(self, code, requested_date, *, limit=10_000):
        self.calls.append(requested_date)
        queued = self.failures.get(requested_date, [])
        if queued:
            raise queued.pop(0)
        if requested_date not in self.responses:
            raise PlatformError(ErrorCode.DATE_UNAVAILABLE, "No verified fixture date")
        return self.responses[requested_date].model_copy(deep=True)


def on_date(response, value):
    copied = response.model_copy(deep=True)
    copied.metadata.holdings_date = value
    return copied


def cfg(tmp_path, **overrides):
    values = dict(
        stock_code="01592",
        sqlite_path=tmp_path / "backfill.db",
        source_mode="google_drive_csv",
        date_from=date(2026, 7, 19),
        date_to=date(2026, 7, 20),
        max_dates=10,
        max_pages=1,
        request_sleep_seconds=0,
        retry_attempts=1,
    )
    values.update(overrides)
    return BackfillConfig(**values)


def test_cli_range_latest_resume_and_invalid_inputs():
    ranged = backfill_config_from_args(
        ["--stock", "1592", "--from", "2026-07-19", "--to", "2026-07-20"]
    )
    assert ranged.date_from == date(2026, 7, 19)
    dry = backfill_config_from_args(["--stock", "01592", "--latest", "2", "--dry-run"])
    assert dry.latest_count == 2 and dry.dry_run
    assert backfill_config_from_args(["--stock", "01592", "--resume"]).resume
    with pytest.raises(SystemExit):
        backfill_config_from_args(["--stock", "01592", "--from", "2026-07-20"])
    with pytest.raises(SystemExit):
        backfill_config_from_args(
            ["--stock", "01592", "--from", "2026-07-20", "--to", "2026-07-19"]
        )
    with pytest.raises(SystemExit):
        backfill_config_from_args(["--stock", "01592", "--latest", "3", "--max-dates", "2"])


@pytest.mark.asyncio
async def test_bounds_and_unsupported_source_fail_before_network_or_write(tmp_path):
    source = FakeHistory({})
    invalid = cfg(tmp_path, max_dates=0)
    with pytest.raises(ValueError):
        await run_backfill(invalid, source=source)
    assert source.calls == [] and not invalid.sqlite_path.exists()
    source.page_count = 2
    with pytest.raises(PlatformError) as caught:
        await run_backfill(cfg(tmp_path), source=source)
    assert caught.value.code == ErrorCode.TOO_LARGE
    with pytest.raises(PlatformError) as caught:
        await run_backfill(cfg(tmp_path, source_mode="webbsite"))
    assert caught.value.code == ErrorCode.DATE_UNAVAILABLE
    assert not invalid.sqlite_path.exists()


@pytest.mark.asyncio
async def test_range_exact_dates_unavailable_skip_and_latest(tmp_path, current_response):
    day19, day20, day21 = date(2026, 7, 19), date(2026, 7, 20), date(2026, 7, 21)
    source = FakeHistory(
        {day19: on_date(current_response, day19), day20: on_date(current_response, day20)}
    )
    selected = cfg(tmp_path, date_to=day21)
    result = await run_backfill(selected, source=source)
    repository = NormalizedSnapshotRepository(selected.sqlite_path)
    items = repository.get_backfill_items(result.run_id)
    assert result.status == "PARTIAL"
    assert (result.success_count, result.skipped_count) == (2, 1)
    assert [item.status for item in items] == ["SUCCESS", "SUCCESS", "SKIPPED"]
    assert items[-1].error_code == ErrorCode.DATE_UNAVAILABLE
    assert repository.count_snapshots("01592") == 2

    latest_source = FakeHistory(
        {value: on_date(current_response, value) for value in (day19, day20, day21)}
    )
    latest_cfg = cfg(
        tmp_path,
        sqlite_path=tmp_path / "latest.db",
        date_from=None,
        date_to=None,
        latest_count=2,
    )
    latest = await run_backfill(latest_cfg, source=latest_source)
    assert latest.status == "SUCCESS"
    assert latest_source.available_calls == 1
    assert latest_source.calls == [day20, day21]


@pytest.mark.asyncio
async def test_dry_run_mismatch_partial_and_existing_skip(tmp_path, current_response):
    day19, day20 = date(2026, 7, 19), date(2026, 7, 20)
    dry = cfg(tmp_path, dry_run=True)
    source = FakeHistory(
        {day19: on_date(current_response, day19), day20: on_date(current_response, day20)}
    )
    result = await run_backfill(dry, source=source)
    assert result.status == "SUCCESS" and result.run_id is None
    assert not dry.sqlite_path.exists()

    mismatch_cfg = cfg(
        tmp_path,
        sqlite_path=tmp_path / "mismatch.db",
        date_from=day19,
        date_to=day19,
    )
    mismatch = await run_backfill(
        mismatch_cfg,
        source=FakeHistory({day19: on_date(current_response, day20)}),
    )
    mismatch_repo = NormalizedSnapshotRepository(mismatch_cfg.sqlite_path)
    assert mismatch.status == "ERROR" and mismatch_repo.count_snapshots() == 0
    assert (
        mismatch_repo.get_backfill_items(mismatch.run_id)[0].error_code == ErrorCode.SOURCE_CHANGED
    )

    partial_response = on_date(current_response, day20)
    partial_response.holdings = partial_response.holdings[:1]
    partial_cfg = cfg(
        tmp_path,
        sqlite_path=tmp_path / "partial.db",
        date_from=day20,
        date_to=day20,
    )
    partial = await run_backfill(partial_cfg, source=FakeHistory({day20: partial_response}))
    assert partial.status == "PARTIAL" and partial.partial_count == 1

    existing_cfg = cfg(
        tmp_path,
        sqlite_path=tmp_path / "existing.db",
        date_from=day20,
        date_to=day20,
    )
    existing_repo = NormalizedSnapshotRepository(existing_cfg.sqlite_path)
    existing_repo.save(
        HistoricalSnapshot.from_response(current_response, source_id="google_drive_csv")
    )
    existing_source = FakeHistory({day20: current_response})
    existing = await run_backfill(existing_cfg, source=existing_source, repository=existing_repo)
    assert existing.skipped_count == 1 and existing_source.calls == []
    assert existing_repo.count_snapshots() == 1

    database_before_dry_run = existing_cfg.sqlite_path.read_bytes()
    dry_existing_source = FakeHistory({day20: current_response})
    dry_existing = await run_backfill(
        cfg(
            tmp_path,
            sqlite_path=existing_cfg.sqlite_path,
            date_from=day20,
            date_to=day20,
            dry_run=True,
        ),
        source=dry_existing_source,
    )
    assert dry_existing.status == "SUCCESS" and dry_existing.run_id is None
    assert dry_existing_source.calls == [day20]
    assert existing_cfg.sqlite_path.read_bytes() == database_before_dry_run
    assert existing_repo.count_snapshots() == 1
    assert existing_repo.get_backfill_items(existing.run_id)[0].status == "SKIPPED"


@pytest.mark.asyncio
async def test_resume_retries_error_without_refetching_success(
    tmp_path, current_response, previous_response
):
    day19, day20 = date(2026, 7, 19), date(2026, 7, 20)
    timeout = PlatformError(ErrorCode.SOURCE_TIMEOUT, "offline timeout")
    selected = cfg(tmp_path)
    first = await run_backfill(
        selected,
        source=FakeHistory({day20: on_date(current_response, day20)}, failures={day19: [timeout]}),
    )
    assert (first.success_count, first.error_count) == (1, 1)
    resumed_source = FakeHistory(
        {day19: on_date(previous_response, day19), day20: on_date(current_response, day20)}
    )
    resumed = await run_backfill(
        cfg(tmp_path, date_from=None, date_to=None, resume=True),
        source=resumed_source,
    )
    assert resumed.run_id == first.run_id and resumed.status == "SUCCESS"
    assert resumed_source.calls == [day19]


@pytest.mark.asyncio
async def test_interrupt_retry_storage_isolation_and_safe_failure(
    tmp_path, current_response, caplog
):
    day19, day20 = date(2026, 7, 19), date(2026, 7, 20)
    interrupted_cfg = cfg(tmp_path, sqlite_path=tmp_path / "interrupt.db")
    interrupted_source = FakeHistory(
        {day19: on_date(current_response, day19)}, failures={day20: [KeyboardInterrupt()]}
    )
    with pytest.raises(KeyboardInterrupt):
        await run_backfill(interrupted_cfg, source=interrupted_source)
    connection = sqlite3.connect(interrupted_cfg.sqlite_path)
    try:
        assert connection.execute("SELECT status FROM backfill_runs").fetchone() == ("RUNNING",)
        assert connection.execute("SELECT COUNT(*) FROM backfill_run_items").fetchone() == (1,)
    finally:
        connection.close()

    retry_cfg = cfg(
        tmp_path,
        sqlite_path=tmp_path / "retry.db",
        retry_attempts=2,
        request_sleep_seconds=0.25,
    )
    sleep_delays = []

    async def fake_sleep(delay):
        sleep_delays.append(delay)

    secret = "https://drive.google.com/?token=private-token&key=secret-api-key"
    transient = PlatformError(ErrorCode.SOURCE_TIMEOUT, secret, retry_recommended=True)
    retry_source = FakeHistory(
        {day19: on_date(current_response, day19), day20: on_date(current_response, day20)},
        failures={day19: [transient]},
    )
    repository = NormalizedSnapshotRepository(retry_cfg.sqlite_path)
    original_save = repository.save
    save_calls = 0

    def flaky_save(snapshot):
        nonlocal save_calls
        save_calls += 1
        if save_calls == 1:
            raise sqlite3.OperationalError("offline storage failure")
        return original_save(snapshot)

    repository.save = flaky_save
    with caplog.at_level(logging.WARNING):
        result = await run_backfill(
            retry_cfg,
            source=retry_source,
            repository=repository,
            sleeper=fake_sleep,
        )
    assert retry_source.calls == [day19, day19, day20]
    assert sleep_delays == [0.25, 0.25]
    assert result.status == "PARTIAL"
    assert [item.status for item in repository.get_backfill_items(result.run_id)] == [
        "ERROR",
        "SUCCESS",
    ]

    parse_cfg = cfg(tmp_path, sqlite_path=tmp_path / "parse-isolation.db")
    parse_source = FakeHistory(
        {day20: on_date(current_response, day20)},
        failures={day19: [ValueError("parser exposed private-token")]},
    )
    parse_result = await run_backfill(parse_cfg, source=parse_source)
    parse_items = NormalizedSnapshotRepository(parse_cfg.sqlite_path).get_backfill_items(
        parse_result.run_id
    )
    assert parse_result.status == "PARTIAL"
    assert [item.status for item in parse_items] == ["ERROR", "SUCCESS"]
    assert "private-token" not in parse_items[0].safe_message

    database = retry_cfg.sqlite_path.read_bytes()
    assert b"private-token" not in database and b"secret-api-key" not in database
    assert "private-token" not in caplog.text and "secret-api-key" not in caplog.text


def test_exit_codes():
    from app.backfill_ccass import BackfillResult

    assert _exit_code(BackfillResult(None, "SUCCESS", 1, 0, 0, 0)) == 0
    assert _exit_code(BackfillResult(None, "PARTIAL", 0, 1, 0, 0)) == 2
    assert _exit_code(BackfillResult(None, "ERROR", 0, 0, 1, 0)) == 1
