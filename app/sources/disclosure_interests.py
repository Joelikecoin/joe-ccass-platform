from __future__ import annotations

import re
from datetime import UTC, date, datetime
from urllib.parse import urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.models import DisclosureInterestRow, DisclosureInterestsMetadata, DisclosureInterestsResponse
from ccass_core.normalize import normalize_stock_code


BASE = "https://di.hkex.com.hk/di/"
SEARCH = BASE + "NSSrchCorp.aspx?src=MAIN&lang=EN&g_lang=en"


class HKEXDisclosureInterestsSource:
    """Parser for the official DION substantial-shareholder result table."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def get_disclosures(self, code: str | int, *, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        normalized = normalize_stock_code(code)
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=True, headers={"User-Agent": self.settings.user_agent}) as client:
            page = await client.get(SEARCH)
            page.raise_for_status()
            soup = BeautifulSoup(page.text, "html.parser")
            form = soup.find("form")
            fields = {element.get("name"): element.get("value", "") for element in form.find_all("input") if element.get("name")} if form else {}
            fields.update({"txtStockCode": normalized, "cmdSearch": "Search", "ddlStartDateDD": f"{start_date.day:02d}", "ddlStartDateMM": f"{start_date.month:02d}", "ddlStartDateYYYY": str(start_date.year), "ddlEndDateDD": f"{end_date.day:02d}", "ddlEndDateMM": f"{end_date.month:02d}", "ddlEndDateYYYY": str(end_date.year)})
            result = await client.post(SEARCH, data=fields)
            result.raise_for_status()
        response = self._parse_result(normalized, result.text, start_date, end_date)
        return response

    def _parse_result(self, code: str, html: str, start_date: date, end_date: date) -> DisclosureInterestsResponse:
        soup = BeautifulSoup(html, "html.parser")
        rows: list[DisclosureInterestRow] = []
        table = next((table for table in soup.find_all("table") if "Form Serial Number" in table.get_text(" ", strip=True)), None)
        if table:
            for tr in table.find_all("tr")[1:]:
                cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])]
                if len(cells) < 8 or not cells[0]:
                    continue
                links = tr.find_all("a")
                filing_id = cells[0]
                href = urljoin(BASE, links[0].get("href", "")) if links else ""
                event_match = re.search(r"\d{2}/\d{2}/\d{4}", cells[-1])
                if not event_match:
                    continue
                event_date = datetime.strptime(event_match.group(), "%d/%m/%Y").date()
                if not start_date <= event_date <= end_date:
                    continue
                def first_number(value: str, integer: bool = True):
                    match = re.search(r"[\d,]+(?:\.\d+)?", value)
                    if not match:
                        return None
                    return int(match.group().replace(",", "")) if integer else float(match.group().replace(",", ""))
                classification = "director_or_substantial_shareholder" if "director" in cells[1].casefold() else "substantial_shareholder"
                rows.append(DisclosureInterestRow(filing_id=filing_id, stock_code=code, event_date=event_date, filer=cells[1], classification=classification, shares_involved=first_number(cells[3]), average_price=first_number(cells[4], integer=False), present_balance=first_number(cells[5]), percentage=first_number(cells[6], integer=False), reason=cells[2], source_url=href, retrieved_at=datetime.now(UTC)))
        return DisclosureInterestsResponse(metadata=DisclosureInterestsMetadata(code=code, source_url=SEARCH, fetched_at=datetime.now(UTC), filing_count=len(rows)), filings=rows)
