"""Pure parser for the approved Webb-site latest Holdings HTML shape."""

import re
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup, Tag

from app.core.normalizers import classify_participant, parse_float, parse_int, parse_iso_date
from app.errors import ErrorCode, PlatformError
from app.models import HoldingRow, HoldingsSummary

WEBBSITE_PARSER_ID = "webbsite-holdings"
WEBBSITE_PARSER_VERSION = "2"
WEBBSITE_SCHEMA_VERSION = "ccass-response-v1"

_DATE_PATTERN = re.compile(r"CCASS holdings on \d{4}-\d{2}-\d{2}", re.IGNORECASE)
_PARTICIPANT_ID_PATTERN = re.compile(r"[A-Z]\d{5}")
_SUMMARY_LABELS = (
    "Total in CCASS",
    "Issued securities",
    "Securities not in CCASS",
)


@dataclass(frozen=True, slots=True)
class ParsedWebbsiteHoldings:
    code: str
    name: str | None
    issue_id: int
    holdings_date: date | None
    holdings_summary: HoldingsSummary
    holdings: tuple[HoldingRow, ...]
    warnings: tuple[str, ...]


def parse_webbsite_holdings(html: str, *, requested_code: str) -> ParsedWebbsiteHoldings:
    """Parse one already-fetched page without settings, storage, or network access."""
    if not html or not html.strip():
        raise PlatformError(
            ErrorCode.PARSE_ERROR,
            "The Webb-site Holdings page was empty.",
        )

    soup = BeautifulSoup(html, "html.parser")
    issue_id, name = _parse_identity(soup, requested_code)
    holdings_date = _parse_snapshot_date(soup)
    summary_values = _parse_summary(soup)
    holdings = _parse_holdings_rows(soup)
    summary = _build_summary(summary_values, holdings)

    warnings: list[str] = []
    if holdings_date is None:
        warnings.append(
            "Holdings date could not be read from the source page; "
            "the latest snapshot date is unverified."
        )
    if (
        summary.total_in_ccass_pct_of_issued is not None
        and summary.total_in_ccass_pct_of_issued > 100
    ) or any(
        row.pct_of_issued > 100
        or (
            row.cumulative_pct_of_issued is not None
            and row.cumulative_pct_of_issued > 100
        )
        for row in holdings
    ):
        warnings.append(
            "A source percentage exceeds 100%; the issued-share denominator "
            "may be stale after a corporate action. Source values were preserved."
        )

    return ParsedWebbsiteHoldings(
        code=requested_code,
        name=name,
        issue_id=issue_id,
        holdings_date=holdings_date,
        holdings_summary=summary,
        holdings=tuple(holdings),
        warnings=tuple(warnings),
    )


def _parse_identity(soup: BeautifulSoup, requested_code: str) -> tuple[int, str | None]:
    code_node = soup.find(
        string=lambda value: bool(value and value.strip() == requested_code)
    )
    issue_values = {
        str(node.get("value", "")).strip()
        for node in soup.select('input[name="i"][value]')
    }

    if code_node is None or not issue_values:
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            f"No verified Webb-site Holdings identity found for stock code {requested_code}.",
            status_code=404,
        )
    if len(issue_values) != 1:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "The Webb-site Holdings page contained conflicting issue IDs.",
        )

    issue_value = next(iter(issue_values))
    if not re.fullmatch(r"[1-9]\d*", issue_value):
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            f"No valid Webb-site issue ID found for stock code {requested_code}.",
            status_code=404,
        )

    heading = soup.find("h2")
    name = heading.get_text(" ", strip=True) if heading else None
    return int(issue_value), name


def _parse_snapshot_date(soup: BeautifulSoup) -> date | None:
    date_heading = soup.find(string=lambda value: bool(value and _DATE_PATTERN.search(value)))
    if date_heading is None:
        return None
    return parse_iso_date(str(date_heading))


def _parse_summary(soup: BeautifulSoup) -> dict[str, tuple[int, float]]:
    summary_table = next(
        (
            table
            for table in soup.find_all("table")
            if all(label in table.get_text(" ", strip=True) for label in _SUMMARY_LABELS)
        ),
        None,
    )
    if summary_table is None:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "The Webb-site Holdings summary table or required fields were not found.",
        )

    values: dict[str, tuple[int, float]] = {}
    for row in summary_table.select("tr"):
        cells = _cells(row)
        if not cells or cells[0] not in _SUMMARY_LABELS:
            continue
        if len(cells) < 3:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                f"The Webb-site summary field {cells[0]!r} has changed shape.",
            )
        try:
            values[cells[0]] = (parse_int(cells[1]), parse_float(cells[2]))
        except ValueError as exc:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                f"Could not parse Webb-site summary field {cells[0]!r}.",
            ) from exc

    missing = [label for label in _SUMMARY_LABELS if label not in values]
    if missing:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "Required Webb-site summary fields were missing.",
        )
    return values


def _parse_holdings_rows(soup: BeautifulSoup) -> list[HoldingRow]:
    details_table = next(
        (
            table
            for table in soup.find_all("table")
            if "CCASS ID" in table.get_text(" ", strip=True)
            and "Cumul" in table.get_text(" ", strip=True)
        ),
        None,
    )
    if details_table is None:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "Holdings table was not found; the source page may have changed.",
        )

    rows = details_table.select("tr")
    header_index = next(
        (
            index
            for index, row in enumerate(rows)
            if "CCASS ID" in _cells(row) and any("Cumul" in cell for cell in _cells(row))
        ),
        None,
    )
    if header_index is None:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "The Webb-site Holdings header or required fields were not found.",
        )

    header = _cells(rows[header_index])
    if (
        len(header) < 7
        or "CCASS ID" not in header[1]
        or "Holding" not in header[3]
        or "Last change" not in header[4]
        or "%" not in header[5]
        or "Cumul" not in header[6]
    ):
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "The Webb-site Holdings required columns have changed.",
        )

    holdings: list[HoldingRow] = []
    for row in rows[header_index + 1 :]:
        cells = _cells(row)
        if not cells:
            continue
        if len(cells) < 7:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "A Webb-site Holdings row did not contain all required fields.",
            )
        if not cells[0].isdigit() or not _PARTICIPANT_ID_PATTERN.fullmatch(cells[1]):
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "A Webb-site Holdings row contained an invalid rank or participant ID.",
            )
        if not cells[2]:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "A Webb-site Holdings row contained an empty participant name.",
            )
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
        except ValueError as exc:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                f"Could not parse Webb-site Holdings row at rank {cells[0]}.",
            ) from exc

    if not holdings:
        raise PlatformError(
            ErrorCode.PARSE_ERROR,
            "The Holdings table was present but contained no participant rows.",
        )

    holdings.sort(key=lambda item: item.rank)
    if len({item.rank for item in holdings}) != len(holdings) or len(
        {item.participant_id for item in holdings}
    ) != len(holdings):
        raise PlatformError(
            ErrorCode.PARSE_ERROR,
            "The Webb-site Holdings table contained duplicate ranks or participant IDs.",
        )
    return holdings


def _build_summary(
    values: dict[str, tuple[int, float]],
    holdings: list[HoldingRow],
) -> HoldingsSummary:
    total_ccass = values["Total in CCASS"]
    issued = values["Issued securities"]
    non_ccass = values["Securities not in CCASS"]
    total_ccass_shares = total_ccass[0]

    def pct_of_ccass(shares: int) -> float | None:
        return (
            round(shares / total_ccass_shares * 100, 4)
            if total_ccass_shares
            else None
        )

    top5 = holdings[:5]
    top10 = holdings[:10]
    return HoldingsSummary(
        total_in_ccass_shares=total_ccass[0],
        total_in_ccass_pct_of_issued=total_ccass[1],
        issued_shares=issued[0],
        non_ccass_shares=non_ccass[0],
        non_ccass_pct_of_issued=non_ccass[1],
        participant_count=len(holdings),
        top5_pct_of_issued=top5[-1].cumulative_pct_of_issued,
        top10_pct_of_issued=top10[-1].cumulative_pct_of_issued,
        top5_pct_of_ccass=pct_of_ccass(sum(row.shares for row in top5)),
        top10_pct_of_ccass=pct_of_ccass(sum(row.shares for row in top10)),
    )


def _cells(row: Tag) -> list[str]:
    return [cell.get_text(" ", strip=True) for cell in row.select("th,td")]
