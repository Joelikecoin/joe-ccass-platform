"""Stable Markdown delivery for the Concentration product response."""

from collections.abc import Sequence

from app.models import ConcentrationResponse, HoldingRow


def build_concentration_markdown_report(response: ConcentrationResponse) -> str:
    metadata = response.metadata
    summary = response.summary
    source = metadata.snapshot_source
    lines = [
        f"# CCASS Concentration — {metadata.code}",
        "",
        "## Snapshot Metadata",
        "",
        f"- Snapshot date: {metadata.snapshot_date}",
        f"- Source: {_escape(source.source_name)} ({source.source_id})",
        f"- Issue ID: {metadata.issue_id}",
        f"- Issued shares: {source.issued_shares:,} (as of {source.issued_shares_as_of})",
        f"- Percentage basis: {metadata.percentage_basis}",
        f"- Settlement note: {_escape(metadata.settlement_note)}",
        "",
        "## Concentration Summary",
        "",
        f"- Participant count: {summary.participant_count}",
        f"- Total tracked shares: {summary.total_tracked_shares:,}",
        f"- Total tracked percentage of issued shares: "
        f"{summary.total_tracked_pct_of_issued:.4f}%",
        f"- Total tracked percentage of CCASS shares: "
        f"{summary.total_tracked_pct_of_ccass:.4f}%",
        f"- Top 1: {summary.top1_pct_of_issued:.4f}% issued / "
        f"{summary.top1_pct_of_ccass:.4f}% CCASS",
        f"- Top 5: {summary.top5_pct_of_issued:.4f}% issued / "
        f"{summary.top5_pct_of_ccass:.4f}% CCASS",
        f"- Top 10: {summary.top10_pct_of_issued:.4f}% issued / "
        f"{summary.top10_pct_of_ccass:.4f}% CCASS",
        "",
        "## Top Holders",
        "",
    ]
    lines.extend(_ranking_table(response.top_holders))
    lines.extend(["", "## Participant Ranking", ""])
    lines.extend(_ranking_table(response.participant_ranking))
    lines.extend(["", "## Data Quality Warnings", ""])
    lines.extend(f"- {_escape(warning)}" for warning in response.data_quality_warnings)
    return "\n".join(lines).rstrip() + "\n"


def _ranking_table(rows: Sequence[HoldingRow]) -> list[str]:
    lines = [
        "| Rank | CCASS ID | Participant | Shares | % Issued | % CCASS |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for row in rows:
        pct_ccass = (
            f"{row.pct_of_ccass:.4f}%" if row.pct_of_ccass is not None else "DATA NOT AVAILABLE"
        )
        lines.append(
            f"| {row.rank} | {_escape(row.participant_id)} | {_escape(row.participant)} | "
            f"{row.shares:,} | {row.pct_of_issued:.4f}% | {pct_ccass} |"
        )
    return lines


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")