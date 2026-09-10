from __future__ import annotations

import asyncio
import io
import re
from datetime import UTC, date, datetime

import httpx
from pypdf import PdfReader

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.models import (
    AnnouncementRow,
    ShareCapitalHistoryMetadata,
    ShareCapitalHistoryResponse,
    ShareCapitalHistoryRow,
)
from app.services.announcements import AnnouncementsService, get_announcements_service
from ccass_core.normalize import normalize_stock_code

SOURCE_NAME = "HKEXnews"
_DATE_RE = re.compile(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})")
_BALANCE_RE = re.compile(
    r"Balance\s+at\s+close\s+of\s+the\s+month\s+([\d,]+)\s+([\d,]+)?\s*([\d,]+)?",
    re.I,
)


class HKEXShareCapitalHistorySource:
    def __init__(self, settings: Settings | None = None, announcements: AnnouncementsService | None = None) -> None:
        self.settings = settings or get_settings()
        self.announcements = announcements or get_announcements_service()

    async def get_share_capital_history(
        self, code: str | int, *, start_date: date | None = None, end_date: date | None = None
    ) -> ShareCapitalHistoryResponse:
        normalized = normalize_stock_code(code)
        response = await self.announcements.get_announcements(normalized, start_date=start_date, end_date=end_date)
        docs = [row for row in response.announcements if "monthly return" in row.title.casefold()]
        rows: list[ShareCapitalHistoryRow] = []
        warnings: list[str] = []
        fetched = parsed = 0
        semaphore = asyncio.Semaphore(6)

        async def process(announcement: AnnouncementRow):
            async with semaphore:
                try:
                    text = await self._fetch_text(announcement.link)
                    row = self._parse(announcement, text)
                    if row is None:
                        raise ValueError("issued-share balance not found")
                    return row, None, True
                except Exception as exc:
                    return None, structured_warning("DATA_LIMITATION", "HKEX_MONTHLY_RETURN_PARSE_FAILED", f"{announcement.link}: {type(exc).__name__}: {exc}"), False

        results = await asyncio.gather(*(process(announcement) for announcement in docs))
        for row, warning, fetched_ok in results:
            fetched += int(fetched_ok)
            parsed += int(row is not None)
            if row is not None:
                rows.append(row)
            if warning:
                warnings.append(warning)
        status = "ready" if docs and not warnings else ("partial" if rows else "unavailable")
        return ShareCapitalHistoryResponse(
            metadata=ShareCapitalHistoryMetadata(
                code=normalized, source_name=SOURCE_NAME, fetched_at=datetime.now(UTC), source_status=status,
                documents_attempted=len(docs), documents_fetched=fetched, documents_parsed=parsed,
                documents_failed=len(docs) - parsed,
            ),
            rows=sorted(rows, key=lambda item: item.announce_date), data_quality_warnings=warnings,
        )

    async def _fetch_text(self, url: str | None) -> str:
        if not url:
            raise ValueError("missing source URL")
        last: Exception | None = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=True, headers={"User-Agent": self.settings.user_agent}) as client:
                    response = await client.get(url)
                response.raise_for_status()
                reader = PdfReader(io.BytesIO(response.content))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                if not text.strip():
                    raise ValueError("PDF has no usable text layer")
                return text
            except Exception as exc:
                last = exc
                if attempt == 0:
                    await asyncio.sleep(0.2)
        raise last or RuntimeError("document fetch failed")

    def _parse(self, announcement: AnnouncementRow, text: str) -> ShareCapitalHistoryRow | None:
        matches = list(_BALANCE_RE.finditer(text))
        if not matches:
            return None
        # The first issued-share table is the target; use the final balance value when present.
        raw = (matches[0].group(3) or matches[0].group(1)).replace(",", "")
        shares = float(raw)
        movement = re.search(r"Increase\s*/\s*decrease\s*\(-\)(.*?)(?:Balance\s+at\s+close\s+of\s+the\s+month)", text, re.I | re.S)
        candidate_reason = movement.group(1).strip(" :-\n") if movement and movement.group(1).strip() else ""
        reason = candidate_reason[:240] if re.search(r"[A-Za-z]", candidate_reason) else None
        dates = _DATE_RE.findall(movement.group(1)) if movement else []
        change_date = None
        if dates:
            try:
                change_date = date.fromisoformat(f"{dates[0][2]}-{datetime.strptime(dates[0][1], '%B').month:02d}-{int(dates[0][0]):02d}")
            except Exception:
                change_date = None
        return ShareCapitalHistoryRow(
            announce_date=announcement.announcement_date, shares_million=shares / 1_000_000,
            shares_approx=f"{shares / 1_000_000:,.3f} million", reason=reason,
            reason_tags=["ISSUED_SHARES_MOVEMENT"] if reason else [], change_date=change_date,
            source=SOURCE_NAME, source_url=announcement.link or "",
        )
