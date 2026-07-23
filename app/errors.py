from enum import StrEnum


class ErrorCode(StrEnum):
    COLD_START = "COLD_START"
    DATA_SOURCE_ERROR = "DATA_SOURCE_ERROR"
    SOURCE_FORBIDDEN = "SOURCE_FORBIDDEN"
    SOURCE_RATE_LIMITED = "SOURCE_RATE_LIMITED"
    SOURCE_TIMEOUT = "SOURCE_TIMEOUT"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    SOURCE_DISABLED = "SOURCE_DISABLED"
    PARSE_ERROR = "PARSE_ERROR"
    DATE_UNAVAILABLE = "DATE_UNAVAILABLE"
    DATA_STALE = "DATA_STALE"
    TOO_LARGE = "TOO_LARGE"
    INVALID_CODE = "INVALID_CODE"
    AUTH_FAILED = "AUTH_FAILED"
    NOT_FOUND = "NOT_FOUND"


class PlatformError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        retry_recommended: bool = False,
        retry_after_seconds: int | None = None,
        status_code: int = 502,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retry_recommended = retry_recommended
        self.retry_after_seconds = retry_after_seconds
        self.status_code = status_code

    def as_dict(self) -> dict:
        return {
            "error_code": self.code,
            "message": self.message,
            "retry_recommended": self.retry_recommended,
            "retry_after_seconds": self.retry_after_seconds,
        }
