from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import PriceHistoryMetadata, PriceHistoryResponse, PriceHistoryRow
from ccass_core.normalize import normalize_stock_code
from app.sources.webbsite import WebbsiteClient


YAHOO_CHART_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
YAHOO_PRICE_SOURCE_NAME = "Yahoo Finance"
WEBBSITE_PRICE_SOURCE_NAME = "Webb-site"
WEBBSITE_PRICE_PATH = "/dbpub/hpu.asp"


def yahoo_hk_ticker(code: str | int) -> str:
    """Convert Joe's canonical HKEX code to Yahoo's four-digit HK symbol."""
    normalized = normalize_stock_code(code)
    digits = normalized.lstrip("0") or "0"
    return f"{digits.zfill(4)}.HK"


@dataclass(frozen=True, slots=True)
class PriceHistoryRequest:
    code: str
    start_date: date
    end_date: date


class YahooFinancePriceHistorySource:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._cache: dict[tuple[str, date, date], PriceHistoryResponse] = {}

    async def get_price_history(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PriceHistoryResponse:
        normalized = normalize_stock_code(code)
        request = self._normalize_request(normalized, start_date=start_date, end_date=end_date)
        cache_key = (request.code, request.start_date, request.end_date)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached.model_copy(deep=True)

        payload = await self._fetch_payload(request)
        response = self._build_response(request, payload)
        self._cache[cache_key] = response.model_copy(deep=True)
        return response

    def _normalize_request(
        self,
        code: str,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> PriceHistoryRequest:
        today = date.today()
        end = end_date or today
        start = start_date or (end - timedelta(days=90))
        if start > end:
            raise PlatformError(
                ErrorCode.INVALID_SCHEMA,
                "price history start_date must be on or before end_date.",
                status_code=400,
            )
        return PriceHistoryRequest(code=code, start_date=start, end_date=end)

    async def _fetch_payload(self, request: PriceHistoryRequest) -> dict[str, Any]:
        ticker = yahoo_hk_ticker(request.code)
        url = f"{YAHOO_CHART_BASE_URL}{ticker}"
        params = {
            "period1": int(datetime.combine(request.start_date, datetime.min.time(), tzinfo=UTC).timestamp()),
            "period2": int(
                datetime.combine(request.end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC).timestamp()
            ),
            "interval": "1d",
            "includeAdjustedClose": "true",
            "events": "div|split",
        }
        headers = {"User-Agent": self.settings.user_agent}
        try:
            async with self._request_lock:
                wait = self.settings.min_request_interval_seconds - (time.monotonic() - self._last_request_at)
                if wait > 0:
                    await asyncio.sleep(wait)
                async with httpx.AsyncClient(
                    timeout=self.settings.request_timeout_seconds,
                    follow_redirects=True,
                    headers=headers,
                ) as client:
                    response = await client.get(url, params=params)
                    self._last_request_at = time.monotonic()
            if response.status_code == 403:
                raise PlatformError(
                    ErrorCode.SOURCE_FORBIDDEN,
                    "Yahoo Finance rejected the price history request.",
                    retry_recommended=False,
                    status_code=503,
                )
            if response.status_code == 429:
                raise PlatformError(
                    ErrorCode.SOURCE_RATE_LIMITED,
                    "Yahoo Finance rate limited the price history request.",
                    retry_recommended=True,
                    retry_after_seconds=60,
                    status_code=503,
                )
            if response.status_code == 404:
                raise PlatformError(
                    ErrorCode.NOT_FOUND,
                    "Yahoo Finance returned no price history for the requested code.",
                    status_code=404,
                )
            if response.status_code >= 500:
                raise PlatformError(
                    ErrorCode.SOURCE_UNAVAILABLE,
                    "Yahoo Finance price history is temporarily unavailable.",
                    retry_recommended=True,
                    status_code=503,
                )
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                "Yahoo Finance price history request timed out.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.NetworkError as exc:
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                f"Yahoo Finance price history network failure: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.HTTPError as exc:
            raise PlatformError(
                ErrorCode.DATA_SOURCE_ERROR,
                f"Yahoo Finance price history request failed: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=502,
            ) from exc
        except ValueError as exc:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "Yahoo Finance returned non-JSON price history content.",
                retry_recommended=True,
                status_code=502,
            ) from exc
        return payload

    def _build_response(self, request: PriceHistoryRequest, payload: dict[str, Any]) -> PriceHistoryResponse:
        chart = payload.get("chart") or {}
        error = chart.get("error")
        if error:
            message = error.get("description") or error.get("code") or "Yahoo Finance reported a chart error."
            raise PlatformError(
                ErrorCode.DATA_SOURCE_ERROR,
                f"Yahoo Finance chart error: {message}",
                retry_recommended=True,
                status_code=502,
            )
        results = chart.get("result") or []
        if not results:
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                "Yahoo Finance returned no price history rows.",
                status_code=404,
            )
        result = results[0] or {}
        meta = result.get("meta") or {}
        timestamps = result.get("timestamp") or []
        indicators = result.get("indicators") or {}
        quote = (indicators.get("quote") or [{}])[0] or {}
        open_rows = quote.get("open") or []
        high_rows = quote.get("high") or []
        low_rows = quote.get("low") or []
        close_rows = quote.get("close") or []
        volume_rows = quote.get("volume") or []
        adjclose_rows = (indicators.get("adjclose") or [{}])[0].get("adjclose") or []

        rows: list[PriceHistoryRow] = []
        row_count = min(
            len(timestamps),
            len(open_rows),
            len(high_rows),
            len(low_rows),
            len(close_rows),
            len(volume_rows),
        )
        if adjclose_rows:
            row_count = min(row_count, len(adjclose_rows))
        warnings: list[str] = []
        if not row_count:
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                "Yahoo Finance returned empty price history rows.",
                status_code=404,
            )
        if len(timestamps) != len(open_rows):
            warnings.append(
                structured_warning(
                    "PRICE_HISTORY",
                    "MISMATCHED_ROW_LENGTHS",
                    "Yahoo Finance returned uneven price arrays; the shortest common length was used.",
                )
            )

        for index in range(row_count):
            price_date = datetime.fromtimestamp(timestamps[index], tz=UTC).date()
            open_value = _float_or_none(open_rows[index])
            high_value = _float_or_none(high_rows[index])
            low_value = _float_or_none(low_rows[index])
            close_value = _float_or_none(close_rows[index])
            volume_value = _int_or_none(volume_rows[index])
            adjusted_close = _float_or_none(adjclose_rows[index]) if index < len(adjclose_rows) else None
            turnover = round(close_value * volume_value, 2) if close_value is not None and volume_value is not None else None
            vwap = turnover / volume_value if turnover is not None and volume_value not in (None, 0) else None
            rows.append(
                PriceHistoryRow(
                    price_date=price_date,
                    open=open_value,
                    high=high_value,
                    low=low_value,
                    close=close_value,
                    vwap=vwap,
                    adjusted_close=adjusted_close,
                    volume=volume_value,
                    turnover=turnover,
                    price_source="yahoo",
                    turnover_est=turnover,
                    vwap_est=vwap,
                )
            )

        if not rows:
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                "Yahoo Finance returned no usable price history rows.",
                status_code=404,
            )

        source_name = YAHOO_PRICE_SOURCE_NAME
        source_ticker = str(meta.get("symbol") or yahoo_hk_ticker(request.code))
        adjustment_state = "adjusted" if adjclose_rows else "unadjusted"
        adjustment_note = (
            "Adjusted close values are available from Yahoo Finance."
            if adjclose_rows
            else "Adjusted close values were not returned by Yahoo Finance."
        )
        currency = meta.get("currency")
        metadata = PriceHistoryMetadata(
            code=request.code,
            name=meta.get("longName") or meta.get("shortName"),
            ticker=source_ticker,
            price_date_from=rows[0].price_date,
            price_date_to=rows[-1].price_date,
            source_name=source_name,
            source_url=f"{YAHOO_CHART_BASE_URL}{source_ticker}",
            fetched_at=datetime.now(UTC),
            adjustment_state=adjustment_state,
            currency=currency,
            adjustment_note=adjustment_note,
        )
        return PriceHistoryResponse(
            metadata=metadata,
            prices=rows,
            data_quality_warnings=warnings,
        )


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class WebbsitePriceHistorySource:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = WebbsiteClient(self.settings)
        self._cache: dict[tuple[str, date, date], PriceHistoryResponse] = {}

    async def get_price_history(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PriceHistoryResponse:
        normalized = normalize_stock_code(code)
        request = _normalize_price_history_request(normalized, start_date=start_date, end_date=end_date)
        cache_key = (request.code, request.start_date, request.end_date)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached.model_copy(deep=True)

        issue_id, company_name = await self.client.resolve_issue_id(request.code)
        page = await self.client.get_price_history_page(issue_id)
        response = _build_webbsite_price_history_response(
            request,
            html=page.html,
            source_url=page.source_url,
            issue_id=issue_id,
            company_name=company_name,
        )
        self._cache[cache_key] = response.model_copy(deep=True)
        return response


class PriceHistorySource:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.webbsite_source = WebbsitePriceHistorySource(self.settings)
        self.yahoo_source = YahooFinancePriceHistorySource(self.settings)
        self._cache: dict[tuple[str, date, date], PriceHistoryResponse] = {}

    async def get_price_history(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PriceHistoryResponse:
        normalized = normalize_stock_code(code)
        request = _normalize_price_history_request(normalized, start_date=start_date, end_date=end_date)
        cache_key = (request.code, request.start_date, request.end_date)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached.model_copy(deep=True)

        primary_failure: PlatformError | None = None
        try:
            response = await self.webbsite_source.get_price_history(
                request.code,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            self._cache[cache_key] = response.model_copy(deep=True)
            return response
        except PlatformError as exc:
            if exc.code == ErrorCode.INVALID_SCHEMA:
                raise
            primary_failure = exc

        try:
            response = await self.yahoo_source.get_price_history(
                request.code,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        except PlatformError as fallback_exc:
            if primary_failure is not None:
                raise PlatformError(
                    primary_failure.code,
                    (
                        f"Webb-site price history failed ({primary_failure.message}); "
                        f"Yahoo Finance fallback also failed ({fallback_exc.message})."
                    ),
                    retry_recommended=primary_failure.retry_recommended or fallback_exc.retry_recommended,
                    retry_after_seconds=primary_failure.retry_after_seconds
                    or fallback_exc.retry_after_seconds,
                    status_code=max(primary_failure.status_code, fallback_exc.status_code, 503),
                ) from fallback_exc
            raise

        if primary_failure is not None:
            response.data_quality_warnings = [
                structured_warning(
                    "PRICE_HISTORY",
                    "PRIMARY_SOURCE_FALLBACK",
                    (
                        "Webb-site price history was unavailable; "
                        "Yahoo Finance fallback was used."
                    ),
                ),
                *response.data_quality_warnings,
            ]

        self._cache[cache_key] = response.model_copy(deep=True)
        return response


def _normalize_price_history_request(
    code: str,
    *,
    start_date: date | None,
    end_date: date | None,
) -> PriceHistoryRequest:
    today = date.today()
    end = end_date or today
    start = start_date or (end - timedelta(days=90))
    if start > end:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            "price history start_date must be on or before end_date.",
            status_code=400,
        )
    return PriceHistoryRequest(code=code, start_date=start, end_date=end)


def _build_webbsite_price_history_response(
    request: PriceHistoryRequest,
    *,
    html: str,
    source_url: str,
    issue_id: int,
    company_name: str | None,
) -> PriceHistoryResponse:
    soup = BeautifulSoup(html, "html.parser")
    table = _find_price_history_table(soup)
    if table is None:
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            f"Webb-site returned no parseable price history table for stock code {request.code}.",
            status_code=404,
        )
    headers, rows = _extract_price_history_table(table)
    if not rows:
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            f"Webb-site returned no usable price history rows for stock code {request.code}.",
            status_code=404,
        )

    parsed_rows: list[PriceHistoryRow] = []
    warnings: list[str] = []
    for row in rows:
        parsed_rows.append(_build_price_history_row_from_mapping(row))

    parsed_rows = [row for row in parsed_rows if request.start_date <= row.price_date <= request.end_date]
    if not parsed_rows:
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            f"Webb-site returned no price history rows in the requested date range for stock code {request.code}.",
            status_code=404,
        )

    for row in parsed_rows:
        if row.turnover is None and row.close is not None and row.volume not in (None, 0):
            row.turnover = round(row.close * row.volume, 2)
            row.turnover_est = row.turnover
            warnings.append(
                structured_warning(
                    "PRICE_HISTORY",
                    "TURNOVER_ESTIMATED",
                    "Webb-site did not provide turnover for at least one row; turnover was estimated as close × volume.",
                )
            )
        if row.vwap is None and row.turnover is not None and row.volume not in (None, 0):
            row.vwap = round(row.turnover / row.volume, 4)
            row.vwap_est = row.vwap
            warnings.append(
                structured_warning(
                    "PRICE_HISTORY",
                    "VWAP_ESTIMATED",
                    "Webb-site did not provide VWAP for at least one row; VWAP was estimated from turnover ÷ volume.",
                )
            )
        if row.price_source is None:
            row.price_source = "webbsite"

    adjustment_state = "adjusted" if any(row.adjusted_close is not None for row in parsed_rows) else "unadjusted"
    adjustment_note = (
        "Webb-site price history fallback was used and adjusted prices were present."
        if adjustment_state == "adjusted"
        else "Webb-site price history fallback was used."
    )
    metadata = PriceHistoryMetadata(
        code=request.code,
        name=company_name,
        ticker=f"{request.code}.HK",
        price_date_from=parsed_rows[0].price_date,
        price_date_to=parsed_rows[-1].price_date,
        source_name=WEBBSITE_PRICE_SOURCE_NAME,
        source_url=source_url,
        fetched_at=datetime.now(UTC),
        adjustment_state=adjustment_state,
        currency=None,
        adjustment_note=adjustment_note,
    )
    return PriceHistoryResponse(
        metadata=metadata,
        prices=parsed_rows,
        data_quality_warnings=list(dict.fromkeys(warnings)),
    )


def _find_price_history_table(soup: BeautifulSoup):
    candidates = soup.find_all("table")
    for table in candidates:
        headers, rows = _extract_price_history_table(table)
        if rows and ({"date", "close", "volume"} & set(headers.values())):
            return table
        if rows and "date" in headers.values() and ("close" in headers.values() or "turnover" in headers.values()):
            return table
    return candidates[0] if len(candidates) == 1 else None


def _extract_price_history_table(table) -> tuple[dict[int, str], list[dict[str, str]]]:
    rows = table.find_all("tr")
    if not rows:
        return {}, []
    header_row = rows[0]
    header_cells = header_row.find_all(["th", "td"])
    data_rows = rows[1:]

    headers: dict[int, str] = {}
    for index, cell in enumerate(header_cells):
        label = _canonical_price_header(cell.get_text(" ", strip=True))
        if label:
            headers[index] = label

    rows: list[dict[str, str]] = []
    for tr in data_rows:
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue
        values = [cell.get_text(" ", strip=True) for cell in cells]
        if not any(value.strip() for value in values):
            continue
        row: dict[str, str] = {}
        for index, value in enumerate(values):
            field = headers.get(index)
            if field is not None:
                row[field] = value
        if row:
            rows.append(row)
    return headers, rows


def _canonical_price_header(value: str) -> str:
    return re.sub(r"[\W_]+", "", value).lower().strip()


def _build_price_history_row_from_mapping(mapping: dict[str, str]) -> PriceHistoryRow:
    price_date = _parse_price_date(
        mapping.get("date")
        or mapping.get("tradingdate")
        or mapping.get("pricedate")
        or mapping.get("交易日期")
        or mapping.get("日期")
        or ""
    )
    if price_date is None:
        raise PlatformError(
            ErrorCode.PARSE_ERROR,
            "Webb-site price history table did not contain a parseable date column.",
            status_code=502,
        )

    open_value = _float_or_none(mapping.get("open") or mapping.get("開") or mapping.get("開市"))
    high_value = _float_or_none(mapping.get("high") or mapping.get("最高"))
    low_value = _float_or_none(mapping.get("low") or mapping.get("最低"))
    close_value = _float_or_none(mapping.get("close") or mapping.get("收市") or mapping.get("收盤"))
    volume_value = _int_or_none(mapping.get("volume") or mapping.get("成交量") or mapping.get("股數"))
    turnover_value = _float_or_none(mapping.get("turnover") or mapping.get("成交額") or mapping.get("成交金額"))
    vwap_value = _float_or_none(mapping.get("vwap") or mapping.get("dailyvwap") or mapping.get("均價"))
    adjusted_close = _float_or_none(mapping.get("adjustedclose") or mapping.get("調整後收市"))

    turnover_est = None
    vwap_est = None
    if turnover_value is not None and volume_value not in (None, 0):
        vwap_est = round(turnover_value / volume_value, 4)
    elif close_value is not None and volume_value not in (None, 0):
        turnover_est = round(close_value * volume_value, 2)
        vwap_est = round(turnover_est / volume_value, 4)

    canonical_turnover = turnover_value if turnover_value is not None else turnover_est
    canonical_vwap = vwap_value if vwap_value is not None else vwap_est
    if canonical_turnover is None and close_value is not None and volume_value not in (None, 0):
        canonical_turnover = round(close_value * volume_value, 2)
    if canonical_vwap is None and canonical_turnover is not None and volume_value not in (None, 0):
        canonical_vwap = round(canonical_turnover / volume_value, 4)
    if vwap_value is None and canonical_vwap is not None and vwap_est is None:
        vwap_est = canonical_vwap

    return PriceHistoryRow(
        price_date=price_date,
        open=open_value,
        high=high_value,
        low=low_value,
        close=close_value,
        vwap=canonical_vwap,
        adjusted_close=adjusted_close,
        volume=volume_value,
        turnover=canonical_turnover,
        price_source="webbsite",
        turnover_est=turnover_est,
        vwap_est=vwap_est,
    )


def _parse_price_date(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    candidates = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y%m%d",
    )
    for fmt in candidates:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if match:
        year, month, day = map(int, match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None
