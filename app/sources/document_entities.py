from __future__ import annotations

import io
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import httpx
from pypdf import PdfReader

from app.models import DocumentEntitiesMetadata, DocumentEntitiesResponse, DocumentEntityRow
from app.sources.announcements import HKEXNewsAnnouncementsSource

# Discovery is dynamic: corporate-action documents (placings, offers, rights
# issues, circulars) are found per stock from the HKEXnews announcement
# stream at runtime — no per-stock document whitelist.
MAX_DISCOVERY_WINDOW_DAYS = 2 * 365
MAX_DOCUMENTS_PER_RUN = 4
MAX_FALLBACK_DOCUMENTS = 3
MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 140
RUN_BUDGET_SECONDS = 45.0

ENTITY_DOCUMENT_CATEGORIES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("general offer", re.compile(r"general offer|mandatory.{0,30}offer|voluntary.{0,30}offer|unconditional\s+cash\s+offer|cash\s+offer|composite document|offer document|offer announcement|merger by way of|要約", re.I)),
    ("whitewash", re.compile(r"whitewash|清洗交易", re.I)),
    ("rights issue", re.compile(r"rights issue|供股", re.I)),
    ("placing", re.compile(r"placing|配售|先舊後新|subscription", re.I)),
    ("underwriting", re.compile(r"underwrit", re.I)),
    ("circular", re.compile(r"circular|通函", re.I)),
)
NON_ENTITY_TITLE_RE = re.compile(r"monthly return|esg|sustainab|可持續|governance|agm|sgm|notice of|proxy|annual report|interim report|quarterly", re.I)


def _classify_entity_document(title: str) -> str | None:
    if NON_ENTITY_TITLE_RE.search(title):
        return None
    for category, pattern in ENTITY_DOCUMENT_CATEGORIES:
        if pattern.search(title):
            return category
    return None


@dataclass(frozen=True)
class HKEXDocumentSpec:
    stock_code: str
    document_id: str
    document_type: str
    announcement_date: date
    url: str


_TYPES = (
    ("independent_financial_adviser", r"independent\s+financial\s+adviser"),
    ("financial_adviser", r"financial\s+adviser"),
    ("placing_agent", r"placing\s+agent"),
    ("underwriter", r"underwriter"),
    ("offeror", r"offeror"),
    ("whitewash_waiver", r"whitewash(?:\s+waiver)?"),
    ("concert_party", r"concert\s+party|concert\s+parties"),
)


def _extract_rows(spec: HKEXDocumentSpec, text: str, retrieved_at: datetime) -> list[DocumentEntityRow]:
    rows: list[DocumentEntityRow] = []
    normalized = re.sub(r"\s+", " ", text).strip()
    for entity_type, label in _TYPES:
        for match in re.finditer(label, normalized, flags=re.I):
            if entity_type == "financial_adviser" and re.search(r"independent\s*$", normalized[max(0, match.start() - 20):match.start()], re.I):
                continue
            window = normalized[max(0, match.start() - 240): min(len(normalized), match.end() + 300)]
            # Capture only an explicitly named organisation adjacent to a role label.
            name_pattern = r"([A-Z][A-Za-z0-9 &'.,()/-]{2,100}?(?:Limited|Corporation|Company Limited|Securities Company Limited))"
            # Prefer the organisation explicitly following the role label; only
            # fall back to the preceding context when the document uses
            # "<name>, the <role>" wording.
            after_label = normalized[match.end() : min(len(normalized), match.end() + 260)]
            name_match = None
            if entity_type == "offeror":
                name_match = re.search(r"Offeror[”\"]?\s*[:\-]?\s*([A-Z][A-Za-z0-9 &'.,()/-]{2,100}?(?:Limited|Corporation|Company Limited|Securities Company Limited))", normalized, re.I)
            elif entity_type == "placing_agent":
                name_match = re.search(r"with\s+([A-Z][A-Za-z ]+Limited)\s*\(", normalized, re.I)
            elif entity_type == "underwriter":
                name_match = re.search(r"(?:First\s+|Second\s+)?Underwriter\s*:\s*([A-Z][A-Za-z0-9 &'.,()/-]{2,100}?(?:Limited|Corporation|Company Limited|Securities Company Limited))", normalized, re.I)
            if name_match is None:
                name_match = re.search(name_pattern, after_label)
            if name_match is None:
                before_label = normalized[max(0, match.start() - 240) : match.start()]
                name_match = re.search(name_pattern, before_label)
            entity_name = name_match.group(1).strip(" ,.;:") if name_match else None
            direct = window[:500]
            if entity_name is None and entity_type not in {"whitewash_waiver", "concert_party"}:
                continue
            rows.append(DocumentEntityRow(stock_code=spec.stock_code, document_id=spec.document_id, document_type=spec.document_type, entity_type=entity_type, entity_name=entity_name, direct_source_fact=direct, derived_classification=None, source_url=spec.url, announcement_date=spec.announcement_date, retrieved_at=retrieved_at))
            break
    return rows


class HKEXDocumentEntitiesSource:
    def __init__(self, timeout: float = 45.0, client: httpx.AsyncClient | None = None, announcements: HKEXNewsAnnouncementsSource | None = None):
        self.timeout = timeout
        self.client = client
        self.announcements = announcements or HKEXNewsAnnouncementsSource()

    async def get_entities(self, stock_code: str | int) -> DocumentEntitiesResponse:
        code = str(stock_code).zfill(5)
        now = datetime.now(UTC)
        warnings: list[str] = []
        try:
            specs, fallback_specs, discovery_warnings = await self._discover_entity_documents(code)
        except Exception as exc:
            warnings.append(f"DISCOVERY_FAILED:{type(exc).__name__}")
            return DocumentEntitiesResponse(metadata=DocumentEntitiesMetadata(code=code, fetched_at=now, source_status="unavailable", documents_attempted=0, documents_fetched=0, rows_extracted=0), rows=[], data_quality_warnings=warnings)
        warnings.extend(discovery_warnings)
        rows: list[DocumentEntityRow] = []
        failed = 0
        deadline = time.monotonic() + RUN_BUDGET_SECONDS
        async with (self.client or httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})) as client:
            for spec in specs:
                if time.monotonic() > deadline - 3.0 and rows:
                    warnings.append("RUN_BUDGET_REACHED: time budget exhausted before this document")
                    break
                try:
                    response = await client.get(spec.url)
                    response.raise_for_status()
                    if len(response.content) > MAX_PDF_BYTES:
                        warnings.append(f"DOCUMENT_TOO_LARGE:{spec.document_id}:{len(response.content)}")
                        failed += 1
                        continue
                    reader = PdfReader(io.BytesIO(response.content))
                    if len(reader.pages) > MAX_PDF_PAGES:
                        warnings.append(f"DOCUMENT_TOO_MANY_PAGES:{spec.document_id}:{len(reader.pages)}")
                        failed += 1
                        continue
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    rows.extend(_extract_rows(spec, text, now))
                except Exception as exc:
                    warnings.append(f"DOCUMENT_FAILED:{spec.document_id}:{type(exc).__name__}")
                    failed += 1
            if not rows and fallback_specs:
                fallback_batch = fallback_specs[:MAX_FALLBACK_DOCUMENTS]
                warnings.append(f"COVER_PAGE_FALLBACK_ATTEMPTED:{len(fallback_batch)}")
                for spec in fallback_batch:
                    if time.monotonic() > deadline - 3.0:
                        warnings.append("RUN_BUDGET_REACHED: time budget exhausted before this document")
                        break
                    try:
                        response = await client.get(spec.url)
                        response.raise_for_status()
                        if len(response.content) > MAX_PDF_BYTES:
                            continue
                        fallback_reader = PdfReader(io.BytesIO(response.content))
                        if len(fallback_reader.pages) > MAX_PDF_PAGES:
                            continue
                        text = "\n".join(page.extract_text() or "" for page in fallback_reader.pages)
                        rows.extend(_extract_rows(spec, text, now))
                    except Exception as exc:
                        warnings.append(f"FALLBACK_DOCUMENT_FAILED:{spec.document_id}:{type(exc).__name__}")
        if rows and not failed:
            status = "ready"
        elif rows:
            status = "partial"
        else:
            status = "unavailable"
        fetched = len(specs) - failed
        if fetched > 0 and not rows:
            warnings.append(
                f"NO_ENTITIES_EXTRACTED: {fetched} document(s) parsed but no intermediary/offeror labels matched "
                "(genuine absence, or document layout not recognised — see cover-page fallback coverage)"
            )
        return DocumentEntitiesResponse(metadata=DocumentEntitiesMetadata(code=code, fetched_at=now, source_status=status, documents_attempted=len(specs), documents_fetched=fetched, rows_extracted=len(rows)), rows=rows, data_quality_warnings=warnings)

    async def _discover_entity_documents(self, code: str) -> tuple[list[HKEXDocumentSpec], list[str]]:
        """Find corporate-action documents (placings, offers, rights issues,
        circulars) for any stock from the HKEXnews announcement stream — these
        carry the placing agents, advisers, offerors, underwriters and
        whitewash wording the entity extractor needs.

        Also returns a small title-agnostic fallback list (most recent PDFs
        that escaped title classification): short cover-page announcements
        often name the parties without saying so in the title."""
        warnings: list[str] = []
        end = datetime.now(UTC).date()
        start = end - timedelta(days=MAX_DISCOVERY_WINDOW_DAYS)
        announcements = await self.announcements.get_announcements(code, start_date=start, end_date=end, row_range=400)
        candidates: dict[str, tuple[date, str, str]] = {}
        fallback: dict[str, tuple[date, str]] = {}
        for row in announcements.announcements:
            title = (row.title or "").strip()
            if not title or not row.link:
                continue
            category = _classify_entity_document(title)
            if category is not None:
                candidates[row.link] = (row.announcement_date, category, title)
            elif row.link.lower().endswith(".pdf") and not NON_ENTITY_TITLE_RE.search(title):
                fallback[row.link] = (row.announcement_date, title)
        if not candidates:
            warnings.append("NO_ENTITY_DOCUMENTS_DISCOVERED: no placing/offer/rights/circular documents found in the discovery window")
        ordered = sorted(candidates.items(), key=lambda item: item[1][0], reverse=True)
        if len(ordered) > MAX_DOCUMENTS_PER_RUN:
            warnings.append(f"DISCOVERY_CAPPED: parsing latest {MAX_DOCUMENTS_PER_RUN} of {len(ordered)} discovered documents (capacity discipline; heavy pulls move to the async pattern)")
            ordered = ordered[:MAX_DOCUMENTS_PER_RUN]
        specs = []
        for url, (announcement_date, category, _title) in ordered:
            document_id = url.rsplit("/", 1)[-1].removesuffix(".pdf")
            specs.append(HKEXDocumentSpec(stock_code=code, document_id=document_id, document_type=f"{category} document", announcement_date=announcement_date, url=url))
        tried = {spec.url for spec in specs}
        fallback_specs = []
        for url, (announcement_date, _title) in sorted(fallback.items(), key=lambda item: item[1][0], reverse=True):
            if url in tried:
                continue
            document_id = url.rsplit("/", 1)[-1].removesuffix(".pdf")
            fallback_specs.append(HKEXDocumentSpec(stock_code=code, document_id=document_id, document_type="cover_page_fallback", announcement_date=announcement_date, url=url))
            if len(fallback_specs) >= MAX_FALLBACK_DOCUMENTS:
                break
        return specs, fallback_specs, warnings
