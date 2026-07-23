import json
from datetime import date

import pytest

import app.backfill_ccass as backfill_module
import app.services.ccass as service_module
from app.backfill_ccass import BackfillConfig, run_backfill
from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.services.ccass import CcassService
from app.sources.registry import (
    GOOGLE_DRIVE_CSV_SOURCE_ID,
    WEBBSITE_SOURCE_ID,
    SourceAuditState,
    SourceCapability,
    SourceStatus,
    build_source_registry,
)

GOOGLE_URL = (
    "https://drive.google.com/file/d/registry-fixture/view"
    "?usp=sharing&resourcekey=private-resource-key"
)


def test_registry_has_truthful_capabilities_and_configured_policies():
    settings = Settings(
        ccass_csv_url=GOOGLE_URL,
        request_timeout_seconds=7.5,
        ccass_csv_max_bytes=123_456,
        webbsite_max_bytes=654_321,
        source_retry_attempts=3,
        min_request_interval_seconds=2.5,
        backfill_request_sleep_seconds=1.5,
        backfill_max_pages=4,
        cache_ttl_seconds=321,
        webbsite_audit_date=date(2026, 7, 22),
        google_drive_csv_audit_date=date(2026, 7, 23),
    )

    registry = build_source_registry(settings)
    webbsite = registry.get(WEBBSITE_SOURCE_ID)
    google = registry.get(GOOGLE_DRIVE_CSV_SOURCE_ID)

    assert webbsite.status == SourceStatus.ACTIVE
    assert webbsite.audit.state == SourceAuditState.APPROVED
    assert webbsite.audit.terms_review == "approved_existing_source_scope"
    assert webbsite.audit.robots_review == "approved_existing_source_scope"
    assert webbsite.capabilities == frozenset({SourceCapability.LATEST})
    assert webbsite.supported_sections == frozenset({"holdings"})
    assert not webbsite.fallback_eligible
    assert webbsite.policy.timeout_seconds == 7.5
    assert webbsite.policy.max_bytes == 654_321
    assert webbsite.policy.retry_attempts == 3
    assert webbsite.policy.minimum_interval_seconds == 2.5
    assert webbsite.policy.cache_ttl_seconds == 321

    assert google.status == SourceStatus.FALLBACK
    assert google.audit.state == SourceAuditState.APPROVED
    assert google.audit.terms_review == "approved_configured_import_scope"
    assert google.audit.robots_review == "not_applicable_no_crawling"
    assert google.capabilities == frozenset(
        {
            SourceCapability.LATEST,
            SourceCapability.REQUESTED_DATE,
            SourceCapability.HISTORICAL,
            SourceCapability.MANUAL_IMPORT,
        }
    )
    assert google.supported_sections == frozenset({"holdings"})
    assert google.fallback_eligible
    assert google.policy.max_bytes == 123_456
    assert google.policy.minimum_interval_seconds == 1.5
    assert google.policy.max_pages == 4
    assert google.policy.cache_policy == "process_memory"
    assert google.policy.last_known_good_policy == "process_memory"


def test_safe_diagnostics_redact_urls_queries_credentials_and_private_paths():
    diagnostics = build_source_registry(
        Settings(
            api_key="must-not-appear",
            ccass_csv_url=GOOGLE_URL,
            google_drive_csv_audit_state="unverified",
        )
    ).diagnostics()
    rendered = json.dumps(diagnostics)

    assert {item["source_id"] for item in diagnostics} == {
        WEBBSITE_SOURCE_ID,
        GOOGLE_DRIVE_CSV_SOURCE_ID,
    }
    google = next(item for item in diagnostics if item["source_id"] == GOOGLE_DRIVE_CSV_SOURCE_ID)
    assert google["status"] == "unverified"
    assert google["capabilities"] == ()
    assert google["disabled_reason"] == "audit_unverified"
    assert google["safe_hostname"] == "drive.google.com"
    assert google["terms_review"] == "approved_configured_import_scope"
    assert google["robots_review"] == "not_applicable_no_crawling"
    for forbidden in (
        "registry-fixture",
        "private-resource-key",
        "must-not-appear",
        "usp=",
        "resourcekey=",
        "authorization",
        "cookie",
        "C:\\Users\\",
    ):
        assert forbidden.lower() not in rendered.lower()


def test_registry_rejects_unknown_disabled_unconfigured_and_invalid_policy():
    registry = build_source_registry(Settings())
    with pytest.raises(PlatformError) as caught:
        registry.get("not-registered")
    assert caught.value.code == ErrorCode.SOURCE_DISABLED

    google = registry.get(GOOGLE_DRIVE_CSV_SOURCE_ID)
    assert not google.configured and not google.enabled
    assert google.capabilities == frozenset()
    with pytest.raises(PlatformError) as caught:
        registry.select_holdings("google_drive_csv")
    assert caught.value.code == ErrorCode.SOURCE_DISABLED

    disabled = build_source_registry(
        Settings(webbsite_enabled=False, google_drive_csv_enabled=False)
    )
    with pytest.raises(PlatformError) as caught:
        disabled.select_holdings("auto")
    assert caught.value.code == ErrorCode.SOURCE_DISABLED

    invalid_url = build_source_registry(Settings(ccass_csv_url="https://example.invalid/data.csv"))
    assert not invalid_url.get(GOOGLE_DRIVE_CSV_SOURCE_ID).configured

    with pytest.raises(ValueError):
        Settings(request_timeout_seconds=0)
    with pytest.raises(ValueError):
        Settings(source_retry_attempts=0)
    with pytest.raises(ValueError):
        Settings(cache_ttl_seconds=-1)


def test_historical_selection_never_falls_back_to_latest():
    registry = build_source_registry(Settings(ccass_csv_url=GOOGLE_URL))
    assert registry.select_historical("auto").source_id == GOOGLE_DRIVE_CSV_SOURCE_ID
    with pytest.raises(PlatformError) as caught:
        registry.select_historical("webbsite")
    assert caught.value.code == ErrorCode.DATE_UNAVAILABLE

    without_import = build_source_registry(Settings())
    with pytest.raises(PlatformError) as caught:
        without_import.select_historical("auto")
    assert caught.value.code == ErrorCode.DATE_UNAVAILABLE


async def test_service_auto_isolates_disabled_webbsite(monkeypatch, current_response):
    constructed = []

    class FixtureCsvSource:
        def __init__(self, settings):
            constructed.append("csv")

        async def get_holdings(self, code, limit=15):
            return current_response.model_copy(deep=True)

    def fail_webbsite(*args, **kwargs):
        raise AssertionError("disabled Webb-site source must remain isolated")

    monkeypatch.setattr(service_module, "GoogleDriveCsvSource", FixtureCsvSource)
    monkeypatch.setattr(service_module, "WebbsiteClient", fail_webbsite)
    service = CcassService(
        settings=Settings(
            data_source="auto",
            webbsite_enabled=False,
            ccass_csv_url=GOOGLE_URL,
        )
    )

    response = await service.get_stock_data("1592", holdings_limit=2)

    assert response.metadata.code == "01592"
    assert constructed == ["csv"]


async def test_backfill_uses_registry_for_exact_date_and_disabled_state(
    tmp_path, monkeypatch, current_response
):
    requested_date = current_response.metadata.holdings_date
    assert requested_date is not None
    calls = []

    class FixtureHistorySource:
        source_id = GOOGLE_DRIVE_CSV_SOURCE_ID
        page_count = 99

        def __init__(self, settings):
            calls.append("constructed")

        async def available_dates(self, code):
            return (requested_date,)

        async def get_holdings_for_date(self, code, value, *, limit=10_000):
            calls.append((code, value, limit))
            return current_response.model_copy(deep=True)

    monkeypatch.setattr(backfill_module, "GoogleDriveCsvSource", FixtureHistorySource)
    config = BackfillConfig(
        stock_code="01592",
        sqlite_path=tmp_path / "must-not-exist.db",
        source_mode="google_drive_csv",
        date_from=requested_date,
        date_to=requested_date,
        dry_run=True,
        max_dates=1,
        max_pages=1,
        request_sleep_seconds=0,
        retry_attempts=1,
    )

    result = await run_backfill(
        config,
        settings=Settings(data_source="google_drive_csv", ccass_csv_url=GOOGLE_URL),
    )

    assert result.status == "SUCCESS"
    assert calls == ["constructed", ("01592", requested_date, 10_000)]
    assert not config.sqlite_path.exists()

    with pytest.raises(PlatformError) as caught:
        await run_backfill(
            config,
            settings=Settings(
                data_source="google_drive_csv",
                ccass_csv_url=GOOGLE_URL,
                google_drive_csv_audit_state="disabled",
            ),
        )
    assert caught.value.code == ErrorCode.SOURCE_DISABLED
    assert calls == ["constructed", ("01592", requested_date, 10_000)]
