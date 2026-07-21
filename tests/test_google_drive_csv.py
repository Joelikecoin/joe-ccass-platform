import logging

import httpx
import pytest
import respx

import app.services.ccass as ccass_service_module
from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.services.ccass import CcassService
from app.sources.google_drive_csv import GoogleDriveCsvSource, google_drive_download_url

CSV_HEADER = (
    "code,name,issue_id,holdings_date,rank,participant_id,participant,shares,last_change,"
    "pct_of_issued,cumulative_pct_of_issued,participant_category,total_in_ccass_shares,"
    "total_in_ccass_pct_of_issued,issued_shares,non_ccass_shares,non_ccass_pct_of_issued"
)
VALID_CSV = (
    CSV_HEADER
    + "\n700,Example Test Holdings,3601,2026-07-20,2,B00002,Test Broker Two,300,,3,5,broker,"
    "1000,10,10000,9000,90"
    + "\n00700,Example Test Holdings,3601,2026-07-20,1,B00001,Test Broker One,200,"
    "2026-07-19,2,2,broker,1000,10,10000,9000,90\n"
)


def csv_settings(**overrides) -> Settings:
    values = {
        "data_source": "google_drive_csv",
        "ccass_csv_url": "https://drive.google.com/file/d/test-file_123/view?usp=sharing",
        "ccass_csv_max_bytes": 10_000,
        "cache_ttl_seconds": 900,
        "request_timeout_seconds": 0.1,
        "api_key": "secret-api-key",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.parametrize(
    ("shared_url", "expected"),
    [
        (
            "https://drive.google.com/file/d/abc_123/view?usp=sharing",
            "https://drive.google.com/uc?export=download&id=abc_123",
        ),
        (
            "https://drive.google.com/uc?export=download&id=abc_123",
            "https://drive.google.com/uc?export=download&id=abc_123",
        ),
        (
            "https://drive.usercontent.google.com/download?id=abc_123&export=download",
            "https://drive.usercontent.google.com/download?id=abc_123&export=download",
        ),
        (
            "https://docs.google.com/spreadsheets/d/sheet_123/edit?gid=42",
            "https://docs.google.com/spreadsheets/d/sheet_123/export?format=csv&gid=42",
        ),
    ],
)
def test_google_drive_url_conversion(shared_url, expected):
    assert google_drive_download_url(shared_url) == expected


@respx.mock
async def test_csv_source_queries_by_code_limits_holdings_and_uses_cache():
    route = respx.get("https://drive.google.com/uc?export=download&id=test-file_123").mock(
        return_value=httpx.Response(
            200, content=VALID_CSV.encode(), headers={"content-type": "text/csv"}
        )
    )
    source = GoogleDriveCsvSource(csv_settings())

    first = await source.get_holdings("00700", limit=1)
    second = await source.get_holdings("00700", limit=2)

    assert len(route.calls) == 1
    assert first.metadata.code == "00700"
    assert first.metadata.name == "Example Test Holdings"
    assert first.metadata.source_name == "Google Drive CSV"
    assert first.metadata.source_url == "https://drive.google.com/"
    assert first.metadata.cached is False
    assert [row.rank for row in first.holdings] == [1]
    assert len(second.holdings) == 2
    assert second.metadata.cached is True
    assert second.holdings_summary.participant_count == 2


def test_csv_mode_does_not_construct_webbsite_client(monkeypatch):
    def forbidden_webbsite_client(*args, **kwargs):
        raise AssertionError("Webb-site client must not be constructed in CSV mode")

    monkeypatch.setattr(ccass_service_module, "WebbsiteClient", forbidden_webbsite_client)
    service = CcassService(settings=csv_settings())

    assert isinstance(service.source, GoogleDriveCsvSource)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"<html>sign in</html>", headers={"content-type": "text/html"}),
        httpx.Response(200, content=b"<!doctype html><a href='accounts.google.com'>Login</a>"),
    ],
)
@respx.mock
async def test_html_or_google_login_page_returns_clear_data_source_error(response):
    respx.get("https://drive.google.com/uc?export=download&id=test-file_123").mock(
        return_value=response
    )

    with pytest.raises(PlatformError) as caught:
        await GoogleDriveCsvSource(csv_settings()).get_holdings("00700")

    assert caught.value.code == ErrorCode.DATA_SOURCE_ERROR
    assert "HTML or a Google sign-in page" in caught.value.message


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=VALID_CSV.encode(), headers={"content-length": "99999"}),
        httpx.Response(200, content=VALID_CSV.encode()),
    ],
)
@respx.mock
async def test_download_enforces_declared_and_actual_size_limits(response):
    respx.get("https://drive.google.com/uc?export=download&id=test-file_123").mock(
        return_value=response
    )

    with pytest.raises(PlatformError) as caught:
        await GoogleDriveCsvSource(csv_settings(ccass_csv_max_bytes=20)).get_holdings("00700")

    assert caught.value.code == ErrorCode.DATA_SOURCE_ERROR
    assert "size limit" in caught.value.message


@respx.mock
async def test_download_timeout_is_data_source_error_without_secret_logging(caplog):
    respx.get("https://drive.google.com/uc?export=download&id=test-file_123").mock(
        side_effect=httpx.ReadTimeout("secret-api-key?token=do-not-log")
    )

    with caplog.at_level(logging.WARNING), pytest.raises(PlatformError) as caught:
        await GoogleDriveCsvSource(csv_settings()).get_holdings("00700")

    assert caught.value.code == ErrorCode.DATA_SOURCE_ERROR
    assert "timed out" in caught.value.message
    assert "hostname=drive.google.com status_code=none error_type=timeout" in caplog.text
    assert "secret-api-key" not in caplog.text
    assert "test-file_123" not in caplog.text
    assert "token=" not in caplog.text


@respx.mock
async def test_last_known_good_is_served_when_refresh_fails():
    route = respx.get("https://drive.google.com/uc?export=download&id=test-file_123")
    route.side_effect = [
        httpx.Response(200, content=VALID_CSV.encode()),
        httpx.Response(503, text="unavailable"),
    ]
    source = GoogleDriveCsvSource(csv_settings(cache_ttl_seconds=0))

    first = await source.get_holdings("00700")
    stale = await source.get_holdings("00700")

    assert len(route.calls) == 2
    assert first.metadata.cached is False
    assert stale.metadata.cached is True
    assert stale.metadata.fetched_at == first.metadata.fetched_at
    assert "last-known-good" in stale.data_quality_warnings[0]


@pytest.mark.parametrize(
    "content",
    [
        b"code,name\n00700,Missing fields\n",
        CSV_HEADER.encode(),
        VALID_CSV.replace("B00002", "B00001").encode(),
        (CSV_HEADER + ",code\n" + VALID_CSV.splitlines()[1] + ",00700\n").encode(),
    ],
)
def test_csv_schema_and_rows_are_validated(content):
    with pytest.raises(PlatformError) as caught:
        GoogleDriveCsvSource._parse(content)

    assert caught.value.code == ErrorCode.DATA_SOURCE_ERROR
