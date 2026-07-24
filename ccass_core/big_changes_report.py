"""Stable Markdown delivery for the Big Changes product response."""

from app.models import BigChangesResponse


def build_big_changes_markdown_report(response: BigChangesResponse) -> str:
    metadata = response.metadata
    summary = response.summary
    lines = [
        f"# CCASS Big Changes — {metadata.code}",
        "",
        "## Comparison Metadata",
        "",
        f"- Compare date: {metadata.compare_date}",
        f"- Snapshot date: {metadata.snapshot_date}",
        f"- Threshold: {summary.threshold_shares:,} shares (absolute, inclusive)",
        f"- Percentage basis: {metadata.percentage_basis}",
        f"- Compare source: {_escape(metadata.compare_source.source_name)} "
        f"({metadata.compare_source.source_id})",
        f"- Snapshot source: {_escape(metadata.snapshot_source.source_name)} "
        f"({metadata.snapshot_source.source_id})",
        f"- Compare issued shares: {metadata.compare_source.issued_shares:,} "
        f"(as of {metadata.compare_source.issued_shares_as_of})",
        f"- Snapshot issued shares: {metadata.snapshot_source.issued_shares:,} "
        f"(as of {metadata.snapshot_source.issued_shares_as_of})",
        f"- Issue ID: {metadata.issue_id}",
        f"- Settlement note: {_escape(metadata.settlement_note)}",
        "",
        "## Big Changes Summary",
        "",
        f"- Participants compared: {summary.participants_compared}",
        f"- Changed participants considered: {summary.changed_participants_considered}",
        f"- Big changes: {summary.big_changes_count}",
        "",
        "## Big Changes",
        "",
    ]
    if not response.big_changes:
        lines.append("No participant changes met the configured absolute threshold.")
    else:
        lines.extend(
            (
                "| CCASS ID | Participant | Before | After | Change | % Before | % After | pp Change | Relative Change | Status |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
            )
        )
        for row in response.big_changes:
            relative = (
                f"{row.relative_change_percent:+.4f}%"
                if row.relative_change_percent is not None
                else "DATA NOT AVAILABLE"
            )
            lines.append(
                f"| {_escape(row.participant_id)} | {_escape(row.participant)} | "
                f"{row.shares_before:,} | {row.shares_after:,} | "
                f"{row.shares_change:+,} | {row.percent_before:.4f}% | "
                f"{row.percent_after:.4f}% | {row.percent_change:+.4f} pp | "
                f"{relative} | {row.status} |"
            )
    lines.extend(["", "## Data Quality Warnings", ""])
    lines.extend(f"- {_escape(warning)}" for warning in response.data_quality_warnings)
    return "\n".join(lines).rstrip() + "\n"


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
