import pytest

from app.core.normalizers import normalize_stock_code
from app.errors import ErrorCode, PlatformError


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("700", "00700"), ("0700", "00700"), ("00700", "00700"), (8123, "08123")],
)
def test_normalize_stock_code(raw, expected):
    assert normalize_stock_code(raw) == expected


def test_invalid_stock_code():
    with pytest.raises(PlatformError) as caught:
        normalize_stock_code("ABC")
    assert caught.value.code == ErrorCode.INVALID_CODE
