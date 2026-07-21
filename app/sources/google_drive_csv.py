import asyncio
import csv
import io
import logging
import math
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx

from app.config import Settings, get_settings
from app.core.normalizers import normalize_stock_code
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "code",
    "name",
    "issue_id",
    "holdings_date",
    "rank",
    "participant_id",
    "participant",
    "shares",
    "last_change",
    "pct_of_issued",
    "cumulative_pct_of_issued",
    "participant_category",
    "total_in_ccass_shares",
    "total_in_ccass_pct_of_issued",
    "issued_shares",
    "non_ccass_shares",
    "non_ccass_pct_of_issued",
}
GOOGLE_DRIVE_HOSTS = {
    "drive.google.com",
    "drive.usercontent.google.com",
    "docs.google.com",
}
GOOGLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
STOCK_COLUMNS = (
    "name",
    "issue_id",
    "holdings_date",
    "total_in_ccass_shares",
    "total_in_ccass_pct_of_issued",
    "issued_shares",
    "non_ccass_shares",
    "non_ccass_pct_of_issued",
)


@dataclass(frozen=True, slots=True)
class CsvStock:
    code: str
    name: str
    issue_id: int
    holdings_date: date | None
    holdings: tuple[HoldingRow, ...]
    total_in_ccass_shares: int | None
    total_in_ccass_pct_of_issued: float | None
    issued_shares: int | None
    non_ccass_shares: int | None
    non_ccass_pct_of_issued: float | None


@dataclass(frozen=True, slots=True)
class CsvSnapshot:
    stocks: dict[str, CsvStock]
    fetched_at: datetime
    stored_at: float


def google_drive_download_url(value: str) -> str:
    """Convert supported Google Drive sharing URLs into CSV download URLs."""
    try:
        parsed = urlsplit(value.strip())
    except ValueError as exc:
        raise _data_source_error("CCASS_CSV_URL is not a valid URL.") from exc

    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in GOOGLE_DRIVE_HOSTS:
        raise _data_source_error("CCASS_CSV_URL must be an HTTPS Google Drive URL.")

    query = parse_qs(parsed.query)
    resource_key = _single_query_value(query, "resourcekey", required=False)

    if hostname == "docs.google.com":
        match = re.fullmatch(r"/spreadsheets/d/([^/]+)(?:/.*)?", parsed.path)
        if not match:
            raise _data_source_error("The Google Sheets sharing URL format is not supported.")
        file_id = _validate_google_id(match.group(1))
        params = {"format": "csv"}
        gid = _single_query_value(query, "gid", required=False)
        if gid:
            params["gid"] = gid
        return urlunsplit(("https", hostname, f"/spreadsheets/d/{file_id}/export", urlencode(params), ""))

    if hostname == "drive.usercontent.google.com":
        file_id = _validate_google_id(_single_query_value(query, "id"))
        params = {"id": file_id, "export": "download"}
        if resource_key:
            params["resourcekey"] = resource_key
        return urlunsplit(("https", hostname, "/download", urlencode(params), ""))

    file_match = re.fullmatch(r"/file/d/([^/]+)(?:/.*)?", parsed.path)
    file_id = file_match.group(1) if file_match else _single_query_value(query, "id", required=False)
    file_id = _validate_google_id(file_id)
    params = {"export": "download", "id": file_id}
    if resource_key:
        params["resourcekey"] = resource_key
    return urlunsplit(("https", "drive.google.com", "/uc", urlencode(params), ""))


class GoogleDriveCsvSource:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._snapshot: CsvSnapshot | None = None
        self._refresh_lock = asyncio.Lock()

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        snapshot, cached, stale_warning = await self._get_snapshot()
        stock = snapshot.stocks.get(code)
        if stock is None:
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                f"Stock code {code} was not found in the configured CCASS CSV.",
                status_code=404,
            )

        holdings = list(stock.holdings)
        top5 = holdings[:5]
        top10 = holdings[:10]

        def pct_of_ccass(rows: list[HoldingRow]) -> float | None:
            total = stock.total_in_ccass_shares
            return round(sum(row.shares for row in rows) / total * 100, 4) if total else None

        warnings = [stale_warning] if stale_warning else []
        return CcassResponse(
            metadata=SourceMetadata(
                code=stock.code,
                name=stock.name,
                issue_id=stock.issue_id,
                holdings_date=stock.holdings_date,
                fetched_at=snapshot.fetched_at,
                source_url=self._safe_source_url(),
                source_name="Google Drive CSV",
                cached=cached,
                attribution="Data supplied through the configured Google Drive CSV.",
            ),
            holdings_summary=HoldingsSummary(
                total_in_ccass_shares=stock.total_in_ccass_shares,
                total_in_ccass_pct_of_issued=stock.total_in_ccass_pct_of_issued,
                issued_shares=stock.issued_shares,
                non_ccass_shares=stock.non_ccass_shares,
                non_ccass_pct_of_issued=stock.non_ccass_pct_of_issued,
                participant_count=len(holdings),
                top5_pct_of_issued=sum(row.pct_of_issued for row in top5),
                top10_pct_of_issued=sum(row.pct_of_issued for row in top10),
                top5_pct_of_ccass=pct_of_ccass(top5),
                top10_pct_of_ccass=pct_of_ccass(top10),
            ),
            holdings=holdings[: max(1, min(limit, 100))],
            data_quality_warnings=warnings,
        )

    async def _get_snapshot(self) -> tuple[CsvSnapshot, bool, str | None]:
        now = time.monotonic()
        if self._snapshot and now - self._snapshot.stored_at < self.settings.cache_ttl_seconds:
            return self._snapshot, True, None

        async with self._refresh_lock:
            now = time.monotonic()
            if self._snapshot and now - self._snapshot.stored_at < self.settings.cache_ttl_seconds:
                return self._snapshot, True, None
            try:
                content = await self._download()
                snapshot = CsvSnapshot(self._parse(content), datetime.now(UTC), time.monotonic())
            except PlatformError:
                if self._snapshot is None:
                    raise
                return (
                    self._snapshot,
                    True,
                    "CSV refresh failed; serving the last-known-good in-memory snapshot.",
                )
            self._snapshot = snapshot
            return snapshot, False, None

    async def _download(self) -> bytes:
        if not self.settings.ccass_csv_url.strip():
            raise _data_source_error(
                "CCASS_CSV_URL is required when DATA_SOURCE=google_drive_csv."
            )
        url = google_drive_download_url(self.settings.ccass_csv_url)
        hostname = urlsplit(url).hostname or "unknown"
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout_seconds,
                follow_redirects=True,
                headers={
                    "User-Agent": self.settings.user_agent,
                    "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
                },
            ) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        self._log_failure(hostname, response.status_code, "http_status")
                        raise _data_source_error(
                            f"Google Drive CSV download returned HTTP {response.status_code}.",
                            retry_recommended=response.status_code >= 500,
                        )
                    declared_size = response.headers.get("content-length")
                    if declared_size and int(declared_size) > self.settings.ccass_csv_max_bytes:
                        raise _data_source_error("Google Drive CSV exceeds the configured size limit.")
                    chunks: list[bytes] = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > self.settings.ccass_csv_max_bytes:
                            raise _data_source_error(
                                "Google Drive CSV exceeds the configured size limit."
                            )
                        chunks.append(chunk)
                    content = b"".join(chunks)
                    content_type = response.headers.get("content-type", "").lower()
        except PlatformError:
            raise
        except httpx.TimeoutException as exc:
            self._log_failure(hostname, None, "timeout")
            raise _data_source_error(
                "Google Drive CSV download timed out.", retry_recommended=True
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            self._log_failure(hostname, None, type(exc).__name__)
            raise _data_source_error(
                "Google Drive CSV download failed.", retry_recommended=True
            ) from exc

        if _looks_like_html(content, content_type):
            raise _data_source_error(
                "CCASS_CSV_URL returned HTML or a Google sign-in page instead of CSV; "
                "check that link sharing allows downloads without signing in."
            )
        return content

    @staticmethod
    def _parse(content: bytes) -> dict[str, CsvStock]:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise _data_source_error("CCASS CSV must be UTF-8 encoded.") from exc
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        fieldnames = reader.fieldnames or []
        columns = set(fieldnames)
        if len(fieldnames) != len(columns):
            raise _data_source_error("CCASS CSV contains duplicate column names.")
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise _data_source_error(f"CCASS CSV is missing required columns: {', '.join(missing)}.")

        grouped: dict[str, list[dict[str, str]]] = {}
        try:
            csv_rows = enumerate(reader, start=2)
            for line_number, raw_row in csv_rows:
                if None in raw_row:
                    raise _data_source_error(
                        f"CCASS CSV row {line_number} has more values than columns."
                    )
                row = {key: (value or "").strip() for key, value in raw_row.items()}
                try:
                    code = normalize_stock_code(row["code"])
                except PlatformError as exc:
                    raise _data_source_error(
                        f"CCASS CSV row {line_number} has an invalid code."
                    ) from exc
                grouped.setdefault(code, []).append(row)
        except csv.Error as exc:
            raise _data_source_error("CCASS CSV has invalid CSV syntax.") from exc
        if not grouped:
            raise _data_source_error("CCASS CSV contains no data rows.")
        return {code: _parse_stock(code, rows) for code, rows in grouped.items()}

    def _safe_source_url(self) -> str:
        parsed = urlsplit(self.settings.ccass_csv_url)
        return f"https://{parsed.hostname}/" if parsed.hostname else "https://drive.google.com/"

    @staticmethod
    def _log_failure(hostname: str, status_code: int | None, error_type: str) -> None:
        logger.warning(
            "Google Drive CSV failed hostname=%s status_code=%s error_type=%s",
            hostname,
            status_code if status_code is not None else "none",
            error_type,
        )


def _parse_stock(code: str, rows: list[dict[str, str]]) -> CsvStock:
    first = rows[0]
    identity = tuple(first[field] for field in STOCK_COLUMNS)
    for row in rows[1:]:
        if tuple(row[field] for field in STOCK_COLUMNS) != identity:
            raise _data_source_error(f"CCASS CSV has inconsistent metadata for code {code}.")
    try:
        name = _required(first, "name")
        issue_id = _positive_int(first["issue_id"], "issue_id")
        holdings_date = _optional_date(first["holdings_date"], "holdings_date")
        total_in_ccass_shares = _optional_non_negative_int(
            first["total_in_ccass_shares"], "total_in_ccass_shares"
        )
        total_in_ccass_pct = _optional_float(
            first["total_in_ccass_pct_of_issued"], "total_in_ccass_pct_of_issued"
        )
        issued_shares = _optional_non_negative_int(first["issued_shares"], "issued_shares")
        non_ccass_shares = _optional_non_negative_int(
            first["non_ccass_shares"], "non_ccass_shares"
        )
        non_ccass_pct = _optional_float(
            first["non_ccass_pct_of_issued"], "non_ccass_pct_of_issued"
        )
        holdings = tuple(sorted((_parse_holding(row) for row in rows), key=lambda row: row.rank))
    except (ValueError, KeyError) as exc:
        raise _data_source_error(f"CCASS CSV data for code {code} is invalid: {exc}") from exc

    ranks = [row.rank for row in holdings]
    if len(ranks) != len(set(ranks)):
        raise _data_source_error(f"CCASS CSV has duplicate ranks for code {code}.")
    participant_ids = [row.participant_id for row in holdings]
    if len(participant_ids) != len(set(participant_ids)):
        raise _data_source_error(f"CCASS CSV has duplicate participant IDs for code {code}.")

    return CsvStock(
        code=code,
        name=name,
        issue_id=issue_id,
        holdings_date=holdings_date,
        holdings=holdings,
        total_in_ccass_shares=total_in_ccass_shares,
        total_in_ccass_pct_of_issued=total_in_ccass_pct,
        issued_shares=issued_shares,
        non_ccass_shares=non_ccass_shares,
        non_ccass_pct_of_issued=non_ccass_pct,
    )


def _parse_holding(row: dict[str, str]) -> HoldingRow:
    shares = _non_negative_int(row["shares"], "shares")
    return HoldingRow(
        rank=_positive_int(row["rank"], "rank"),
        participant_id=_required(row, "participant_id"),
        participant=_required(row, "participant"),
        shares=shares,
        last_change=_optional_date(row["last_change"], "last_change"),
        pct_of_issued=_non_negative_float(row["pct_of_issued"], "pct_of_issued"),
        cumulative_pct_of_issued=_optional_float(
            row["cumulative_pct_of_issued"], "cumulative_pct_of_issued"
        ),
        participant_category=row["participant_category"] or None,
    )


def _required(row: dict[str, str], field: str) -> str:
    if not row[field]:
        raise ValueError(f"{field} is required")
    return row[field]


def _positive_int(value: str, field: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


def _non_negative_int(value: str, field: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{field} cannot be negative")
    return parsed


def _optional_non_negative_int(value: str, field: str) -> int | None:
    return _non_negative_int(value, field) if value else None


def _optional_float(value: str, field: str) -> float | None:
    return _non_negative_float(value, field) if value else None


def _non_negative_float(value: str, field: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return parsed


def _optional_date(value: str, field: str) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD") from exc


def _single_query_value(
    query: dict[str, list[str]], key: str, *, required: bool = True
) -> str | None:
    values = query.get(key, [])
    if len(values) == 1 and values[0]:
        return values[0]
    if required:
        raise _data_source_error(f"Google Drive URL is missing a valid {key} value.")
    return None


def _validate_google_id(value: str | None) -> str:
    if not value or not GOOGLE_ID_PATTERN.fullmatch(value):
        raise _data_source_error("Google Drive URL contains an invalid file ID.")
    return value


def _looks_like_html(content: bytes, content_type: str) -> bool:
    prefix = content[:4096].lstrip().lower()
    return (
        "text/html" in content_type
        or prefix.startswith(b"<!doctype html")
        or prefix.startswith(b"<html")
        or b"accounts.google.com" in prefix
        or b"servicelogin" in prefix
    )


def _data_source_error(message: str, *, retry_recommended: bool = False) -> PlatformError:
    return PlatformError(
        ErrorCode.DATA_SOURCE_ERROR,
        message,
        retry_recommended=retry_recommended,
        retry_after_seconds=30 if retry_recommended else None,
        status_code=502,
    )
