import asyncio
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.core.normalizers import (
    classify_participant,
    parse_float,
    parse_int,
    parse_iso_date,
)
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata


@dataclass(slots=True)
class CachedPage:
    html: str
    stored_at: float


class WebbsiteClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._cache: dict[str, CachedPage] = {}
        self._last_request_at = 0.0
        self._request_lock = asyncio.Lock()

    async def _fetch(self, path: str, params: dict[str, str | int]) -> tuple[str, str, bool]:
        last_error: Exception | None = None
        for base_url in (
            self.settings.webbsite_base_url,
            self.settings.webbsite_fallback_base_url,
        ):
            url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
            cache_key = str(httpx.URL(url, params=params))
            cached = self._cache.get(cache_key)
            now = time.monotonic()
            if cached and now - cached.stored_at < self.settings.cache_ttl_seconds:
                return cached.html, cache_key, True

            try:
                async with self._request_lock:
                    wait = self.settings.min_request_interval_seconds - (
                        time.monotonic() - self._last_request_at
                    )
                    if wait > 0:
                        await asyncio.sleep(wait)
                    async with httpx.AsyncClient(
                        timeout=self.settings.request_timeout_seconds,
                        follow_redirects=True,
                        headers={"User-Agent": self.settings.user_agent},
                    ) as client:
                        response = await client.get(url, params=params)
                    self._last_request_at = time.monotonic()
                response.raise_for_status()
                if "cf-chl-" in response.text or "Just a moment..." in response.text:
                    last_error = RuntimeError("Cloudflare challenge page")
                    continue
                if len(response.content) > 5_000_000:
                    raise PlatformError(
                        ErrorCode.TOO_LARGE,
                        "Upstream response exceeded the 5 MB safety limit.",
                    )
                self._cache[cache_key] = CachedPage(response.text, time.monotonic())
                return response.text, str(response.url), False
            except PlatformError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                continue
            except httpx.HTTPError as exc:
                last_error = exc
                continue

        raise PlatformError(
            ErrorCode.SOURCE_TIMEOUT,
            f"Both Webb-site mirror sources failed: {type(last_error).__name__}",
            retry_recommended=True,
            retry_after_seconds=30,
        )

    async def resolve_issue_id(self, code: str) -> tuple[int, str | None]:
        html, _, _ = await self._fetch(
            "/dbpub/orgdata.asp", {"code": code.lstrip("0") or "0", "Submit": "current"}
        )
        soup = BeautifulSoup(html, "html.parser")
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
                        'a[href*="/ccass/choldings.asp?i="], a[href*="ccass/choldings.asp?i="]'
                    )
                    if not link:
                        continue
                    match = re.search(r"[?&]i=(\d+)", link.get("href", ""))
                    if match:
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
                f"Stock code {code} resolved to multiple issue IDs; manual verification is required.",
            )
        return candidates[0]

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        issue_id, resolved_name = await self.resolve_issue_id(code)
        html, source_url, cached = await self._fetch("/ccass/choldings.asp", {"i": issue_id})
        return self.parse_holdings(
            html,
            code=code,
            issue_id=issue_id,
            source_url=source_url,
            resolved_name=resolved_name,
            limit=limit,
            cached=cached,
        )

    @staticmethod
    def parse_holdings(
        html: str,
        *,
        code: str,
        issue_id: int,
        source_url: str,
        resolved_name: str | None = None,
        limit: int = 15,
        cached: bool = False,
    ) -> CcassResponse:
        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.find("h2")
        name = page_title.get_text(" ", strip=True) if page_title else resolved_name
        date_heading = soup.find(string=re.compile(r"CCASS holdings on \d{4}-\d{2}-\d{2}"))
        holdings_date = parse_iso_date(str(date_heading)) if date_heading else None

        summary_values: dict[str, tuple[int, float]] = {}
        details_table = None
        for table in soup.find_all("table"):
            text = table.get_text(" ", strip=True)
            if "Total in CCASS" in text and "Issued securities" in text:
                for row in table.select("tr"):
                    cells = [cell.get_text(" ", strip=True) for cell in row.select("th,td")]
                    if len(cells) >= 3:
                        try:
                            summary_values[cells[0]] = (parse_int(cells[1]), parse_float(cells[2]))
                        except ValueError:
                            pass
            if "CCASS ID" in text and "Cumul" in text:
                details_table = table

        if details_table is None:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                "Holdings table was not found; the source page may have changed.",
            )

        holdings: list[HoldingRow] = []
        for row in details_table.select("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.select("th,td")]
            if (
                len(cells) < 7
                or not cells[0].isdigit()
                or not re.fullmatch(r"[A-Z]\d{5}", cells[1])
            ):
                continue
            try:
                holdings.append(
                    HoldingRow(
                        rank=int(cells[0]),
                        participant_id=cells[1],
                        participant=cells[2],
                        shares=parse_int(cells[3]),
                        last_change=parse_iso_date(cells[4]),
                        pct_of_issued=parse_float(cells[5]),
                        cumulative_pct_of_issued=parse_float(cells[6]),
                        participant_category=classify_participant(cells[1], cells[2]),
                    )
                )
            except (ValueError, IndexError) as exc:
                raise PlatformError(
                    ErrorCode.PARSE_ERROR,
                    f"Could not parse holdings row {cells!r}: {exc}",
                ) from exc

        if not holdings:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "The holdings table was present but no participant rows could be parsed.",
            )

        total_ccass = summary_values.get("Total in CCASS", (None, None))
        issued = summary_values.get("Issued securities", (None, None))
        non_ccass = summary_values.get("Securities not in CCASS", (None, None))
        total_ccass_shares = total_ccass[0]

        def pct_of_ccass(n: int) -> float | None:
            return round(n / total_ccass_shares * 100, 4) if total_ccass_shares else None

        top5_shares = sum(row.shares for row in holdings[:5])
        top10_shares = sum(row.shares for row in holdings[:10])
        warnings: list[str] = []
        if holdings_date is None:
            warnings.append("Holdings date could not be read from the source page.")
        if total_ccass[1] is not None and total_ccass[1] > 100:
            warnings.append(
                "CCASS percentage exceeds 100%; the issued-share denominator may be stale after a corporate action."
            )

        return CcassResponse(
            metadata=SourceMetadata(
                code=code,
                name=name,
                issue_id=issue_id,
                holdings_date=holdings_date,
                fetched_at=datetime.now(UTC),
                source_url=source_url,
                cached=cached,
            ),
            holdings_summary=HoldingsSummary(
                total_in_ccass_shares=total_ccass[0],
                total_in_ccass_pct_of_issued=total_ccass[1],
                issued_shares=issued[0],
                non_ccass_shares=non_ccass[0],
                non_ccass_pct_of_issued=non_ccass[1],
                participant_count=len(holdings),
                top5_pct_of_issued=holdings[min(4, len(holdings) - 1)].cumulative_pct_of_issued,
                top10_pct_of_issued=holdings[min(9, len(holdings) - 1)].cumulative_pct_of_issued,
                top5_pct_of_ccass=pct_of_ccass(top5_shares),
                top10_pct_of_ccass=pct_of_ccass(top10_shares),
            ),
            holdings=holdings[: max(1, min(limit, 100))],
            data_quality_warnings=warnings,
        )
