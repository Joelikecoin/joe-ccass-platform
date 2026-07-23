from datetime import datetime

from app.models import CcassResponse
from ccass_core.compute import AnalysisResult, HoldingChange

SECTION_HEADINGS = (
    "## AI Analysis Ready Summary",
    "## Fetch Summary",
    "## Metadata",
    "## Holdings Summary",
    "## Holdings",
    "## Changes",
    "## Big Changes",
    "## Concentration",
    "## Data Quality Warnings",
)
DATA_NOT_AVAILABLE = "DATA NOT AVAILABLE"
CHATGPT_COPY_HEADER = (
    "Please analyse this HK CCASS report. Treat CCASS as settlement-layer nominee data, "
    "not proof of beneficial ownership. Do not invent unavailable facts or figures."
)


def build_markdown_report(
    response: CcassResponse | None,
    *,
    code: str,
    analysis: AnalysisResult | None = None,
    fetch_error: str | None = None,
) -> str:
    """Render the complete report with all sections present in a stable order."""
    stock_name = response.metadata.name if response and response.metadata.name else DATA_NOT_AVAILABLE
    lines = [f"# CCASS Report — {code} {stock_name}", ""]

    if response is None:
        reason = fetch_error or "No source response was available."
        unavailable = f"{DATA_NOT_AVAILABLE} — {reason}"
        for heading in SECTION_HEADINGS:
            lines.extend([heading, "", unavailable, ""])
        return "\n".join(lines).rstrip() + "\n"

    computed = analysis or AnalysisResult()
    summary = response.holdings_summary
    metadata = response.metadata
    lines.extend(
        [
            SECTION_HEADINGS[0],
            "",
            _analysis_summary(response, computed),
            "",
            SECTION_HEADINGS[1],
            "",
            "- Status: SUCCESS",
            f"- Source: {_text(metadata.source_name)}",
            f"- Fetched at: {_datetime(metadata.fetched_at)}",
            f"- Holdings date: {_text(metadata.holdings_date)}",
            f"- Cached/snapshot: {'Yes' if metadata.cached else 'No'}",
            "",
            SECTION_HEADINGS[2],
            "",
            f"- Code: {metadata.code}",
            f"- Stock name: {_text(metadata.name)}",
            f"- Issue ID: {metadata.issue_id}",
            f"- Source URL: {_text(metadata.source_url)}",
            f"- Settlement note: {_text(metadata.settlement_note)}",
            f"- Attribution: {_text(metadata.attribution)}",
            "",
            SECTION_HEADINGS[3],
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Total in CCASS shares | {_integer(summary.total_in_ccass_shares)} |",
            f"| Total in CCASS / issued | {_percent(summary.total_in_ccass_pct_of_issued)} |",
            f"| Issued shares | {_integer(summary.issued_shares)} |",
            f"| Issued shares as of | {_text(summary.issued_shares_as_of)} |",
            f"| Non-CCASS shares | {_integer(summary.non_ccass_shares)} |",
            f"| Non-CCASS / issued | {_percent(summary.non_ccass_pct_of_issued)} |",
            f"| Participant count | {summary.participant_count} |",
            "",
            SECTION_HEADINGS[4],
            "",
        ]
    )
    lines.extend(_holdings_table(response))
    lines.extend(["", SECTION_HEADINGS[5], ""])
    lines.extend(_changes_section(computed))
    lines.extend(["", SECTION_HEADINGS[6], ""])
    lines.extend(_big_changes_section(computed))
    lines.extend(
        [
            "",
            SECTION_HEADINGS[7],
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Top 5 / issued | {_percent(summary.top5_pct_of_issued)} |",
            f"| Top 10 / issued | {_percent(summary.top10_pct_of_issued)} |",
            f"| Top 5 / CCASS | {_percent(summary.top5_pct_of_ccass)} |",
            f"| Top 10 / CCASS | {_percent(summary.top10_pct_of_ccass)} |",
            "",
            SECTION_HEADINGS[8],
            "",
        ]
    )
    warnings = list(computed.warnings)
    if not warnings:
        lines.append("- No additional data-quality warning was generated.")
    else:
        lines.extend(f"- {_escape(warning)}" for warning in warnings)
    return "\n".join(lines).rstrip() + "\n"


def build_chatgpt_copy_payload(report: str) -> str:
    return f"{CHATGPT_COPY_HEADER}\n\n{report.strip()}\n"


def report_filename(code: str) -> str:
    return f"{code}_ccass_report.md"


def _analysis_summary(response: CcassResponse, analysis: AnalysisResult) -> str:
    summary = response.holdings_summary
    return (
        f"Snapshot {_text(response.metadata.holdings_date)} contains "
        f"{summary.participant_count} participant rows. "
        f"Top 5 concentration is {_percent(summary.top5_pct_of_issued)} of issued shares "
        f"and {_percent(summary.top5_pct_of_ccass)} of shares held in CCASS. "
        f"Change comparison is {'available' if analysis.previous_available else 'not available'}."
    )


def _holdings_table(response: CcassResponse) -> list[str]:
    if not response.holdings:
        return [f"{DATA_NOT_AVAILABLE} — No participant rows were returned."]
    lines = [
        "| Rank | CCASS ID | Participant | Shares | Last change | % issued | % CCASS | Cumulative % | Category |",
        "|---:|---|---|---:|---|---:|---:|---:|---|",
    ]
    for row in response.holdings:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.rank),
                    _escape(row.participant_id),
                    _escape(row.participant),
                    f"{row.shares:,}",
                    _text(row.last_change),
                    _percent(row.pct_of_issued),
                    _percent(row.pct_of_ccass),
                    _percent(row.cumulative_pct_of_issued),
                    _escape(row.participant_category or DATA_NOT_AVAILABLE),
                ]
            )
            + " |"
        )
    return lines


def _changes_section(analysis: AnalysisResult) -> list[str]:
    if not analysis.previous_available:
        return [f"{DATA_NOT_AVAILABLE} — No previous snapshot was supplied for comparison."]
    lines = _change_table(analysis.changes)
    lines.extend(["", "### Possible Transfer Patterns", ""])
    if not analysis.transfer_patterns:
        lines.append(f"{DATA_NOT_AVAILABLE} — No matching transfer-like pattern was detected.")
    else:
        lines.append("Possible patterns are mechanical matches only; they do not prove ownership transfer.")
        for pattern in analysis.transfer_patterns:
            lines.append(
                f"- {_escape(pattern.from_participant)} → {_escape(pattern.to_participant)}: "
                f"approximately {pattern.approximate_shares:,} shares "
                f"(difference {pattern.difference:,})."
            )
    return lines


def _big_changes_section(analysis: AnalysisResult) -> list[str]:
    if not analysis.previous_available:
        return [f"{DATA_NOT_AVAILABLE} — No previous snapshot was supplied for comparison."]
    if not analysis.big_changes:
        return [
            f"No changes met the absolute threshold of {analysis.big_change_threshold:,} shares."
        ]
    return _change_table(analysis.big_changes)


def _change_table(changes: tuple[HoldingChange, ...]) -> list[str]:
    if not changes:
        return ["No participant-level changes were found."]
    lines = [
        "| CCASS ID | Participant | Previous | Current | Change | pp change | Status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for change in changes:
        lines.append(
            f"| {_escape(change.participant_id)} | {_escape(change.participant)} | "
            f"{change.previous_shares:,} | {change.current_shares:,} | "
            f"{change.share_change:+,} | {change.pct_point_change:+.4f} | {change.status} |"
        )
    return lines


def _integer(value: int | None) -> str:
    return f"{value:,}" if value is not None else DATA_NOT_AVAILABLE


def _percent(value: float | None) -> str:
    return f"{value:.4f}%" if value is not None else DATA_NOT_AVAILABLE


def _datetime(value: datetime | None) -> str:
    return value.isoformat() if value else DATA_NOT_AVAILABLE


def _text(value: object | None) -> str:
    return _escape(str(value)) if value is not None and str(value) else DATA_NOT_AVAILABLE


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
