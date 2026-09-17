from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

import httpx
from pypdf import PdfReader

from app.models import DocumentEntitiesMetadata, DocumentEntitiesResponse, DocumentEntityRow


@dataclass(frozen=True)
class HKEXDocumentSpec:
    stock_code: str
    document_id: str
    document_type: str
    announcement_date: date
    url: str


DOCUMENT_ENTITY_SPECS = (
    HKEXDocumentSpec("00388", "2026031701088", "AGM circular", date(2026, 3, 17), "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0317/2026031701088.pdf"),
    HKEXDocumentSpec("00006", "2026040800063", "major transaction circular", date(2026, 4, 8), "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0408/2026040800063.pdf"),
)

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
            window = normalized[max(0, match.start() - 240): min(len(normalized), match.end() + 300)]
            # Capture only an explicitly named organisation adjacent to a role label.
            name_match = re.search(r"([A-Z][A-Za-z0-9 &'.,()/-]{2,100}?(?:Limited|Corporation|Company Limited|Securities Company Limited))", window)
            entity_name = name_match.group(1).strip(" ,.;:") if name_match else None
            direct = window[:500]
            if entity_name is None and entity_type not in {"whitewash_waiver", "concert_party"}:
                continue
            rows.append(DocumentEntityRow(stock_code=spec.stock_code, document_id=spec.document_id, document_type=spec.document_type, entity_type=entity_type, entity_name=entity_name, direct_source_fact=direct, derived_classification=None, source_url=spec.url, announcement_date=spec.announcement_date, retrieved_at=retrieved_at))
            break
    return rows


class HKEXDocumentEntitiesSource:
    def __init__(self, timeout: float = 45.0):
        self.timeout = timeout

    async def get_entities(self, stock_code: str | int) -> DocumentEntitiesResponse:
        code = str(stock_code).zfill(5)
        specs = tuple(spec for spec in DOCUMENT_ENTITY_SPECS if spec.stock_code == code)
        now = datetime.now(UTC)
        rows: list[DocumentEntityRow] = []
        warnings: list[str] = []
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
            for spec in specs:
                try:
                    response = await client.get(spec.url)
                    response.raise_for_status()
                    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(response.content)).pages)
                    rows.extend(_extract_rows(spec, text, now))
                except Exception as exc:
                    warnings.append(f"DOCUMENT_FAILED:{spec.document_id}:{type(exc).__name__}")
        status = "ready" if rows and not warnings else ("partial" if rows else "unavailable")
        return DocumentEntitiesResponse(metadata=DocumentEntitiesMetadata(code=code, fetched_at=now, source_status=status, documents_attempted=len(specs), documents_fetched=len(specs)-len(warnings), rows_extracted=len(rows)), rows=rows, data_quality_warnings=warnings)
