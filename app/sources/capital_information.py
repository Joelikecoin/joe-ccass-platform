from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import CapitalInformationMetadata, CapitalInformationResponse, CapitalInformationRow
from ccass_core.normalize import normalize_stock_code

CAPITAL_INFORMATION_SOURCE_NAME = "10jqka F10"
CAPITAL_INFORMATION_SOURCE_PENDING_NAME = "Capital information source pending"
CAPITAL_INFORMATION_SOURCE_PENDING_URL: str | None = None
CAPITAL_INFORMATION_SOURCE_URL_TEMPLATE = "https://stockpage.10jqka.com.cn/basicweb/176/HK{code}/"

_TOTAL_SHARES_RE = re.compile(r"\u603b\u80a1\u672c[:：]\s*(?P<value>[\d.]+)\s*(?P<unit>[\u4ebf\u4e07]?\u80a1)?")
_BOARD_LOT_RE = re.compile(r"\u6bcf\u624b\u80a1\u6570[:：]\s*(?P<value>[\d.]+)\s*(?P<unit>\u80a1)?")
_ROE_RE = re.compile(r"\u51c0\u8d44\u4ea7\u6536\u76ca\u7387\(\u644a\u8584\)[:：]\s*(?P<value>-?[\d.]+)\s*(?P<unit>%?)")
_DEBT_RE = re.compile(r"\u8d44\u4ea7\u8d1f\u503a\u7387[:：]\s*(?P<value>-?[\d.]+)\s*(?P<unit>%?)")
_REPORT_PERIOD_RE = re.compile(
    r"\u4e0a\u8ff0\u6570\u636e\u6765\u6e90\u4e8e(?P<year>\d{4})\u5e74(?P<period>\u4e00\u5b63\u62a5|\u4e2d\u62a5|\u4e09\u5b63\u62a5|\u5e74\u62a5)"
)


class CapitalInformationSource(Protocol):
    async def get_capital_information(self, code: str | int) -> CapitalInformationResponse: ...


class PendingCapitalInformationSource:
    async def get_capital_information(self, code: str | int) -> CapitalInformationResponse:
        normalized = normalize_stock_code(code)
        return CapitalInformationResponse(
            metadata=CapitalInformationMetadata(
                code=normalized,
                source_name=CAPITAL_INFORMATION_SOURCE_PENDING_NAME,
                source_url=CAPITAL_INFORMATION_SOURCE_PENDING_URL,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                capital_information_count=0,
                source_status="pending",
            ),
            capital_information=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "CAPITAL_INFORMATION_SOURCE_PENDING",
                    "Capital information source is pending approval; placeholder read path only.",
                )
            ],
        )


@dataclass(frozen=True, slots=True)
class ParsedCapitalInformationPage:
    company_name: str | None
    rows: tuple[CapitalInformationRow, ...]
    report_period: date | None
    warnings: tuple[str, ...]


class ThsF10CapitalInformationSource:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def get_capital_information(self, code: str | int) -> CapitalInformationResponse:
        normalized = normalize_stock_code(code)
        source_url = self._build_source_url(normalized)
        try:
            html = await self._fetch_html(source_url)
            parsed = self._parse_page(html, source_url=source_url)
            rows = list(parsed.rows)
            if not rows:
                return self._unavailable_response(
                    normalized,
                    source_url,
                    company_name=parsed.company_name,
                    message="The 10jqka capital information page did not yield any capital rows.",
                )
            metadata = CapitalInformationMetadata(
                code=normalized,
                name=parsed.company_name,
                source_name=CAPITAL_INFORMATION_SOURCE_NAME,
                source_url=source_url,
                fetched_at=datetime.now(UTC),
                data_as_of=parsed.report_period,
                capital_information_count=len(rows),
                source_status="ready",
            )
            return CapitalInformationResponse(
                metadata=metadata,
                capital_information=rows,
                data_quality_warnings=list(dict.fromkeys(parsed.warnings)),
            )
        except PlatformError as exc:
            return self._unavailable_response(
                normalized,
                source_url,
                message=f"Capital information source unavailable ({exc.code}: {exc.message}).",
            )
        except Exception as exc:
            return self._unavailable_response(
                normalized,
                source_url,
                message=f"Capital information source unavailable ({type(exc).__name__}).",
            )

    async def _fetch_html(self, source_url: str) -> str:
        headers = {
            "User-Agent": getattr(self.settings, "user_agent", None)
            or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        try:
            async with self._request_lock:
                wait = getattr(self.settings, "min_request_interval_seconds", 0.0) - (
                    time.monotonic() - self._last_request_at
                )
                if wait > 0:
                    await asyncio.sleep(wait)
                async with httpx.AsyncClient(
                    timeout=getattr(self.settings, "request_timeout_seconds", 20.0),
                    follow_redirects=True,
                    headers=headers,
                ) as client:
                    response = await client.get(source_url)
                    self._last_request_at = time.monotonic()
            if response.status_code == 403:
                raise PlatformError(
                    ErrorCode.SOURCE_FORBIDDEN,
                    "10jqka rejected the capital information request.",
                    retry_recommended=False,
                    status_code=503,
                )
            if response.status_code == 429:
                raise PlatformError(
                    ErrorCode.SOURCE_RATE_LIMITED,
                    "10jqka rate limited the capital information request.",
                    retry_recommended=True,
                    retry_after_seconds=60,
                    status_code=503,
                )
            if response.status_code >= 500:
                raise PlatformError(
                    ErrorCode.SOURCE_UNAVAILABLE,
                    "10jqka capital information is temporarily unavailable.",
                    retry_recommended=True,
                    status_code=503,
                )
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                "10jqka capital information request timed out.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.NetworkError as exc:
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                f"10jqka capital information network failure: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.HTTPError as exc:
            raise PlatformError(
                ErrorCode.DATA_SOURCE_ERROR,
                f"10jqka capital information request failed: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=502,
            ) from exc

    def _parse_page(self, html: str, *, source_url: str) -> ParsedCapitalInformationPage:
        soup = BeautifulSoup(html, "html.parser")
        company_name = self._extract_company_name(soup)
        lines = self._text_lines(soup)

        note_line = next(
            (
                line
                for line in lines
                if "\u4e0a\u8ff0\u6570\u636e\u6765\u6e90\u4e8e" in line
                or "\u6ce8\u91ca" in line
            ),
            None,
        )
        report_period = self._parse_report_period(note_line)
        note_text = self._clean_note(note_line)
        warnings: list[str] = []
        if company_name is None:
            warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "CAPITAL_INFORMATION_COMPANY_NAME_UNPARSED",
                    "The 10jqka capital information page did not expose a stable company name.",
                )
            )
        if report_period is None:
            warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "CAPITAL_INFORMATION_REPORT_PERIOD_UNPARSED",
                    "The 10jqka capital information page did not expose a stable reporting period.",
                )
            )
        if note_line is None:
            warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "CAPITAL_INFORMATION_NOTE_MISSING",
                    "The 10jqka capital information page did not expose a stable note line.",
                )
            )

        rows: list[CapitalInformationRow] = []
        metric_lines = {
            "Total shares": self._find_metric_line(lines, _TOTAL_SHARES_RE),
            "Board lot size": self._find_metric_line(lines, _BOARD_LOT_RE),
            "Diluted ROE": self._find_metric_line(lines, _ROE_RE),
            "Debt ratio": self._find_metric_line(lines, _DEBT_RE),
        }
        row_specs = (
            ("Total shares", _TOTAL_SHARES_RE, "reporting capital", "?"),
            ("Board lot size", _BOARD_LOT_RE, "board lot", "?"),
            ("Diluted ROE", _ROE_RE, "profitability", "%"),
            ("Debt ratio", _DEBT_RE, "leverage", "%"),
        )
        for label, pattern, note_label, default_unit in row_specs:
            metric_line = metric_lines.get(label)
            if metric_line is None:
                warnings.append(
                    structured_warning(
                        "SOURCE_STATUS",
                        f"CAPITAL_INFORMATION_{_warning_key(label)}_MISSING",
                        f"The 10jqka capital information page did not expose {label.lower()}.",
                    )
                )
                continue
            match = pattern.search(metric_line)
            if match is None:
                warnings.append(
                    structured_warning(
                        "SOURCE_STATUS",
                        f"CAPITAL_INFORMATION_{_warning_key(label)}_MISSING",
                        f"The 10jqka capital information page did not expose {label.lower()}.",
                    )
                )
                continue
            value = match.group("value").strip()
            unit = match.groupdict().get("unit") or None
            rows.append(
                CapitalInformationRow(
                    label=label,
                    value=value,
                    unit=(unit or default_unit),
                    as_of=report_period,
                    source=CAPITAL_INFORMATION_SOURCE_NAME,
                    note="; ".join(
                        part
                        for part in (
                            f"Source note: {note_text}" if note_text else None,
                            f"Parsed from 10jqka capital summary ({note_label}).",
                        )
                        if part
                    )
                    or None,
                    link=source_url,
                )
            )

        if not rows:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "The 10jqka capital information page did not contain parseable capital rows.",
            )
        return ParsedCapitalInformationPage(
            company_name=company_name,
            rows=tuple(rows),
            report_period=report_period,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _extract_company_name(soup: BeautifulSoup) -> str | None:
        for selector in ("h1", "title"):
            node = soup.find(selector)
            if node is None:
                continue
            text = " ".join(node.stripped_strings).strip()
            if not text:
                continue
            text = text.split("(", 1)[0].strip()
            text = text.replace("_F10_\u540c\u82b1\u987a\u91d1\u878d\u670d\u52a1\u7f51", "").strip()
            text = text.replace("\u6700\u65b0\u52a8\u6001", "").strip()
            if text:
                return text
        return None

    @staticmethod
    def _text_lines(soup: BeautifulSoup) -> list[str]:
        lines: list[str] = []
        for raw in soup.get_text("\n", strip=True).splitlines():
            line = re.sub(r"\s+", " ", raw.strip())
            if not line:
                continue
            lines.append(line)
        return lines

    @staticmethod
    def _clean_note(note_line: str | None) -> str | None:
        if note_line is None:
            return None
        note = note_line.replace("\u6ce8\u91ca\uff1a", "").strip()
        return note or None

    @staticmethod
    def _find_metric_line(lines: list[str], pattern: re.Pattern[str]) -> str | None:
        return next((line for line in lines if pattern.search(line)), None)

    @staticmethod
    def _parse_report_period(note_line: str | None) -> date | None:
        if not note_line:
            return None
        match = _REPORT_PERIOD_RE.search(note_line)
        if not match:
            return None
        year = int(match.group("year"))
        period = match.group("period")
        if period == "\u4e00\u5b63\u62a5":
            return date(year, 3, 31)
        if period == "\u4e2d\u62a5":
            return date(year, 6, 30)
        if period == "\u4e09\u5b63\u62a5":
            return date(year, 9, 30)
        if period == "\u5e74\u62a5":
            return date(year, 12, 31)
        return None

    def _unavailable_response(
        self,
        normalized: str,
        source_url: str,
        *,
        message: str,
        company_name: str | None = None,
    ) -> CapitalInformationResponse:
        return CapitalInformationResponse(
            metadata=CapitalInformationMetadata(
                code=normalized,
                name=company_name,
                source_name=CAPITAL_INFORMATION_SOURCE_NAME,
                source_url=source_url,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                capital_information_count=0,
                source_status="unavailable",
            ),
            capital_information=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "CAPITAL_INFORMATION_SOURCE_UNAVAILABLE",
                    message,
                )
            ],
        )

    @staticmethod
    def _build_source_url(normalized: str) -> str:
        compact = normalized.lstrip("0") or "0"
        return CAPITAL_INFORMATION_SOURCE_URL_TEMPLATE.format(code=compact)


def _warning_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")
