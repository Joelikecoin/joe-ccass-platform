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
from app.models import OfficerRow, OfficersMetadata, OfficersResponse
from ccass_core.normalize import normalize_stock_code

OFFICERS_SOURCE_NAME = "同花順 F10 managers"
OFFICERS_SOURCE_URL_TEMPLATE = "https://stockpage.10jqka.com.cn/basicweb/176/HK{code}/manager.html"
OFFICERS_SOURCE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
OFFICERS_SECTION_TITLES = {"高管简介", "高管簡介", "高管介绍", "高管介紹", "董事介绍", "董事介紹"}


class OfficersSource(Protocol):
    async def get_officers(self, code: str | int) -> OfficersResponse: ...


class PendingOfficersSource:
    async def get_officers(self, code: str | int) -> OfficersResponse:
        normalized = normalize_stock_code(code)
        return OfficersResponse(
            metadata=OfficersMetadata(
                code=normalized,
                source_name=OFFICERS_SOURCE_NAME,
                source_url=OFFICERS_SOURCE_URL_TEMPLATE.format(code=normalized.lstrip("0") or "0"),
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                officers_count=0,
                source_status="pending",
            ),
            officers=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "OFFICERS_SOURCE_PENDING",
                    "Officers source is pending approval; placeholder read path only.",
                )
            ],
        )


@dataclass(frozen=True, slots=True)
class ParsedOfficerRow:
    row: OfficerRow
    cutoff_date: date | None


@dataclass(frozen=True, slots=True)
class ParsedOfficersPage:
    company_name: str | None
    officers: tuple[ParsedOfficerRow, ...]
    warnings: tuple[str, ...]


class ThsF10OfficersSource:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def get_officers(self, code: str | int) -> OfficersResponse:
        normalized = normalize_stock_code(code)
        source_url = self._build_source_url(normalized)
        try:
            html = await self._fetch_html(source_url)
            parsed = self._parse_page(html)
            officer_rows = [item.row for item in parsed.officers]
            if not officer_rows:
                return self._unavailable_response(
                    normalized,
                    source_url,
                    company_name=parsed.company_name,
                    message="The 10jqka officers page did not yield any officer rows.",
                )
            data_as_of = max(
                (item.cutoff_date for item in parsed.officers if item.cutoff_date is not None),
                default=None,
            )
            metadata = OfficersMetadata(
                code=normalized,
                name=parsed.company_name,
                source_name=OFFICERS_SOURCE_NAME,
                source_url=source_url,
                fetched_at=datetime.now(UTC),
                data_as_of=data_as_of,
                officers_count=len(officer_rows),
                source_status="ready",
            )
            warnings = list(dict.fromkeys(parsed.warnings))
            return OfficersResponse(
                metadata=metadata,
                officers=officer_rows,
                data_quality_warnings=warnings,
            )
        except PlatformError as exc:
            return self._unavailable_response(
                normalized,
                source_url,
                message=f"Officers source unavailable ({exc.code}: {exc.message}).",
            )
        except Exception as exc:
            return self._unavailable_response(
                normalized,
                source_url,
                message=f"Officers source unavailable ({type(exc).__name__}).",
            )

    async def _fetch_html(self, source_url: str) -> str:
        headers = {
            "User-Agent": getattr(self.settings, "user_agent", OFFICERS_SOURCE_USER_AGENT),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        hostname = urlsplit(source_url).hostname or "unknown"
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
                    "10jqka rejected the officers request.",
                    retry_recommended=False,
                    status_code=503,
                )
            if response.status_code == 429:
                raise PlatformError(
                    ErrorCode.SOURCE_RATE_LIMITED,
                    "10jqka rate limited the officers request.",
                    retry_recommended=True,
                    retry_after_seconds=60,
                    status_code=503,
                )
            if response.status_code >= 500:
                raise PlatformError(
                    ErrorCode.SOURCE_UNAVAILABLE,
                    "10jqka officers are temporarily unavailable.",
                    retry_recommended=True,
                    status_code=503,
                )
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise PlatformError(
                ErrorCode.SOURCE_TIMEOUT,
                "10jqka officers request timed out.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.NetworkError as exc:
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                f"10jqka officers network failure: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=503,
            ) from exc
        except httpx.HTTPError as exc:
            raise PlatformError(
                ErrorCode.DATA_SOURCE_ERROR,
                f"10jqka officers request failed: {type(exc).__name__}.",
                retry_recommended=True,
                status_code=502,
            ) from exc

    def _parse_page(self, html: str) -> ParsedOfficersPage:
        soup = BeautifulSoup(html, "html.parser")
        company_name = self._extract_company_name(soup)
        lines = self._text_lines(soup)
        officers, parse_warnings = self._parse_officers_from_lines(lines)
        warnings: list[str] = []
        warnings.extend(parse_warnings)
        if company_name is None:
            warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "OFFICERS_COMPANY_NAME_UNPARSED",
                    "The 10jqka officers page did not expose a company name in a stable location.",
                )
            )
        if not officers:
            warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "OFFICERS_PARSE_EMPTY",
                    "The 10jqka officers page did not yield any parseable officer blocks.",
                )
            )
        return ParsedOfficersPage(
            company_name=company_name,
            officers=tuple(officers),
            warnings=tuple(warnings),
        )

    def _parse_officers_from_lines(self, lines: list[str]) -> tuple[list[ParsedOfficerRow], list[str]]:
        start_index = self._find_section_start(lines)
        if start_index is None:
            return [], [
                structured_warning(
                    "SOURCE_STATUS",
                    "OFFICERS_SECTION_MISSING",
                    "The 10jqka officers page did not expose a recognizable officers section.",
                )
            ]

        parsed: list[ParsedOfficerRow] = []
        warnings: list[str] = []
        index = start_index + 1
        while index < len(lines):
            current = lines[index]
            if self._looks_like_name(current) and self._looks_like_positions_block(lines, index + 1):
                block_end = self._find_next_name(lines, index + 1)
                block = lines[index + 1 : block_end]
                try:
                    parsed_row = self._parse_officer_block(current, block)
                except Exception as exc:
                    warnings.append(
                        structured_warning(
                            "SOURCE_STATUS",
                            "OFFICERS_BLOCK_PARSE_FAILED",
                            f"A 10jqka officers block could not be parsed ({type(exc).__name__}).",
                        )
                    )
                    parsed_row = None
                if parsed_row is not None:
                    parsed.append(parsed_row)
                index = block_end
                continue
            index += 1
        return parsed, warnings

    def _parse_officer_block(self, name: str, block: list[str]) -> ParsedOfficerRow | None:
        cleaned_block = [line for line in block if line and not self._is_boilerplate(line)]
        if not cleaned_block:
            return None

        positions_line, tenure_line, profile_lines, biography_lines = self._split_block(cleaned_block)
        positions, tenure_from, tenure_to, is_current = self._parse_positions(positions_line, tenure_line)
        sex, age, education, salary, cutoff_date = self._parse_profile(profile_lines)
        biography = " ".join(biography_lines).strip() or None
        officer = OfficerRow(
            name=self._clean_name(name),
            positions=positions,
            tenure_from=tenure_from,
            tenure_to=tenure_to,
            is_current=is_current,
            sex=sex,
            age=age,
            education=education,
            salary=salary,
            biography=biography,
        )
        return ParsedOfficerRow(row=officer, cutoff_date=cutoff_date)

    @staticmethod
    def _split_block(block: list[str]) -> tuple[str, str | None, list[str], list[str]]:
        positions_line = block[0]
        tenure_line: str | None = None
        profile_start = 1
        if "本届任期" in positions_line:
            profile_start = 1
        elif len(block) > 1 and "本届任期" in block[1]:
            tenure_line = block[1]
            profile_start = 2
        else:
            if len(block) > 1:
                profile_start = 1

        if tenure_line is None and "本届任期" in positions_line:
            match = re.search(r"(.*?本届任期[:：].*)", positions_line)
            if match:
                positions_line = match.group(1)

        profile_lines: list[str] = []
        biography_start = profile_start
        for index in range(profile_start, len(block)):
            line = block[index]
            profile_lines.append(line)
            biography_start = index + 1
            if "截止日期" in line:
                break
            if len(profile_lines) >= 3:
                break
        biography_lines = block[biography_start:]
        return positions_line, tenure_line, profile_lines, biography_lines

    @staticmethod
    def _parse_positions(positions_line: str, tenure_line: str | None) -> tuple[list[str], date | None, date | None, bool | None]:
        combined = " | ".join(line for line in (positions_line, tenure_line) if line)
        match = re.search(
            r"(?P<positions>.+?)(?:\s*\|\s*|\s+)本届任期[:：]\s*(?P<start>\d{4}-\d{2}-\d{2})(?:\s*(?:至今|至)\s*(?P<end>\d{4}-\d{2}-\d{2}))?",
            combined,
        )
        positions_text = positions_line.strip()
        tenure_from = None
        tenure_to = None
        is_current: bool | None = None
        if match:
            positions_text = match.group("positions").strip()
            tenure_from = _parse_date(match.group("start"))
            tenure_to = _parse_date(match.group("end"))
            is_current = tenure_to is None
        elif tenure_line:
            tenure_match = re.search(
                r"本届任期[:：]\s*(?P<start>\d{4}-\d{2}-\d{2})(?:\s*(?:至今|至)\s*(?P<end>\d{4}-\d{2}-\d{2}))?",
                tenure_line,
            )
            if tenure_match:
                tenure_from = _parse_date(tenure_match.group("start"))
                tenure_to = _parse_date(tenure_match.group("end"))
                is_current = tenure_to is None
        positions = [
            item.strip()
            for item in re.split(r"[，,、/]+", positions_text.replace("本届任期", ""))
            if item.strip()
        ]
        return positions, tenure_from, tenure_to, is_current

    @staticmethod
    def _parse_profile(profile_lines: list[str]) -> tuple[str | None, int | None, str | None, str | None, date | None]:
        blob = " ".join(profile_lines).strip()
        sex = None
        age = None
        education = None
        salary = None
        cutoff_date = None
        if blob:
            sex_match = re.search(r"(男|女)", blob)
            if sex_match:
                sex = sex_match.group(1)
            age_match = re.search(r"(?<!\d)(\d{1,3})(?!\d)", blob)
            if age_match:
                age_value = int(age_match.group(1))
                if 0 < age_value < 120:
                    age = age_value
            salary_match = re.search(r"(?:报酬|薪酬)[:：]\s*([^|]+)", blob)
            if salary_match:
                salary = salary_match.group(1).strip() or None
            cutoff_match = re.search(r"截止日期[:：]\s*([0-9\-]{4,10}|--)", blob)
            if cutoff_match:
                cutoff_date = _parse_date(cutoff_match.group(1))

            first_segment = re.split(r"(?:报酬|薪酬)[:：]|截止日期[:：]", blob, maxsplit=1)[0].strip()
            tokens = first_segment.split()
            if tokens and tokens[0] in {"男", "女"}:
                tokens = tokens[1:]
            if tokens and re.fullmatch(r"\d{1,3}", tokens[0]):
                tokens = tokens[1:]
            education = " ".join(tokens).replace("|", " ").strip() or None
        return sex, age, education, salary, cutoff_date

    @staticmethod
    def _find_section_start(lines: list[str]) -> int | None:
        for index, line in enumerate(lines):
            if line in OFFICERS_SECTION_TITLES:
                return index
        return None

    @staticmethod
    def _find_next_name(lines: list[str], start: int) -> int:
        for index in range(start, len(lines)):
            if ThsF10OfficersSource._looks_like_name(lines[index]) and index > start:
                return index
        return len(lines)

    @staticmethod
    def _looks_like_positions_block(lines: list[str], index: int) -> bool:
        if index >= len(lines):
            return False
        probe = lines[index]
        if "本届任期" in probe:
            return True
        return index + 1 < len(lines) and "本届任期" in lines[index + 1]

    @staticmethod
    def _looks_like_name(line: str) -> bool:
        candidate = line.lstrip("#").strip()
        if not candidate or candidate in OFFICERS_SECTION_TITLES:
            return False
        if any(marker in candidate for marker in ("|", "：", "报酬", "薪酬", "截止日期", "本届任期")):
            return False
        if any(marker in candidate for marker in ("，", "。", "；", "、")):
            return False
        if candidate.startswith(("注：", "姓名", "性别", "职位")):
            return False
        if len(candidate) > 80:
            return False
        return bool(re.search(r"[\u4e00-\u9fffA-Za-z]", candidate))

    @staticmethod
    def _is_boilerplate(line: str) -> bool:
        return line.startswith("注：") or line.startswith("## ") or line.startswith("### ")

    @staticmethod
    def _clean_name(value: str) -> str:
        return value.lstrip("#").strip()

    @staticmethod
    def _text_lines(soup: BeautifulSoup) -> list[str]:
        lines: list[str] = []
        for raw in soup.get_text("\n", strip=True).splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("加入自选股"):
                continue
            lines.append(line)
        return lines

    @staticmethod
    def _extract_company_name(soup: BeautifulSoup) -> str | None:
        for selector in ("h1", "title"):
            node = soup.find(selector)
            if node is None:
                continue
            text = " ".join(node.stripped_strings).strip()
            if not text:
                continue
            text = re.split(r"(?:\(|（|_F10|高管介绍|高管简介|董事介绍)", text, maxsplit=1)[0].strip()
            text = re.sub(r"\s*\(?HK?\d{3,5}\)?$", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"\s+\d{3,5}$", "", text).strip()
            if text:
                return text
        return None

    def _unavailable_response(
        self,
        normalized: str,
        source_url: str,
        *,
        message: str,
        company_name: str | None = None,
    ) -> OfficersResponse:
        return OfficersResponse(
            metadata=OfficersMetadata(
                code=normalized,
                name=company_name,
                source_name=OFFICERS_SOURCE_NAME,
                source_url=source_url,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                officers_count=0,
                source_status="unavailable",
            ),
            officers=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "OFFICERS_SOURCE_UNAVAILABLE",
                    message,
                )
            ],
        )

    @staticmethod
    def _build_source_url(normalized: str) -> str:
        compact = normalized.lstrip("0") or "0"
        return OFFICERS_SOURCE_URL_TEMPLATE.format(code=compact)


def _parse_date(value: str | None) -> date | None:
    if not value or value.strip() in {"--", "-"}:
        return None
    text = value.strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            return None
