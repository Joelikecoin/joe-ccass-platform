from __future__ import annotations

import asyncio
import re
import time
from datetime import UTC, date, datetime
from urllib.parse import urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.models import DisclosureInterestRow, DisclosureInterestsMetadata, DisclosureInterestsResponse
from ccass_core.normalize import normalize_stock_code


BASE = "https://di.hkex.com.hk/di/"
SEARCH = BASE + "NSSrchCorp.aspx?src=MAIN&lang=EN&g_lang=en"

# Real DION result rows are nested <tr>s whose first cell is a form serial
# such as CS20260908E00043 (shareholder notice) or DA20260811E00498 (director).
SERIAL_PATTERN = re.compile(r"^(?:CS|DA)\d{8}[EP]\d{5}$")
TOTAL_RECORDS_PATTERN = re.compile(r"Total records:\s*(?:</span>)?\s*(?:<span[^>]*>)?\s*([\d,]+)", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\d{2}/\d{2}/\d{4}")


class HKEXDisclosureInterestsSource:
    """Parser for the official DION substantial-shareholder result table."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def get_disclosures(self, code: str | int, *, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        normalized = normalize_stock_code(code)
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=True, headers={"User-Agent": self.settings.user_agent}) as client:
                page = await client.get(SEARCH)
                page.raise_for_status()
                soup = BeautifulSoup(page.text, "html.parser")
                form = soup.find("form")
                fields = {element.get("name"): element.get("value", "") for element in form.find_all("input") if element.get("name")} if form else {}
                fields.update({"txtStockCode": normalized, "cmdSearch": "Search", "ddlStartDateDD": f"{start_date.day:02d}", "ddlStartDateMM": f"{start_date.month:02d}", "ddlEndDateDD": f"{end_date.day:02d}", "ddlStartDateYYYY": str(start_date.year), "ddlEndDateMM": f"{end_date.month:02d}", "ddlEndDateYYYY": str(end_date.year)})
                result = await client.post(SEARCH, data=fields)
                result.raise_for_status()
                if "Home/Login" not in str(result.url) and "HKEX - Login" not in result.text:
                    return self._parse_result(normalized, result.text, start_date, end_date)
        except httpx.HTTPError:
            pass
        # DION's public form currently redirects non-browser POSTs to its login
        # host.  Reproduce the normal public browser session once, with a hard
        # bound, and hand the resulting HTML to the same parser.
        return await self._get_disclosures_via_browser(normalized, start_date=start_date, end_date=end_date)

    async def _get_disclosures_via_browser(self, code: str, *, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        async_playwright = self._load_playwright_async_api()
        if async_playwright is None:
            return self._unavailable(code, "DION browser transport unavailable: Playwright is not installed")
        timeout_ms = max(1_000, int(self.settings.request_timeout_seconds * 1_000))
        try:
            return await asyncio.wait_for(
                self._run_browser_search(async_playwright, code, start_date=start_date, end_date=end_date, timeout_ms=timeout_ms),
                timeout=max(1.0, self.settings.request_timeout_seconds),
            )
        except asyncio.TimeoutError:
            return self._unavailable(code, "DION browser transport timed out")
        except Exception as exc:
            detail = str(exc).strip().replace("\n", " ")[:220]
            return self._unavailable(code, f"DION browser transport failed: {type(exc).__name__}: {detail}")

    async def _run_browser_search(self, async_playwright, code: str, *, start_date: date, end_date: date, timeout_ms: int) -> DisclosureInterestsResponse:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                context = await browser.new_context(user_agent=self.settings.user_agent)
                page = await context.new_page()
                await page.goto(SEARCH, wait_until="domcontentloaded", timeout=timeout_ms)
                await page.locator("#txtStockCode").fill(code)
                for selector, value in (
                    ("#ddlStartDateDD", f"{start_date.day:02d}"),
                    ("#ddlStartDateMM", f"{start_date.month:02d}"),
                    ("#ddlStartDateYYYY", str(start_date.year)),
                    ("#ddlEndDateDD", f"{end_date.day:02d}"),
                    ("#ddlEndDateMM", f"{end_date.month:02d}"),
                    ("#ddlEndDateYYYY", str(end_date.year)),
                ):
                    await page.locator(selector).select_option(value)
                await page.locator("#cmdSearch").click(timeout=timeout_ms)
                await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
                result_link = page.get_by_role("link", name="List of all notices")
                await result_link.click(timeout=timeout_ms)
                await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)

                deadline = time.monotonic() + max(1.0, self.settings.request_timeout_seconds)
                collected: dict[str, DisclosureInterestRow] = {}
                total_records: int | None = None
                warnings: list[str] = []
                first_page_url = page.url
                html = await page.content()
                pg = 1
                # The browser only earns the first result page; the pager links
                # are stateless GETs (&pg=N), so later pages are fetched with
                # plain HTTP instead of paying a browser navigation per page.
                async with httpx.AsyncClient(timeout=max(1.0, self.settings.request_timeout_seconds), follow_redirects=True, headers={"User-Agent": self.settings.user_agent}) as client:
                    while True:
                        total_records = self._total_records(html) or total_records
                        parsed = self._parse_result(code, html, start_date, end_date)
                        new_before = len(collected)
                        for row in parsed.filings:
                            collected[row.filing_id] = row
                        if len(collected) == new_before:
                            break
                        pg += 1
                        next_url = self._page_url(first_page_url, pg)
                        if total_records is not None and len(collected) >= total_records:
                            break
                        if next_url is None:
                            break
                        if time.monotonic() > deadline - 5.0:
                            warnings.append(f"DI_PAGINATION_TIME_BUDGET: collected {len(collected)} of {total_records} records before the flow budget expired")
                            break
                        try:
                            follow = await client.get(next_url)
                            follow.raise_for_status()
                        except httpx.HTTPError as exc:
                            warnings.append(f"DI_PAGINATION_FETCH_FAILED at pg={pg}: {type(exc).__name__}")
                            break
                        html = follow.text
                if total_records is not None and len(collected) < total_records and not warnings:
                    warnings.append(
                        f"DI_DATE_WINDOW_DIFFERENCE: DION lists {total_records} records for the query; "
                        f"{len(collected)} carry an event date inside the requested window (DION's list "
                        "counter can use a slightly different date basis than the per-row event date)"
                    )
                if not collected:
                    warnings.append(
                        "DI_ZERO_ROWS_DIAGNOSTIC: "
                        f"final_url={page.url} total_records={total_records} "
                        f"title={await page.title()!r} notices_link_seen={first_page_url}"
                    )
                ordered = sorted(collected.values(), key=lambda row: (row.event_date, row.filing_id), reverse=True)
                metadata = DisclosureInterestsMetadata(code=code, source_url=SEARCH, fetched_at=datetime.now(UTC), filing_count=len(ordered))
                return DisclosureInterestsResponse(metadata=metadata, filings=ordered, data_quality_warnings=warnings)
            finally:
                await browser.close()

    @staticmethod
    def _page_url(first_page_url: str, pg: int) -> str | None:
        if "NSAllFormList.aspx" not in first_page_url:
            return None
        cleaned = re.sub(r"&?pg=\d+", "", first_page_url)
        if not cleaned.endswith(("&", "?")):
            cleaned += "&"
        return f"{cleaned}pg={pg}"

    @staticmethod
    def _total_records(html: str) -> int | None:
        match = TOTAL_RECORDS_PATTERN.search(html)
        return int(match.group(1).replace(",", "")) if match else None

    @staticmethod
    def _load_playwright_async_api():
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return None
        return async_playwright

    @staticmethod
    def _unavailable(code: str, warning: str) -> DisclosureInterestsResponse:
        return DisclosureInterestsResponse(
            metadata=DisclosureInterestsMetadata(
                code=code,
                source_url=SEARCH,
                fetched_at=datetime.now(UTC),
                source_status="unavailable",
                filing_count=0,
            ),
            data_quality_warnings=[warning],
        )

    def _parse_result(self, code: str, html: str, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        soup = BeautifulSoup(html, "html.parser")
        rows: dict[str, DisclosureInterestRow] = {}
        for tr in soup.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"], recursive=False)]
            if len(cells) < 8 or not SERIAL_PATTERN.match(cells[0]):
                continue
            date_match = DATE_PATTERN.search(cells[7]) if len(cells) > 7 else None
            if date_match is None:
                date_match = next((DATE_PATTERN.search(cell) for cell in cells if DATE_PATTERN.search(cell)), None)
            if date_match is None:
                continue
            event_date = datetime.strptime(date_match.group(), "%d/%m/%Y").date()
            if not start_date <= event_date <= end_date:
                continue
            links = tr.find_all("a")
            href = urljoin(BASE, links[0].get("href", "")) if links else ""

            def first_number(value: str, integer: bool = True):
                match = re.search(r"[\d,]+(?:\.\d+)?", value)
                if not match:
                    return None
                return int(match.group().replace(",", "")) if integer else float(match.group().replace(",", ""))

            classification = "director_or_substantial_shareholder" if "director" in cells[1].casefold() else "substantial_shareholder"
            rows[cells[0]] = DisclosureInterestRow(filing_id=cells[0], stock_code=code, event_date=event_date, filer=cells[1], classification=classification, shares_involved=first_number(cells[3]), average_price=first_number(cells[4], integer=False), present_balance=first_number(cells[5]), percentage=first_number(cells[6], integer=False), reason=cells[2], source_url=href, retrieved_at=datetime.now(UTC))
        ordered = sorted(rows.values(), key=lambda row: (row.event_date, row.filing_id), reverse=True)
        return DisclosureInterestsResponse(metadata=DisclosureInterestsMetadata(code=code, source_url=SEARCH, fetched_at=datetime.now(UTC), filing_count=len(ordered)), filings=ordered)
