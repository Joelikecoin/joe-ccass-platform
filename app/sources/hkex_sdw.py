"""HKEX SDW CCASS holdings adapter."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
import re
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse, SourceMetadata
from app.services.request_context import REQUESTED_CCASS_SNAPSHOT_DATE
from app.sources.hkex_sdw_parser import ParsedHKEXSdwHoldings, parse_hkex_sdw_holdings
from app.sources.registry import (
    HKEX_SDW_SOURCE_ID,
    SourceCapability,
    SourceRegistry,
    build_source_registry,
)

HKEX_SDW_BASE_URL = "https://www3.hkexnews.hk"
HKEX_SDW_SEARCH_PATH = "/sdw/search/searchsdw_c.aspx"
_HK_TZ = ZoneInfo("Asia/Hong_Kong")
_ALLOWED_HTML_TYPES = frozenset({"text/html", "application/xhtml+xml"})


@dataclass(frozen=True, slots=True)
class FetchedPage:
    html: str
    source_url: str
    cached: bool


class HKEXSdwClient:
    """Fetch and normalize the official HKEX SDW shareholding search."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        registry: SourceRegistry | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.registry = registry or build_source_registry(self.settings)
        self.definition = self.registry.get(HKEX_SDW_SOURCE_ID)
        self._request_lock = asyncio.Lock()
        self._session_client: httpx.AsyncClient | None = None
        self._last_request_at = 0.0

    async def aclose(self) -> None:
        if self._session_client is not None:
            await self._session_client.aclose()
            self._session_client = None

    async def _get_session_client(self) -> httpx.AsyncClient:
        if self._session_client is None:
            self._session_client = httpx.AsyncClient(
                timeout=self.definition.policy.timeout_seconds,
                follow_redirects=True,
                cookies=httpx.Cookies(),
            )
        return self._session_client

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        self._ensure_latest_enabled()
        page = await self._fetch_holdings_page(code)
        parsed = parse_hkex_sdw_holdings(page.html, requested_code=code)
        return self._to_response(parsed, page=page, limit=limit)

    async def _fetch_holdings_page(self, code: str) -> FetchedPage:
        base_url = HKEX_SDW_BASE_URL
        landing_url = urljoin(base_url.rstrip("/") + "/", HKEX_SDW_SEARCH_PATH.lstrip("/"))
        landing_headers = self._browser_headers(base_url, referer=base_url.rstrip("/") + "/")
        search_date = self._current_hong_kong_date().strftime("%Y/%m/%d")

        async with self._request_lock:
            client = await self._get_session_client()
            await self._maybe_wait()
            try:
                landing_response = await self._request_html(
                    client,
                    "GET",
                    landing_url,
                    headers=landing_headers,
                    phase="landing",
                )
                requested_date = REQUESTED_CCASS_SNAPSHOT_DATE.get()
                if requested_date is not None and requested_date < self._current_hong_kong_date():
                    search_date = requested_date.strftime("%Y/%m/%d")
                else:
                    search_date = self._latest_available_search_date(landing_response.html)
                search_payload = self._build_search_payload(
                    landing_response.html, code, search_date
                )
                search_headers = self._browser_headers(
                    base_url,
                    referer=landing_response.source_url,
                )
                await self._maybe_wait()
                result_response = await self._request_html(
                    client,
                    "POST",
                    urljoin(landing_url, search_payload.pop("_action", HKEX_SDW_SEARCH_PATH)),
                    data=search_payload,
                    headers=search_headers,
                    phase="search",
                )
                return result_response
            except PlatformError as primary_error:
                browser_page = await self._fetch_holdings_page_via_browser(
                    base_url=base_url,
                    landing_url=landing_url,
                    code=code,
                    search_date=search_date,
                )
                if browser_page is not None:
                    return browser_page
                raise primary_error

    async def _request_html(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        *,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        phase: str,
    ) -> FetchedPage:
        try:
            response = await client.request(method, url, data=data, headers=headers)
        except httpx.TimeoutException as exc:
            raise self._platform_error(
                ErrorCode.SOURCE_TIMEOUT,
                phase=phase,
                request_url=url,
                retry_recommended=True,
                detail=f"timeout: {type(exc).__name__}",
            ) from exc
        except httpx.NetworkError as exc:
            raise self._platform_error(
                ErrorCode.SOURCE_UNAVAILABLE,
                phase=phase,
                request_url=url,
                retry_recommended=True,
                detail=f"network error: {type(exc).__name__}: {exc}",
            ) from exc

        self._last_request_at = time.monotonic()
        content_type = response.headers.get("content-type")
        redirect_target = self._redirect_target(response, url)
        status_error = self._status_error(response.status_code)
        if status_error is not None:
            raise self._platform_error(
                status_error[0],
                phase=phase,
                request_url=url,
                status_code=response.status_code,
                content_type=content_type,
                redirect_target=redirect_target,
                retry_recommended=status_error[1],
                detail=self._status_detail(response.status_code),
            )

        if content_type is not None:
            media_type = content_type.split(";", 1)[0].strip().lower()
            if media_type and media_type not in _ALLOWED_HTML_TYPES:
                raise self._platform_error(
                    ErrorCode.SOURCE_CHANGED,
                    phase=phase,
                    request_url=url,
                    status_code=response.status_code,
                    content_type=content_type,
                    redirect_target=redirect_target,
                    detail="unexpected content type",
                )

        html = response.text or ""
        if not html.strip():
            raise self._platform_error(
                ErrorCode.SOURCE_CHANGED,
                phase=phase,
                request_url=url,
                status_code=response.status_code,
                content_type=content_type,
                redirect_target=redirect_target,
                detail="empty body",
            )
        if len(response.content) > self.definition.policy.max_bytes:
            raise self._platform_error(
                ErrorCode.TOO_LARGE,
                phase=phase,
                request_url=url,
                status_code=response.status_code,
                content_type=content_type,
                redirect_target=redirect_target,
                detail=f"actual_size>{self.definition.policy.max_bytes}",
            )

        body_failure = self._body_failure_type(html)
        if body_failure is not None:
            raise self._platform_error(
                ErrorCode.AUTH_FAILED if body_failure in {"cloudflare_challenge", "login_page"} else ErrorCode.SOURCE_CHANGED,
                phase=phase,
                request_url=url,
                status_code=response.status_code,
                content_type=content_type,
                redirect_target=redirect_target,
                detail=self._body_failure_detail(html),
            )

        return FetchedPage(html=html, source_url=str(response.url), cached=False)

    @staticmethod
    def _load_playwright_async_api():
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return None
        return async_playwright

    async def _fetch_holdings_page_via_browser(
        self,
        *,
        base_url: str,
        landing_url: str,
        code: str,
        search_date: str,
    ) -> FetchedPage | None:
        async_playwright = self._load_playwright_async_api()
        if async_playwright is None:
            return None

        browser = None
        context = None
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.settings.user_agent,
                    extra_http_headers=self._browser_headers(base_url),
                )
                page = await context.new_page()
                await page.goto(landing_url, wait_until="domcontentloaded")
                date_input = page.locator("#txtShareholdingDate")
                try:
                    await date_input.evaluate(
                        """(element, value) => {
                            element.removeAttribute('readonly');
                            element.value = value;
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                        }""",
                        search_date,
                    )
                except Exception:
                    pass
                await page.locator("#txtStockCode").fill(code)
                try:
                    await page.locator("#btnSearch").click()
                except Exception:
                    await page.locator("form").evaluate("form => form.requestSubmit()")
                try:
                    await page.wait_for_load_state("networkidle")
                except Exception:
                    pass
                html = await page.content()
                if not html.strip():
                    return None
                return FetchedPage(html=html, source_url=page.url or landing_url, cached=False)
        except Exception:
            return None
        finally:
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    pass

    def _build_search_payload(self, html: str, code: str, search_date: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form")
        payload: dict[str, str] = {}
        if form is not None:
            action = str(form.get("action") or "").strip()
            if action:
                payload["_action"] = action
            for node in form.select("input[name]"):
                name = str(node.get("name") or "").strip()
                if not name:
                    continue
                payload[name] = str(node.get("value") or "")
            for node in form.select("textarea[name]"):
                name = str(node.get("name") or "").strip()
                if not name:
                    continue
                payload[name] = node.get_text(" ", strip=True)

        payload["txtShareholdingDate"] = search_date
        payload["txtStockCode"] = code
        payload.setdefault("txtParticipantID", "")
        payload.setdefault("txtParticipantName", "")
        if not payload.get("btnSearch"):
            payload["btnSearch"] = "Search"
        payload.setdefault("__EVENTTARGET", "")
        payload.setdefault("__EVENTARGUMENT", "")
        return payload

    def _to_response(
        self,
        parsed: ParsedHKEXSdwHoldings,
        *,
        page: FetchedPage,
        limit: int,
    ) -> CcassResponse:
        warnings = list(parsed.warnings)
        warnings.extend(
            f"SOURCE_LIMITATION: {limitation}"
            for limitation in self.definition.audit.known_limitations
        )
        return CcassResponse(
            metadata=SourceMetadata(
                code=parsed.code,
                name=parsed.name,
                issue_id=parsed.issue_id,
                holdings_date=parsed.holdings_date,
                fetched_at=datetime.now(UTC),
                source_url=page.source_url,
                source_name=self.definition.display_name,
                cached=page.cached,
                attribution=self.definition.audit.attribution,
            ),
            holdings_summary=parsed.holdings_summary,
            holdings=list(parsed.holdings[: max(1, limit)]),
            data_quality_warnings=warnings,
        )

    def _ensure_latest_enabled(self) -> None:
        if not self.definition.supports(SourceCapability.LATEST):
            raise PlatformError(
                ErrorCode.SOURCE_DISABLED,
                "The HKEX SDW latest Holdings source is disabled or unverified.",
                status_code=503,
            )

    async def _maybe_wait(self) -> None:
        wait = self.definition.policy.minimum_interval_seconds - (
            time.monotonic() - self._last_request_at
        )
        if wait > 0:
            await asyncio.sleep(wait)

    def _platform_error(
        self,
        code: ErrorCode,
        *,
        phase: str,
        request_url: str,
        status_code: int | None = None,
        content_type: str | None = None,
        redirect_target: str | None = None,
        retry_recommended: bool = False,
        detail: str | None = None,
    ) -> PlatformError:
        message = self._failure_message(
            phase=phase,
            request_url=request_url,
            status_code=status_code,
            content_type=content_type,
            redirect_target=redirect_target,
            detail=detail,
        )
        return PlatformError(
            code,
            message,
            retry_recommended=retry_recommended,
            status_code=status_code or 502,
        )

    @staticmethod
    def _failure_message(
        *,
        phase: str,
        request_url: str,
        status_code: int | None,
        content_type: str | None,
        redirect_target: str | None,
        detail: str | None,
    ) -> str:
        bits = [
            f"HKEX SDW holdings request failed during {phase} phase.",
            f"url={request_url}",
        ]
        if status_code is not None:
            bits.append(f"status={status_code}")
        if content_type:
            bits.append(f"content_type={content_type}")
        if redirect_target:
            bits.append(f"redirect_target={redirect_target}")
        if detail:
            bits.append(f"detail={detail}")
        return " ".join(bits)

    @staticmethod
    def _status_error(status_code: int) -> tuple[ErrorCode, bool] | None:
        if status_code == 403:
            return ErrorCode.SOURCE_FORBIDDEN, False
        if status_code == 429:
            return ErrorCode.SOURCE_RATE_LIMITED, True
        if 500 <= status_code <= 599:
            return ErrorCode.SOURCE_UNAVAILABLE, True
        return None

    @staticmethod
    def _status_detail(status_code: int) -> str | None:
        if status_code == 403:
            return "HTTP 403 forbidden"
        if status_code == 429:
            return "HTTP 429 rate limited"
        if 500 <= status_code <= 599:
            return f"HTTP {status_code} server error"
        return None

    @staticmethod
    def _body_failure_type(html: str) -> str | None:
        lowered = html.lower()
        if "cf-chl-" in lowered or "just a moment..." in lowered or "captcha" in lowered:
            return "cloudflare_challenge"
        if (
            'type="password"' in lowered
            or 'name="login"' in lowered
            or "<title>sign in" in lowered
            or "<title>login" in lowered
            or "access denied" in lowered
        ):
            return "login_page"
        if "<html" not in lowered or "</html>" not in lowered:
            return "incomplete_body"
        return None

    @staticmethod
    def _body_failure_detail(html: str) -> str | None:
        lowered = html.lower()
        if "cf-chl-" in lowered or "just a moment..." in lowered or "captcha" in lowered:
            return "cloudflare challenge detected"
        if (
            'type="password"' in lowered
            or 'name="login"' in lowered
            or "<title>sign in" in lowered
            or "<title>login" in lowered
            or "access denied" in lowered
        ):
            return "login or access-denied page detected"
        if "<html" not in lowered or "</html>" not in lowered:
            return "incomplete HTML document"
        return None

    @staticmethod
    def _redirect_target(response: httpx.Response, request_url: str) -> str | None:
        response_url = str(response.url)
        request_base_url = str(getattr(response.request, "url", request_url))
        if response_url != request_base_url:
            return response_url
        history = getattr(response, "history", None) or ()
        if history:
            first_redirect = str(history[0].headers.get("location") or "").strip()
            return first_redirect or None
        return None

    def _browser_headers(self, base_url: str, *, referer: str | None = None) -> dict[str, str]:
        return {
            "User-Agent": self.settings.user_agent,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "en-GB,en;q=0.9,zh-HK;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "no-cache",
            "DNT": "1",
            "Pragma": "no-cache",
            "Origin": base_url.rstrip("/"),
            "Referer": referer or base_url.rstrip("/") + "/",
            "Sec-CH-UA": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i",
            "Upgrade-Insecure-Requests": "1",
        }

    @staticmethod
    def _latest_available_search_date(landing_html: str) -> str:
        """Use HKEX's own visible landing-page limit for the first search date.

        The SDW landing page exposes the latest allowed date via both the
        shareholding input's `data-reset` attribute and an inline `MAX` value.
        Using that value keeps the request aligned with the current official
        form contract instead of assuming "today" is still queryable.
        """

        soup = BeautifulSoup(landing_html or "", "html.parser")
        date_input = soup.find(id="txtShareholdingDate")
        if date_input is not None:
            data_reset = str(date_input.get("data-reset") or "").strip()
            if re.fullmatch(r"\d{4}/\d{2}/\d{2}", data_reset):
                return data_reset
        match = re.search(r"MAX:\s*new Date\(['\"](\d{4}/\d{2}/\d{2})['\"]\)", landing_html or "")
        if match:
            return match.group(1)
        return HKEXSdwClient._current_hong_kong_date().strftime("%Y/%m/%d")

    @staticmethod
    def _current_hong_kong_date() -> date:
        return datetime.now(UTC).astimezone(_HK_TZ).date()
