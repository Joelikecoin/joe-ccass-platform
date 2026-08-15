"""Pure parser for the HKEX SDW CCASS holdings HTML shape."""

import re
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup, Tag

from app.core.normalizers import classify_participant, parse_float, parse_int, parse_iso_date
from app.errors import ErrorCode, PlatformError
from app.models import HoldingRow, HoldingsSummary

HKEX_SDW_PARSER_ID = "hkex-sdw-holdings"
HKEX_SDW_PARSER_VERSION = "1"
HKEX_SDW_SCHEMA_VERSION = "ccass-response-v1"

_DATE_PATTERN = re.compile(r"CCASS holdings on \d{4}-\d{2}-\d{2}", re.IGNORECASE)
_DATE_VALUE_PATTERN = re.compile(r"\d{4}[/-]\d{2}[/-]\d{2}")
_PARTICIPANT_ID_PATTERN = re.compile(r"[A-Z]\d{5}")
_SUMMARY_LABELS = (
    "Total in CCASS",
    "Issued securities",
    "Securities not in CCASS",
)
_LIVE_SUMMARY_LABELS = {
    "市場中介者",
    "不願意披露的投資者戶口持有人",
    "總數",
}


@dataclass(frozen=True, slots=True)
class ParsedHKEXSdwHoldings:
    code: str
    name: str | None
    issue_id: int
    holdings_date: date | None
    holdings_summary: HoldingsSummary
    holdings: tuple[HoldingRow, ...]
    warnings: tuple[str, ...]


def parse_hkex_sdw_holdings(html: str, *, requested_code: str) -> ParsedHKEXSdwHoldings:
    """Parse one already-fetched HKEX SDW result page."""
    if not html or not html.strip():
        raise PlatformError(
            ErrorCode.PARSE_ERROR,
            "The HKEX SDW Holdings page was empty.",
        )

    soup = BeautifulSoup(html, "html.parser")
    issue_id, name = _parse_identity(soup, requested_code)
    holdings_date = _parse_snapshot_date(soup)
    summary_values = _parse_summary(soup)
    holdings = _parse_holdings_rows(soup, total_ccass_shares=summary_values["Total in CCASS"][0])
    summary = _build_summary(summary_values, holdings, holdings_date)

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

    return ParsedHKEXSdwHoldings(
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
    stock_code_input = soup.select_one('input[name="txtStockCode"][value]')

    if code_node is None and stock_code_input is None and not issue_values:
        raise PlatformError(
            ErrorCode.NOT_FOUND,
            f"No verified HKEX SDW Holdings identity found for stock code {requested_code}.",
            status_code=404,
        )

    if len(issue_values) > 1:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "The HKEX SDW Holdings page contained conflicting issue IDs.",
        )

    heading = soup.find("h2")
    title = soup.find("title")
    name = heading.get_text(" ", strip=True) if heading else None
    if name is None and title is not None:
        name = title.get_text(" ", strip=True) or None

    if issue_values:
        issue_value = next(iter(issue_values))
        if not re.fullmatch(r"[1-9]\d*", issue_value):
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                f"No valid HKEX SDW issue ID found for stock code {requested_code}.",
                status_code=404,
            )
        return int(issue_value), name

    normalized_code = requested_code.lstrip("0") or "0"
    return int(normalized_code), name


def _parse_snapshot_date(soup: BeautifulSoup) -> date | None:
    date_heading = soup.find(string=lambda value: bool(value and _DATE_PATTERN.search(value)))
    if date_heading is None:
        original_date = soup.select_one('input[name="originalShareholdingDate"][value]')
        if original_date is not None:
            raw_value = str(original_date.get("value") or "").strip()
            if raw_value:
                normalized = raw_value.replace("/", "-")
                parsed = parse_iso_date(normalized)
                if parsed is not None:
                    return parsed
        return None
    parsed = parse_iso_date(str(date_heading))
    if parsed is not None:
        return parsed
    match = _DATE_VALUE_PATTERN.search(str(date_heading))
    if match:
        return parse_iso_date(match.group(0).replace("/", "-"))
    return None


def _parse_summary(soup: BeautifulSoup) -> dict[str, tuple[int, float]]:
    summary_root = soup.select_one("div.ccass-search-summary-table")
    values: dict[str, tuple[int, float]] = {}

    if summary_root is not None:
        rows = summary_root.select("div.ccass-search-datarow")
        if rows:
            total_ccass: int | None = None
            issued_shares: int | None = None
            total_pct: float | None = None
            for row in rows:
                category = row.select_one("div.summary-category")
                shareholding = row.select_one("div.shareholding div.value")
                participants = row.select_one("div.number-of-participants div.value")
                pct = row.select_one("div.percent-of-participants div.value")
                if category is None or shareholding is None or participants is None or pct is None:
                    continue
                label = category.get_text(" ", strip=True)
                if label not in _LIVE_SUMMARY_LABELS:
                    continue
                try:
                    shares = parse_int(shareholding.get_text(" ", strip=True))
                    percent = parse_float(pct.get_text(" ", strip=True))
                    if label == "總數":
                        total_ccass = shares
                        total_pct = percent
                    elif label == "市場中介者":
                        values["Market intermediaries"] = (shares, percent)
                    elif label == "不願意披露的投資者戶口持有人":
                        values["Non-disclosing investor account holders"] = (shares, percent)
                except ValueError as exc:
                    raise PlatformError(
                        ErrorCode.PARSE_ERROR,
                        f"Could not parse HKEX SDW summary field {label!r}.",
                    ) from exc

            remarks_value = summary_root.select_one("div.ccass-search-remarks div.summary-value")
            if remarks_value is not None:
                try:
                    issued_shares = parse_int(remarks_value.get_text(" ", strip=True))
                except ValueError as exc:
                    raise PlatformError(
                        ErrorCode.PARSE_ERROR,
                        "Could not parse HKEX SDW issued shares value.",
                    ) from exc

            if total_ccass is not None and issued_shares is not None:
                total_pct = round(total_ccass / issued_shares * 100, 4) if issued_shares else None
                non_ccass = issued_shares - total_ccass
                non_ccass_pct = round(100 - total_pct, 4) if total_pct is not None else None
                values["Total in CCASS"] = (total_ccass, total_pct if total_pct is not None else 0.0)
                values["Issued securities"] = (issued_shares, 100.0)
                values["Securities not in CCASS"] = (non_ccass, non_ccass_pct if non_ccass_pct is not None else 0.0)

        if not values:
            summary_table = next(
                (
                    table
                    for table in soup.find_all("table")
                    if all(label in table.get_text(" ", strip=True) for label in _SUMMARY_LABELS)
                ),
                None,
            )
            if summary_table is not None:
                for row in summary_table.select("tr"):
                    cells = _cells(row)
                    if not cells or cells[0] not in _SUMMARY_LABELS:
                        continue
                    if len(cells) < 3:
                        raise PlatformError(
                            ErrorCode.SOURCE_CHANGED,
                            f"The HKEX SDW summary field {cells[0]!r} has changed shape.",
                        )
                    try:
                        values[cells[0]] = (parse_int(cells[1]), parse_float(cells[2]))
                    except ValueError as exc:
                        raise PlatformError(
                            ErrorCode.PARSE_ERROR,
                            f"Could not parse HKEX SDW summary field {cells[0]!r}.",
                        ) from exc

    if not values:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "The HKEX SDW Holdings summary table or required fields were not found.",
        )

    missing = [label for label in _SUMMARY_LABELS if label not in values]
    if missing:
        raise PlatformError(
            ErrorCode.SOURCE_CHANGED,
            "Required HKEX SDW summary fields were missing.",
        )
    return values


def _parse_holdings_rows(
    soup: BeautifulSoup,
    *,
    total_ccass_shares: int | None,
) -> list[HoldingRow]:
    live_table = next(
        (
            table
            for table in soup.find_all("table")
            if "參與者編號" in table.get_text(" ", strip=True)
            and "持股量" in table.get_text(" ", strip=True)
            and "百分比" in table.get_text(" ", strip=True)
        ),
        None,
    )
    if live_table is not None:
        live_rows = live_table.select("tbody tr")
        holdings: list[HoldingRow] = []
        cumulative_pct = 0.0
        for rank, row in enumerate(live_rows, start=1):
            cells = [cell.get_text(" ", strip=True) for cell in row.select("div.mobile-list-body")]
            if len(cells) < 5:
                continue
            participant_id = cells[0]
            participant_name = cells[1]
            shares_text = cells[3]
            pct_text = cells[4]
            if not participant_id or not participant_name:
                continue
            try:
                shares = parse_int(shares_text)
                pct_of_issued = parse_float(pct_text)
            except ValueError as exc:
                raise PlatformError(
                    ErrorCode.PARSE_ERROR,
                    f"Could not parse HKEX SDW Holdings row at rank {rank}.",
                ) from exc
            cumulative_pct += pct_of_issued
            holdings.append(
                HoldingRow(
                    rank=rank,
                    participant_id=participant_id,
                    participant=participant_name,
                    shares=shares,
                    last_change=None,
                    pct_of_issued=pct_of_issued,
                    pct_of_ccass=(
                        round(shares / total_ccass_shares * 100, 6)
                        if total_ccass_shares
                        else None
                    ),
                    cumulative_pct_of_issued=round(cumulative_pct, 6),
                    participant_category=classify_participant(participant_id, participant_name),
                )
            )

        if not holdings:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "The HKEX SDW Holdings table was present but contained no participant rows.",
            )
        return holdings

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
            "The HKEX SDW Holdings header or required fields were not found.",
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
            "The HKEX SDW Holdings required columns have changed.",
        )

    holdings: list[HoldingRow] = []
    for row in rows[header_index + 1 :]:
        cells = _cells(row)
        if not cells:
            continue
        if len(cells) < 7:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "A HKEX SDW Holdings row did not contain all required fields.",
            )
        if not cells[0].isdigit() or not _PARTICIPANT_ID_PATTERN.fullmatch(cells[1]):
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "A HKEX SDW Holdings row contained an invalid rank or participant ID.",
            )
        if not cells[2]:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "A HKEX SDW Holdings row contained an empty participant name.",
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
                f"Could not parse HKEX SDW Holdings row at rank {cells[0]}.",
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
            "The HKEX SDW Holdings table contained duplicate ranks or participant IDs.",
        )
    return holdings


def _build_summary(
    values: dict[str, tuple[int, float]],
    holdings: list[HoldingRow],
    holdings_date: date | None,
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
        issued_shares_as_of=holdings_date,
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
