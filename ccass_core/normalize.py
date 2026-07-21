import re

from app.errors import ErrorCode, PlatformError


def normalize_stock_code(value: str | int) -> str:
    """Normalize a one-to-five digit HK stock code to five digits."""
    raw_value = str(value).strip()
    if not re.fullmatch(r"\d{1,5}", raw_value):
        raise PlatformError(
            ErrorCode.INVALID_CODE,
            "Stock code must contain only 1 to 5 digits.",
            status_code=422,
        )
    return raw_value.zfill(5)
