from datetime import date

try:
    from fastmcp import FastMCP
except ModuleNotFoundError:  # pragma: no cover - test environment fallback
    class FastMCP:  # type: ignore[override]
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def tool(self, func=None):
            if func is None:
                return lambda inner: inner
            return func

        def run(self, *_args, **_kwargs) -> None:
            raise RuntimeError("fastmcp is not installed")

from app.api import _build_ccass_markdown_report
from app.services.ai_read_model import get_ai_read_model_service
from app.services.announcements import get_announcements_service
from app.services.ccass import get_ccass_service
from app.services.capital_information import get_capital_information_service
from app.services.officers import get_officers_service
from app.services.price_history import get_price_history_service
from app.services.stock_events import get_stock_events_service
from app.sources.registry import build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.normalize import normalize_stock_code

mcp = FastMCP("Joe CCASS Platform")


@mcp.tool
async def get_ccass_stock_data(code: str, holdings_limit: int = 15) -> dict:
    """Return verified CCASS holdings for a Hong Kong stock code.

    The result includes source/date metadata, T+2 limitations, dual concentration
    denominators and structured warnings. The issue ID is resolved from the stock code;
    it is never guessed.
    """
    result = await get_ccass_service().get_stock_data(code, holdings_limit=holdings_limit)
    return result.model_dump(mode="json")


@mcp.tool
async def get_stock_summary(code: str, holdings_limit: int = 15) -> dict:
    """Return the canonical stock summary payload for a Hong Kong stock code."""
    result = await get_ccass_service().get_stock_data(code, holdings_limit=holdings_limit)
    return result.model_dump(mode="json")


@mcp.tool
async def get_price_history(
    code: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Return historical price records for a Hong Kong stock code."""
    result = await get_price_history_service().get_price_history(
        code,
        start_date=start_date,
        end_date=end_date,
    )
    return result.model_dump(mode="json")


@mcp.tool
async def get_rainbow_data(code: str) -> dict:
    """Return the local historical rainbow payload for a Hong Kong stock code."""
    normalized = normalize_stock_code(code)
    repository = NormalizedSnapshotRepository(get_ccass_service().settings.ccass_sqlite_path)
    dates = repository.available_dates(normalized, include_partial=False)
    if not dates:
        return {
            "status": "unavailable",
            "stock_code": normalized,
            "available": False,
            "snapshot_count": 0,
            "top_ids": [],
            "snapshots": [],
            "warnings": ["No historical snapshots are available for DT Rainbow yet."],
        }
    snapshots = repository.date_range(
        normalized,
        date_from=dates[0],
        date_to=dates[-1],
        include_partial=False,
    )
    top_ids = [row.participant_id for row in snapshots[-1].holdings[:8]]
    payload: list[dict[str, object]] = []
    for snapshot in snapshots:
        total = snapshot.issued_shares or snapshot.total_in_ccass_shares or 0
        participant_map = {holding.participant_id: holding for holding in snapshot.holdings}
        stacks: list[dict[str, object]] = []
        remainder = 0.0
        for participant_id in top_ids:
            holding = participant_map.get(participant_id)
            shares = float(holding.shares if holding else 0)
            pct = (shares / total * 100) if total else 0.0
            stacks.append(
                {
                    "participant_id": participant_id,
                    "participant": holding.participant_name if holding else participant_id,
                    "pct": pct,
                }
            )
        for holding in snapshot.holdings:
            if holding.participant_id not in top_ids:
                remainder += float(holding.shares)
        payload.append(
            {
                "date": snapshot.snapshot_date.isoformat(),
                "stacks": [
                    *stacks,
                    {
                        "participant_id": "others",
                        "participant": "Others",
                        "pct": (remainder / total * 100) if total else 0.0,
                    },
                ],
                "participant_count": snapshot.participant_count,
                "source_name": snapshot.source.display_name,
            }
        )
    return {
        "status": "ok",
        "stock_code": normalized,
        "available": True,
        "snapshot_count": len(snapshots),
        "earliest_snapshot_date": dates[0].isoformat(),
        "latest_snapshot_date": dates[-1].isoformat(),
        "top_ids": top_ids,
        "snapshots": payload,
        "warnings": [],
    }


@mcp.tool
async def get_announcements(
    code: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Return HKEXnews announcements for a Hong Kong stock code."""
    result = await get_announcements_service().get_announcements(
        code,
        start_date=start_date,
        end_date=end_date,
    )
    return result.model_dump(mode="json")


@mcp.tool
async def get_full_report(
    code: str,
    holdings_limit: int = 20,
    big_change_threshold: int = 1_000_000,
) -> dict:
    """Return the canonical full markdown report for a Hong Kong stock code."""
    service = get_ccass_service()
    report = await _build_ccass_markdown_report(
        code,
        holdings_limit=holdings_limit,
        big_change_threshold=big_change_threshold,
        announcements_service=get_announcements_service(),
        stock_events_service=get_stock_events_service(),
        capital_information_service=get_capital_information_service(),
        officers_service=get_officers_service(),
        service=service,
    )
    return {"markdown": report}


@mcp.tool
async def get_source_status() -> dict:
    """Return the safe source registry diagnostics."""
    registry = build_source_registry(get_ccass_service().settings)
    sources = list(registry.diagnostics())
    return {"status": "ok", "source_count": len(sources), "sources": sources}


@mcp.tool
async def get_officers(code: str) -> dict:
    """Return officer data for a Hong Kong stock code.

    The current build exposes a placeholder officers slice while the source
    boundary is awaiting a confirmed live data path.
    """
    result = await get_officers_service().get_officers(code)
    return result.model_dump(mode="json")


@mcp.tool
async def get_stock_events(code: str) -> dict:
    """Return stock event data for a Hong Kong stock code.

    The current build exposes a placeholder stock-events slice while the source
    boundary is awaiting a confirmed live data path.
    """
    result = await get_stock_events_service().get_stock_events(code)
    return result.model_dump(mode="json")


@mcp.tool
async def get_capital_information(code: str) -> dict:
    """Return capital information data for a Hong Kong stock code.

    The current build exposes a placeholder capital-information slice while the source
    boundary is awaiting a confirmed live data path.
    """
    result = await get_capital_information_service().get_capital_information(code)
    return result.model_dump(mode="json")


@mcp.tool
async def get_ai_read_model(code: str) -> dict:
    """Return the normalized AI read model for a Hong Kong stock code."""
    result = await get_ai_read_model_service().get_read_model(code)
    return result.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001, path="/mcp")
