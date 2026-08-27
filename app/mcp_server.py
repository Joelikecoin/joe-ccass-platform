from datetime import date
from base64 import b64encode
import json

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

from app.api import (
    _build_ccass_markdown_report,
    _history_snapshot_payload,
    _history_summary_payload,
    _rainbow_csv_bytes,
)
from app.config import get_settings
from app.friend_clone_app import _build_bundle, _bundle_markdown
from app.errors import PlatformError
from app.streamlit_ui import build_section_csv_artifact
from app.services.ai_read_model import get_ai_read_model_service
from app.services.announcements import get_announcements_service
from app.services.big_changes import get_big_changes_service
from app.services.ccass import get_ccass_service
from app.services.capital_information import get_capital_information_service
from app.services.changes import get_changes_service
from app.services.concentration import get_concentration_service
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
async def get_holdings(code: str, holdings_limit: int = 15) -> dict:
    """Return the canonical holdings payload for a Hong Kong stock code."""
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
async def get_snapshot_history(code: str, include_partial: bool = False) -> dict:
    """Return the available persisted snapshot dates for a Hong Kong stock code."""
    normalized = normalize_stock_code(code)
    repository = NormalizedSnapshotRepository(get_ccass_service().settings.ccass_sqlite_path)
    return _history_summary_payload(
        normalized,
        repository,
        include_partial=include_partial,
    )


@mcp.tool
async def get_snapshot_history_snapshots(code: str, include_partial: bool = False) -> dict:
    """Return the persisted snapshot payloads for a Hong Kong stock code."""
    normalized = normalize_stock_code(code)
    repository = NormalizedSnapshotRepository(get_ccass_service().settings.ccass_sqlite_path)
    return _history_snapshot_payload(
        normalized,
        repository,
        include_partial=include_partial,
    )


@mcp.tool
async def get_changes(
    code: str,
    snapshot_date: date,
    compare_date: date,
) -> dict:
    """Return participant movement changes for a Hong Kong stock code."""
    result = get_changes_service().get_changes(
        code,
        snapshot_date=snapshot_date,
        compare_date=compare_date,
    )
    return result.model_dump(mode="json")


@mcp.tool
async def get_big_changes(
    code: str,
    snapshot_date: date,
    compare_date: date,
    threshold_shares: int | None = None,
) -> dict:
    """Return threshold-based big changes for a Hong Kong stock code."""
    result = get_big_changes_service().get_big_changes(
        code,
        snapshot_date=snapshot_date,
        compare_date=compare_date,
        threshold_shares=threshold_shares,
    )
    return result.model_dump(mode="json")


@mcp.tool
async def get_concentration(
    code: str,
    snapshot_date: date,
    top_holders_limit: int = 10,
) -> dict:
    """Return concentration metrics for a Hong Kong stock code."""
    result = get_concentration_service().get_concentration(
        code,
        snapshot_date=snapshot_date,
        top_holders_limit=top_holders_limit,
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
async def get_download_artifact(
    code: str,
    section: str,
    kind: str,
    locale: str = "en",
    holdings_limit: int = 20,
    big_change_threshold: int = 1_000_000,
    source_mode: str = "auto",
    use_local_history: bool = True,
) -> dict:
    """Return a canonical downloadable artifact for a Hong Kong stock code."""
    bundle = await _build_bundle(
        raw_code=code,
        input_type="Stock Code",
        source_mode=source_mode,
        top_n=holdings_limit,
        big_change_threshold=big_change_threshold,
        use_local_history=use_local_history,
    )
    if section == "live":
        if bundle.live_artifacts is None:
            raise PlatformError("NOT_FOUND", "Live product artifacts are unavailable.", status_code=404)
        if kind == "csv":
            payload = bundle.live_artifacts.combined_csv_bytes
            filename = bundle.live_artifacts.combined_csv_filename
            media_type = "text/csv"
        elif kind == "xlsx":
            payload = bundle.live_artifacts.workbook_bytes
            filename = bundle.live_artifacts.workbook_filename
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif kind == "json":
            payload = bundle.live_artifacts.json_bytes
            filename = bundle.live_artifacts.json_filename
            media_type = "application/json"
        elif kind == "md":
            payload = _bundle_markdown(bundle, "live", locale).encode("utf-8")
            filename = f"{bundle.resolved_code}_live_markdown.md"
            media_type = "text/markdown; charset=utf-8"
        else:
            raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)
    elif section == "ccass":
        if bundle.ccass_artifacts is None or bundle.prepared is None:
            raise PlatformError("NOT_FOUND", "CCASS artifacts are unavailable.", status_code=404)
        if kind == "csv":
            payload = bundle.ccass_artifacts.combined_csv_bytes
            filename = bundle.ccass_artifacts.combined_csv_filename
            media_type = "text/csv"
        elif kind == "xlsx":
            payload = bundle.ccass_artifacts.workbook_bytes
            filename = bundle.ccass_artifacts.workbook_filename
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif kind == "json":
            payload = bundle.prepared.response.model_dump_json(indent=2).encode("utf-8")
            filename = f"{bundle.prepared.response.metadata.code}_ccass.json"
            media_type = "application/json"
        elif kind == "md":
            payload = _bundle_markdown(bundle, "ccass", locale).encode("utf-8")
            filename = bundle.prepared.filename
            media_type = "text/markdown; charset=utf-8"
        elif kind == "sqlite":
            sqlite_path = get_settings().ccass_sqlite_path
            if not sqlite_path.is_file():
                raise PlatformError("NOT_FOUND", "SQLite backup is unavailable.", status_code=404)
            payload = sqlite_path.read_bytes()
            filename = sqlite_path.name
            media_type = "application/x-sqlite3"
        else:
            raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)
    elif section == "rainbow":
        rainbow_payload = await get_rainbow_data(code)
        if kind == "json":
            payload = json.dumps(rainbow_payload, ensure_ascii=False, indent=2).encode("utf-8")
            filename = f"{normalize_stock_code(code)}_rainbow.json"
            media_type = "application/json"
        elif kind == "csv":
            payload = _rainbow_csv_bytes(rainbow_payload)
            filename = f"{normalize_stock_code(code)}_rainbow.csv"
            media_type = "text/csv"
        else:
            raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)
    elif section in {"holdings", "changes", "big_changes", "concentration", "announcements", "price_history"}:
        if bundle.prepared is None:
            raise PlatformError("NOT_FOUND", f"{section} artifacts are unavailable.", status_code=404)
        if kind == "csv":
            payload, filename = build_section_csv_artifact(bundle.prepared.response, section)
            media_type = "text/csv"
        else:
            raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)
    elif section == "raw_previews":
        if bundle.ccass_artifacts is None or bundle.prepared is None:
            raise PlatformError("NOT_FOUND", "Raw preview artifacts are unavailable.", status_code=404)
        if kind == "json":
            payload = bundle.ccass_artifacts.raw_preview_json_bytes
            filename = bundle.ccass_artifacts.raw_preview_json_filename
            media_type = "application/json"
        elif kind == "summary_csv":
            payload = bundle.ccass_artifacts.raw_preview_summary_bytes
            filename = bundle.ccass_artifacts.raw_preview_summary_filename
            media_type = "text/csv"
        elif kind == "holdings_csv":
            payload = bundle.ccass_artifacts.raw_preview_holdings_bytes
            filename = bundle.ccass_artifacts.raw_preview_holdings_filename
            media_type = "text/csv"
        else:
            raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)
    else:
        raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)
    return {
        "section": section,
        "kind": kind,
        "filename": filename,
        "media_type": media_type,
        "content_b64": b64encode(payload).decode("ascii"),
        "content_length": len(payload),
    }


@mcp.tool
async def get_raw_previews(
    code: str,
    locale: str = "en",
    holdings_limit: int = 20,
    big_change_threshold: int = 1_000_000,
    source_mode: str = "auto",
    use_local_history: bool = True,
) -> dict:
    """Return the canonical raw preview tables for a Hong Kong stock code."""
    bundle = await _build_bundle(
        raw_code=code,
        input_type="Stock Code",
        source_mode=source_mode,
        top_n=holdings_limit,
        big_change_threshold=big_change_threshold,
        use_local_history=use_local_history,
    )
    if bundle.ccass_artifacts is None or bundle.prepared is None:
        raise PlatformError("NOT_FOUND", "Raw preview artifacts are unavailable.", status_code=404)
    payload = json.loads(bundle.ccass_artifacts.raw_preview_json_bytes.decode("utf-8"))
    return {
        "stock_code": bundle.resolved_code,
        "locale": locale,
        **payload,
    }


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


for _tool in (
    get_ccass_stock_data,
    get_stock_summary,
    get_holdings,
    get_price_history,
    get_snapshot_history,
    get_snapshot_history_snapshots,
    get_changes,
    get_big_changes,
    get_concentration,
    get_rainbow_data,
    get_announcements,
    get_full_report,
    get_source_status,
    get_download_artifact,
    get_raw_previews,
    get_officers,
    get_stock_events,
    get_capital_information,
    get_ai_read_model,
):
    setattr(_tool, "fn", _tool)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001, path="/mcp")
