import pytest

from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.services.ccass import MirrorWithCsvFallback


class FailingMirror:
    async def get_holdings(self, code, limit=15):
        raise PlatformError(ErrorCode.SOURCE_TIMEOUT, "Offline mirror timeout fixture")


class FixtureCsv:
    def __init__(self, response):
        self.response = response

    async def get_holdings(self, code, limit=15):
        return self.response.model_copy(deep=True)


class FailingCsv:
    async def get_holdings(self, code, limit=15):
        raise PlatformError(ErrorCode.DATA_SOURCE_ERROR, "Offline CSV failure fixture")


async def test_auto_source_uses_configured_csv_only_after_mirror_failure(current_response):
    source = MirrorWithCsvFallback(Settings(ccass_csv_url="https://drive.google.com/open?id=test"))
    source.mirror = FailingMirror()
    source.csv = FixtureCsv(current_response)

    response = await source.get_holdings("01592", limit=20)

    assert response.metadata.source_name == "Offline test fixture"
    assert "Primary mirror failed (SOURCE_TIMEOUT)" in response.data_quality_warnings[-1]


async def test_auto_source_without_csv_preserves_mirror_error():
    source = MirrorWithCsvFallback(Settings(ccass_csv_url=""))
    source.mirror = FailingMirror()

    with pytest.raises(PlatformError) as caught:
        await source.get_holdings("01592")

    assert caught.value.code == ErrorCode.SOURCE_TIMEOUT


async def test_auto_source_reports_both_primary_and_fallback_failure_codes():
    source = MirrorWithCsvFallback(Settings(ccass_csv_url="https://drive.google.com/open?id=test"))
    source.mirror = FailingMirror()
    source.csv = FailingCsv()

    with pytest.raises(PlatformError) as caught:
        await source.get_holdings("01592")

    assert caught.value.code == ErrorCode.DATA_SOURCE_ERROR
    assert "Primary mirror failed (SOURCE_TIMEOUT)" in caught.value.message
    assert "CSV fallback also failed (DATA_SOURCE_ERROR)" in caught.value.message
