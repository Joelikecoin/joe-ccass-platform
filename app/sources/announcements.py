from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import AnnouncementRow, AnnouncementsMetadata, AnnouncementsResponse
from ccass_core.normalize import normalize_stock_code


HKEXNEWS_BASE_URL = "https://www1.hkexnews.hk"
HKEXNEWS_TITLE_SEARCH_URL = f"{HKEXNEWS_BASE_URL}/search/titlesearch.xhtml"
HKEXNEWS_TITLE_SEARCH_SERVLET_URL = f"{HKEXNEWS_BASE_URL}/search/titleSearchServlet.do"
HKEXNEWS_PREFIX_URL = f"{HKEXNEWS_BASE_URL}/search/prefix.do"
HKEXNEWS_SOURCE_NAME = "HKEXnews"
HKEXNEWS_MARKET = "SEHK"
HKEXNEWS_CATEGORY = "0"
HKEXNEWS_DOCUMENT_TYPE = "-1"
HKEXNEWS_SEARCH_TYPE = "0"
HKEXNEWS_TIER_DEFAULT = "-2"


@dataclass(frozen=True, slots=True)
class AnnouncementsRequest:
    code: str
    stock_id: int
    start_date: date
    end_date: date
    row_range: int


class HKEXNewsAnnouncementsSource:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._cache: dict[tuple[str, date, date], AnnouncementsResponse] = {}

    async def get_announcements(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        row_range: int = 10_000,
    ) -> AnnouncementsResponse:
        normalized = normalize_stock_code(code)
        request = self._normalize_request(
            normalized,
            start_date=start_date,
            end_date=end_date,
            row_range=row_range,
        )
        cache_key = (request.code, request.start_date, request.end_date, request.row_range)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached.model_copy(deep=True)

        stock_id = await self._resolve_stock_id(request.code)
        payload = await self._fetch_payload(request, stock_id=stock_id)
        response = self._build_response(request, stock_id=stock_id, payload=payload)
        self._cache[cache_key] = response.model_copy(deep=True)
        return response

    def _normalize_request(
        self,
        code: str,
        *,
        start_date: date | None,
        end_date: date | None,
        row_range: int,
    ) -> AnnouncementsRequest:
        today = date.today()
        end = end_date or today
        start = start_date or date(1999, 4, 1)
        if start > end:
            raise PlatformError(
                ErrorCode.INVALID_SCHEMA,
                "announcement start_date must be on or before end_date.",
                status_code=400,
            )
        if row_range < 1:
            raise PlatformError(
                ErrorCode.INVALID_SCHEMA,
                "announcement row_range must be positive.",
                status_code=400,
            )
        return AnnouncementsRequest(
            code=code,
            stock_id=-1,
            start_date=start,
            end_date=end,
            row_range=row_range,
        )

    async def _resolve_stock_id(self, code: str) -> int:
        for securities_type in ("A", "I"):
            payload = await self._fetch_stock_candidates(code, securities_type)
            candidates = payload.get("stockInfo") or []
            for candidate in candidates:
                candidate_code = normalize_stock_code(candidate.get("code") or "")
                if candidate_code == code:
                    stock_id = candidate.get("stockId")
                    if isinstance(stock_id, int) and stock_id > 0:
                        return stock_id
                    if isinstance(stock_id, str) and stock_id.isdigit():
                        return int(stock_id)
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            f"No verified HKEXnews stock identifier found for stock code {code}.",
            status_code=404,
        )

    async def _fetch_stock_candidates(self, code: str, securities_type: str) -> dict[str, Any]:
        params = {
            "lang": "EN",
            "type": securities_type,
            "name": code,
            "market": HKEXNEWS_MARKET,
            "callback": "callback",
        }
        headers = {"User-Agent": self.settings.user_agent}
        url = f"{HKEXNEWS_PREFIX_URL}?{urlencode(params)}"
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
                    response = await client.get(url)
                    self._last_request_at = time.monotonic()
            if response.status_code == 403:
                raise PlatformError(
                    ErrorCode.SOURCE_FORBIDDEN,
                    "HKEXnews rejected the announcement lookup request.",
                    retry_recommended=False,
                    status_code=503,
                )
            if response.status_code == 429:
                raise PlatformError(
                    ErrorCode.SOURCE_RATE_LIMITED,
                    "HKEXnews rate limited the announcement lookup request.",
                    retry_recommended=True,
                    retry_after_seconds=60,
                    status_code=503,
                )
            if response.status_code == 404:
                raise PlatformError(
                    ErrorCode.NOT_FOUND,
                    "HKEXnews could not resolve the requested stock code.",
                    status_code=404,
                )
            if response.status_code >= 500:
                raise PlatformError(
                    ErrorCode.SOURCE_UNAVAILABLE,
                    "HKEXnews announcement lookup is temporarily unavailable.",
                    retry_recommended=True,
                    status_code=503,
                )
            response.raise_for_status()
            text = response.text.strip()
        except httpx.TimeoutException as exc:
            raise PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                "HKEXnews announcement lookup timed out.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.NetworkError as exc:
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                f"HKEXnews announcement lookup network failure: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.HTTPError as exc:
            raise PlatformError(
                ErrorCode.DATA_SOURCE_ERROR,
                f"HKEXnews announcement lookup failed: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=502,
            ) from exc

        callback_match = re.fullmatch(r"callback\((.*)\);\s*", text, flags=re.S)
        if callback_match is None:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "HKEXnews announcement lookup returned unexpected content.",
                retry_recommended=True,
                status_code=502,
            )
        try:
            return json.loads(callback_match.group(1))
        except json.JSONDecodeError as exc:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "HKEXnews announcement lookup returned invalid JSON.",
                retry_recommended=True,
                status_code=502,
            ) from exc

    async def _fetch_payload(self, request: AnnouncementsRequest, *, stock_id: int) -> dict[str, Any]:
        params = {
            "sortDir": "0",
            "sortByOptions": "DateTime",
            "category": HKEXNEWS_CATEGORY,
            "market": HKEXNEWS_MARKET,
            "stockId": str(stock_id),
            "documentType": HKEXNEWS_DOCUMENT_TYPE,
            "fromDate": request.start_date.strftime("%Y%m%d"),
            "toDate": request.end_date.strftime("%Y%m%d"),
            "title": "",
            "searchType": HKEXNEWS_SEARCH_TYPE,
            "t1code": HKEXNEWS_TIER_DEFAULT,
            "t2Gcode": HKEXNEWS_TIER_DEFAULT,
            "t2code": HKEXNEWS_TIER_DEFAULT,
            "rowRange": str(request.row_range),
            "lang": "E",
        }
        headers = {
            "User-Agent": self.settings.user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
        url = f"{HKEXNEWS_TITLE_SEARCH_SERVLET_URL}?{urlencode(params)}"
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
                    response = await client.get(url)
                    self._last_request_at = time.monotonic()
            if response.status_code == 403:
                raise PlatformError(
                    ErrorCode.SOURCE_FORBIDDEN,
                    "HKEXnews rejected the announcement request.",
                    retry_recommended=False,
                    status_code=503,
                )
            if response.status_code == 429:
                raise PlatformError(
                    ErrorCode.SOURCE_RATE_LIMITED,
                    "HKEXnews rate limited the announcement request.",
                    retry_recommended=True,
                    retry_after_seconds=60,
                    status_code=503,
                )
            if response.status_code == 404:
                raise PlatformError(
                    ErrorCode.NOT_FOUND,
                    "HKEXnews returned no announcements for the requested stock code.",
                    status_code=404,
                )
            if response.status_code >= 500:
                raise PlatformError(
                    ErrorCode.SOURCE_UNAVAILABLE,
                    "HKEXnews announcements are temporarily unavailable.",
                    retry_recommended=True,
                    status_code=503,
                )
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                "HKEXnews announcement request timed out.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.NetworkError as exc:
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                f"HKEXnews announcement network failure: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.HTTPError as exc:
            raise PlatformError(
                ErrorCode.DATA_SOURCE_ERROR,
                f"HKEXnews announcement request failed: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=502,
            ) from exc
        except ValueError as exc:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "HKEXnews announcement request returned non-JSON content.",
                retry_recommended=True,
                status_code=502,
            ) from exc
        return payload

    def _build_response(
        self,
        request: AnnouncementsRequest,
        *,
        stock_id: int,
        payload: dict[str, Any],
    ) -> AnnouncementsResponse:
        raw_result = payload.get("result") or "[]"
        if not isinstance(raw_result, str):
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "HKEXnews announcement payload had an unexpected result format.",
                retry_recommended=True,
                status_code=502,
            )
        try:
            result_rows = json.loads(raw_result)
        except json.JSONDecodeError as exc:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "HKEXnews announcement payload contained invalid rows.",
                retry_recommended=True,
                status_code=502,
            ) from exc

        announcements: list[AnnouncementRow] = []
        warnings: list[str] = []
        for row in result_rows:
            if not isinstance(row, dict):
                continue
            announcement_date = self._parse_row_date(row.get("DATE_TIME"))
            title = str(row.get("TITLE") or row.get("LONG_TEXT") or "").strip()
            if announcement_date is None or not title:
                continue
            link = self._absolute_link(row.get("FILE_LINK") or row.get("DOD_WEB_PATH"))
            announcements.append(
                AnnouncementRow(
                    announcement_date=announcement_date,
                    title=title,
                    source=HKEXNEWS_SOURCE_NAME,
                    link=link,
                )
            )

        if payload.get("hasNextRow") and announcements:
            warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "HKEXNEWS_ANNOUNCEMENTS_TRUNCATED",
                    "HKEXnews returned additional announcement rows beyond the requested row range.",
                )
            )

        if announcements:
            announcements.sort(key=lambda item: (item.announcement_date, item.title), reverse=True)

        dates = [item.announcement_date for item in announcements]
        metadata = AnnouncementsMetadata(
            code=request.code,
            name=self._extract_stock_name(payload),
            source_name=HKEXNEWS_SOURCE_NAME,
            source_url=self._build_source_url(stock_id=stock_id, request=request),
            fetched_at=datetime.now(UTC),
            earliest_announcement_date=min(dates) if dates else None,
            latest_announcement_date=max(dates) if dates else None,
            announcement_count=len(announcements),
        )
        return AnnouncementsResponse(
            metadata=metadata,
            announcements=announcements,
            data_quality_warnings=list(dict.fromkeys(warnings)),
        )

    def _build_source_url(self, *, stock_id: int, request: AnnouncementsRequest) -> str:
        params = {
            "category": HKEXNEWS_CATEGORY,
            "lang": "EN",
            "market": HKEXNEWS_MARKET,
            "stockId": str(stock_id),
        }
        if request.start_date:
            params["from"] = request.start_date.strftime("%Y%m%d")
        if request.end_date:
            params["to"] = request.end_date.strftime("%Y%m%d")
        return f"{HKEXNEWS_TITLE_SEARCH_URL}?{urlencode(params)}"

    @staticmethod
    def _extract_stock_name(payload: dict[str, Any]) -> str | None:
        if not payload:
            return None
        result = payload.get("result")
        if not isinstance(result, str) or not result:
            return None
        try:
            rows = json.loads(result)
        except json.JSONDecodeError:
            return None
        if not rows:
            return None
        first = rows[0]
        if not isinstance(first, dict):
            return None
        stock_name = first.get("STOCK_NAME")
        if not isinstance(stock_name, str):
            return None
        return stock_name.split("<br/>", 1)[0].strip() or None

    @staticmethod
    def _parse_row_date(value: object | None) -> date | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return datetime.strptime(value.split(" ", 1)[0], "%d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _absolute_link(link: object | None) -> str | None:
        if not isinstance(link, str) or not link.strip():
            return None
        return urljoin(HKEXNEWS_BASE_URL, link)

