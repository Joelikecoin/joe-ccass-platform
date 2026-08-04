from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import PriceHistoryMetadata, PriceHistoryResponse, PriceHistoryRow
from ccass_core.normalize import normalize_stock_code


YAHOO_CHART_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
YAHOO_PRICE_SOURCE_NAME = "Yahoo Finance"


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
        ticker = f"{request.code}.HK"
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
            rows.append(
                PriceHistoryRow(
                    price_date=price_date,
                    open=open_value,
                    high=high_value,
                    low=low_value,
                    close=close_value,
                    adjusted_close=adjusted_close,
                    volume=volume_value,
                    turnover=turnover,
                )
            )

        if not rows:
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                "Yahoo Finance returned no usable price history rows.",
                status_code=404,
            )

        source_name = YAHOO_PRICE_SOURCE_NAME
        source_ticker = str(meta.get("symbol") or f"{request.code}.HK")
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
