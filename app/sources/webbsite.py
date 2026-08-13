import asyncio
import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse, SourceMetadata
from app.sources.registry import (
    WEBBSITE_SOURCE_ID,
    SourceCapability,
    SourceRegistry,
    build_source_registry,
)
from app.sources.webbsite_parser import ParsedWebbsiteHoldings, parse_webbsite_holdings

logger = logging.getLogger(__name__)

_ALLOWED_HTML_TYPES = frozenset({"text/html", "application/xhtml+xml"})
_SOURCE_CHANGED_FAILURES = frozenset(
    {
        "empty_body",
        "error_page",
        "incomplete_body",
        "invalid_content_length",
        "invalid_content_type",
    }
)


@dataclass(slots=True)
class CachedPage:
    html: str
    source_url: str
    stored_at: float


@dataclass(frozen=True, slots=True)
class FetchedPage:
    html: str
    source_url: str
    cached: bool


@dataclass(frozen=True, slots=True)
class MirrorFailure:
    hostname: str
    request_url: str
    status_code: int | None
    error_type: str
    content_type: str | None = None
    redirect_target: str | None = None
    failure_detail: str | None = None


@dataclass(frozen=True, slots=True)
class _GuardedHtml:
    html: str
    failure_type: str | None
    failure_detail: str | None = None
    content_type: str | None = None
    redirect_target: str | None = None


class WebbsiteClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        registry: SourceRegistry | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.registry = registry or build_source_registry(self.settings)
        self.definition = self.registry.get(WEBBSITE_SOURCE_ID)
        self._cache: dict[str, CachedPage] = {}
        self._last_request_at = 0.0
        self._request_lock = asyncio.Lock()
        self._session_client: httpx.AsyncClient | None = None

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

    async def _fetch(self, path: str, params: dict[str, str | int]) -> FetchedPage:
        self._ensure_latest_enabled()
        failures: list[MirrorFailure] = []
        base_urls = tuple(
            dict.fromkeys(
                (
                    self.settings.webbsite_base_url,
                    self.settings.webbsite_fallback_base_url,
                )
            )
        )
        for _attempt in range(self.definition.policy.retry_attempts):
            for base_url in base_urls:
                page = await self._fetch_from_mirror(
                    base_url,
                    path=path,
                    params=params,
                    failures=failures,
                )
                if page is not None:
                    return page
        raise self._platform_error_for(failures)

    async def _fetch_from_mirror(
        self,
        base_url: str,
        *,
        path: str,
        params: dict[str, str | int],
        failures: list[MirrorFailure],
    ) -> FetchedPage | None:
        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        hostname = urlsplit(url).hostname or "unknown"
        cache_key = str(httpx.URL(url, params=params))
        cached = self._cache.get(cache_key)
        now = time.monotonic()
        if (
            cached
            and now - cached.stored_at < self.definition.policy.cache_ttl_seconds
        ):
            return FetchedPage(cached.html, cached.source_url, True)

        try:
            async with self._request_lock:
                wait = self.definition.policy.minimum_interval_seconds - (
                    time.monotonic() - self._last_request_at
                )
                if wait > 0:
                    await asyncio.sleep(wait)
                client = await self._get_session_client()
                async with client.stream(
                    "GET",
                    url,
                    params=params,
                    headers=self._browser_headers(base_url),
                ) as response:
                    self._last_request_at = time.monotonic()
                    failure_type = self._status_failure_type(response.status_code)
                    if failure_type is not None:
                        self._record_failure(
                            failures,
                            hostname=hostname,
                            request_url=url,
                            status_code=response.status_code,
                            error_type=failure_type,
                            content_type=response.headers.get("content-type"),
                            redirect_target=self._redirect_target(response, url),
                            failure_detail=self._status_failure_detail(response.status_code),
                        )
                        return None
                    response.raise_for_status()
                    guarded = await self._read_guarded_html(response, request_url=url)

            if guarded.failure_type is not None:
                self._record_failure(
                    failures,
                    hostname=hostname,
                    request_url=url,
                    status_code=response.status_code,
                    error_type=guarded.failure_type,
                    content_type=guarded.content_type,
                    redirect_target=guarded.redirect_target,
                    failure_detail=guarded.failure_detail,
                )
                return None

            source_url = str(response.url)
            self._cache[cache_key] = CachedPage(
                guarded.html,
                source_url,
                time.monotonic(),
            )
            return FetchedPage(guarded.html, source_url, False)
        except httpx.TimeoutException:
            self._record_failure(
                failures,
                hostname=hostname,
                request_url=url,
                status_code=None,
                error_type="timeout",
            )
        except httpx.NetworkError as exc:
            self._record_failure(
                failures,
                hostname=hostname,
                request_url=url,
                status_code=None,
                error_type=type(exc).__name__,
                failure_detail=str(exc),
            )
        except httpx.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if isinstance(exc, httpx.HTTPStatusError)
                else None
            )
            self._record_failure(
                failures,
                hostname=hostname,
                request_url=url,
                status_code=status_code,
                error_type=type(exc).__name__,
                failure_detail=str(exc),
            )
        return None

    async def _read_guarded_html(
        self,
        response: httpx.Response,
        *,
        request_url: str,
    ) -> _GuardedHtml:
        content_type = response.headers.get("content-type", "")
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type not in _ALLOWED_HTML_TYPES:
            return _GuardedHtml(
                "",
                "invalid_content_type",
                failure_detail=f"content-type={content_type or 'missing'}",
                content_type=content_type or None,
                redirect_target=self._redirect_target(response, request_url),
            )

        content_length = response.headers.get("content-length")
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError:
                return _GuardedHtml(
                    "",
                    "invalid_content_length",
                    failure_detail=f"content-length={content_length}",
                    content_type=content_type or None,
                    redirect_target=self._redirect_target(response, request_url),
                )
            if declared_size < 0:
                return _GuardedHtml(
                    "",
                    "invalid_content_length",
                    failure_detail=f"content-length={content_length}",
                    content_type=content_type or None,
                    redirect_target=self._redirect_target(response, request_url),
                )
            if declared_size > self.definition.policy.max_bytes:
                return _GuardedHtml(
                    "",
                    "too_large",
                    failure_detail=(
                        f"declared_size={declared_size}, max_bytes={self.definition.policy.max_bytes}"
                    ),
                    content_type=content_type or None,
                    redirect_target=self._redirect_target(response, request_url),
                )

        chunks: list[bytes] = []
        actual_size = 0
        async for chunk in response.aiter_bytes():
            actual_size += len(chunk)
            if actual_size > self.definition.policy.max_bytes:
                return _GuardedHtml(
                    "",
                    "too_large",
                    failure_detail=f"actual_size>{self.definition.policy.max_bytes}",
                    content_type=content_type or None,
                    redirect_target=self._redirect_target(response, request_url),
                )
            chunks.append(chunk)

        if actual_size == 0:
            return _GuardedHtml(
                "",
                "empty_body",
                failure_detail="empty body",
                content_type=content_type or None,
                redirect_target=self._redirect_target(response, request_url),
            )
        encoding = response.encoding or "utf-8"
        html = b"".join(chunks).decode(encoding, errors="replace")
        return _GuardedHtml(
            html,
            self._body_failure_type(html),
            failure_detail=self._body_failure_detail(html),
            content_type=content_type or None,
            redirect_target=self._redirect_target(response, request_url),
        )

    def _ensure_latest_enabled(self) -> None:
        if not self.definition.supports(SourceCapability.LATEST):
            raise PlatformError(
                ErrorCode.SOURCE_DISABLED,
                "The Webb-site latest Holdings source is disabled or unverified.",
                status_code=503,
            )

    @staticmethod
    def _status_failure_type(status_code: int) -> str | None:
        if status_code == 403:
            return "forbidden"
        if status_code == 429:
            return "rate_limited"
        if 500 <= status_code <= 599:
            return "server_error"
        return None

    @staticmethod
    def _body_failure_type(html: str) -> str | None:
        lowered = html.lower()
        if not html.strip():
            return "empty_body"
        if (
            "cf-chl-" in lowered
            or "just a moment..." in lowered
            or "captcha" in lowered
        ):
            return "cloudflare_challenge"
        if (
            'type="password"' in lowered
            or 'name="login"' in lowered
            or "<title>sign in" in lowered
            or "<title>login" in lowered
        ):
            return "login_page"
        if "<title>error" in lowered or "internal server error" in lowered:
            return "error_page"
        if "<html" not in lowered or "</html>" not in lowered:
            return "incomplete_body"
        return None

    @staticmethod
    def _body_failure_detail(html: str) -> str | None:
        lowered = html.lower()
        if not html.strip():
            return "empty body"
        if (
            "cf-chl-" in lowered
            or "just a moment..." in lowered
            or "captcha" in lowered
        ):
            return "cloudflare challenge detected"
        if (
            'type="password"' in lowered
            or 'name="login"' in lowered
            or "<title>sign in" in lowered
            or "<title>login" in lowered
        ):
            return "login page detected"
        if "<title>error" in lowered or "internal server error" in lowered:
            return "error page detected"
        if "<html" not in lowered or "</html>" not in lowered:
            return "incomplete HTML document"
        return None

    @staticmethod
    def _status_failure_detail(status_code: int) -> str | None:
        if status_code == 403:
            return "HTTP 403 forbidden"
        if status_code == 429:
            return "HTTP 429 rate limited"
        if 500 <= status_code <= 599:
            return f"HTTP {status_code} server error"
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

    def _browser_headers(self, base_url: str) -> dict[str, str]:
        """Return navigation headers without API credentials or other secrets."""
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
            "Referer": base_url.rstrip("/") + "/",
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
    def _record_failure(
        failures: list[MirrorFailure],
        *,
        hostname: str,
        request_url: str,
        status_code: int | None,
        error_type: str,
        content_type: str | None = None,
        redirect_target: str | None = None,
        failure_detail: str | None = None,
    ) -> None:
        failures.append(
            MirrorFailure(
                hostname=hostname,
                request_url=request_url,
                status_code=status_code,
                error_type=error_type,
                content_type=content_type,
                redirect_target=redirect_target,
                failure_detail=failure_detail,
            )
        )
        logger.warning(
            (
                "Webb-site mirror failed hostname=%s status_code=%s error_type=%s "
                "request_url=%s content_type=%s redirect_target=%s failure_detail=%s"
            ),
            hostname,
            status_code if status_code is not None else "none",
            error_type,
            request_url,
            content_type or "none",
            redirect_target or "none",
            failure_detail or "none",
        )

    @staticmethod
    def _failure_summary(failures: list[MirrorFailure]) -> str:
        details: list[str] = []
        for failure in failures[:4]:
            parts = [f"{failure.hostname}:{failure.error_type}"]
            if failure.status_code is not None:
                parts.append(f"status={failure.status_code}")
            if failure.content_type:
                parts.append(f"content_type={failure.content_type}")
            if failure.redirect_target:
                parts.append(f"redirect={failure.redirect_target}")
            if failure.failure_detail:
                parts.append(f"detail={failure.failure_detail}")
            parts.append(f"url={failure.request_url}")
            details.append("[" + ", ".join(parts) + "]")
        if len(failures) > 4:
            details.append(f"... +{len(failures) - 4} more")
        return "; ".join(details) if details else "no upstream failures captured"

    @classmethod
    def _platform_error_for(cls, failures: list[MirrorFailure]) -> PlatformError:
        error_types = {failure.error_type for failure in failures}
        summary = cls._failure_summary(failures)
        if failures and error_types == {"timeout"}:
            return PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                f"All configured Webb-site mirror requests timed out. {summary}",
                retry_recommended=True,
                retry_after_seconds=30,
                status_code=504,
            )
        if "rate_limited" in error_types:
            return PlatformError(
                ErrorCode.SOURCE_RATE_LIMITED,
                f"A Webb-site mirror rate limit prevented the request. {summary}",
                retry_recommended=True,
                retry_after_seconds=60,
                status_code=503,
            )
        if error_types & {"forbidden", "cloudflare_challenge", "login_page"}:
            return PlatformError(
                ErrorCode.SOURCE_FORBIDDEN,
                f"Webb-site mirrors refused, challenged, or required login for the request. {summary}",
                status_code=502,
            )
        if "too_large" in error_types:
            return PlatformError(
                ErrorCode.TOO_LARGE,
                f"Webb-site mirror responses exceeded the configured safety limit. {summary}",
            )
        if error_types & _SOURCE_CHANGED_FAILURES:
            return PlatformError(
                ErrorCode.SOURCE_CHANGED,
                f"Webb-site mirrors returned an invalid or unexpected HTML page. {summary}",
            )
        return PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            f"Webb-site mirrors were unavailable. {summary}",
            retry_recommended=True,
            retry_after_seconds=30,
            status_code=502,
        )

    async def resolve_issue_id(self, code: str) -> tuple[int, str | None]:
        """Compatibility lookup; latest Holdings uses the guarded one-request route."""
        page = await self._fetch(
            "/dbpub/orgdata.asp",
            {"code": code.lstrip("0") or "0", "Submit": "current"},
        )
        soup = BeautifulSoup(page.html, "html.parser")
        candidates: list[tuple[int, str | None]] = []
        code_node = soup.find(string=lambda value: bool(value and value.strip() == code))
        if code_node:
            security_table = code_node.find_parent("table")
            if security_table:
                for sibling in security_table.next_siblings:
                    sibling_name = getattr(sibling, "name", None)
                    if sibling_name in {"h3", "h4", "table"}:
                        break
                    if not hasattr(sibling, "select_one"):
                        continue
                    link = sibling.select_one(
                        'a[href*="/ccass/choldings.asp?i="], '
                        'a[href*="ccass/choldings.asp?i="]'
                    )
                    if not link:
                        continue
                    match = re.search(r"[?&]i=(\d+)", link.get("href", ""))
                    if match and int(match.group(1)) > 0:
                        heading = soup.find("h2")
                        candidates.append(
                            (
                                int(match.group(1)),
                                heading.get_text(" ", strip=True) if heading else None,
                            )
                        )
                        break
        if not candidates:
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                f"No verified Webb-site issue ID found for stock code {code}.",
                status_code=404,
            )
        unique_ids = {item[0] for item in candidates}
        if len(unique_ids) != 1:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                f"Stock code {code} resolved to multiple issue IDs; "
                "manual verification is required.",
            )
        return candidates[0]

    async def get_stock_events_page(self, issue_id: int) -> FetchedPage:
        return await self._fetch("/dbpub/events.asp", {"i": issue_id})

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        # The stock-code route resolves and verifies the issue in one upstream response.
        page = await self._fetch(
            "/ccass/choldings.asp",
            {"sc": code.lstrip("0") or "0"},
        )
        parsed = parse_webbsite_holdings(page.html, requested_code=code)
        return self._to_response(parsed, page=page, limit=limit)

    def _to_response(
        self,
        parsed: ParsedWebbsiteHoldings,
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

    @staticmethod
    def _resolve_holdings_identity(html: str, code: str) -> tuple[int, str | None]:
        """Compatibility identity guard retained for existing internal callers."""
        soup = BeautifulSoup(html, "html.parser")
        code_node = soup.find(string=lambda value: bool(value and value.strip() == code))
        issue_input = soup.select_one('input[name="i"][value]')
        issue_value = issue_input.get("value", "") if issue_input else ""
        if (
            code_node is None
            or not re.fullmatch(r"[1-9]\d*", str(issue_value).strip())
        ):
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                f"No verified Webb-site Holdings page found for stock code {code}.",
                status_code=404,
            )
        heading = soup.find("h2")
        name = heading.get_text(" ", strip=True) if heading else None
        return int(issue_value), name
