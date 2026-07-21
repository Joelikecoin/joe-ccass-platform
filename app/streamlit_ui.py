import base64
import html
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.errors import PlatformError
from app.models import CcassResponse
from ccass_core.compute import compute_analysis
from ccass_core.normalize import normalize_stock_code
from ccass_core.report import (
    build_chatgpt_copy_payload,
    build_markdown_report,
    report_filename,
)


class StockDataService(Protocol):
    async def get_stock_data(
        self, code: str | int, holdings_limit: int = 15
    ) -> CcassResponse: ...


@dataclass(frozen=True, slots=True)
class PreparedReport:
    code: str
    markdown: str
    chatgpt_payload: str
    filename: str
    response: CcassResponse | None
    fetch_error: str | None = None


async def prepare_report(
    raw_code: str,
    *,
    holdings_limit: int,
    big_change_threshold: int,
    service: StockDataService,
    previous_loader: Callable[[CcassResponse], CcassResponse | None] | None = None,
    progress: Callable[[int, str], None] | None = None,
) -> PreparedReport:
    """Fetch, compute, and render without depending on Streamlit runtime state."""
    code = normalize_stock_code(raw_code)
    _progress(progress, 15, "Validated stock code")
    try:
        _progress(progress, 30, "Fetching low-frequency CCASS source")
        response = await service.get_stock_data(code, holdings_limit=holdings_limit)
    except PlatformError as exc:
        error = f"{exc.code}: {exc.message}"
        _progress(progress, 75, "Source unavailable; building a complete diagnostic report")
        markdown = build_markdown_report(None, code=code, fetch_error=error)
        _progress(progress, 100, "Report ready with source error details")
        return PreparedReport(
            code=code,
            markdown=markdown,
            chatgpt_payload=build_chatgpt_copy_payload(markdown),
            filename=report_filename(code),
            response=None,
            fetch_error=error,
        )

    _progress(progress, 65, "Computing concentration and comparison fields")
    try:
        previous = previous_loader(response) if previous_loader else None
    except Exception as exc:
        response.data_quality_warnings.append(
            f"Previous-snapshot enrichment is unavailable ({type(exc).__name__})."
        )
        previous = None
    analysis = compute_analysis(
        response,
        previous=previous,
        big_change_threshold=big_change_threshold,
    )
    _progress(progress, 85, "Rendering Markdown report")
    markdown = build_markdown_report(response, code=code, analysis=analysis)
    _progress(progress, 100, "Report ready")
    return PreparedReport(
        code=code,
        markdown=markdown,
        chatgpt_payload=build_chatgpt_copy_payload(markdown),
        filename=report_filename(code),
        response=response,
    )


def copy_button_html(label: str, payload: str, *, element_id: str) -> str:
    """Create a clipboard button without interpolating raw report text into JavaScript."""
    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    safe_label = html.escape(label)
    safe_id = "".join(character for character in element_id if character.isalnum() or character in "-_")
    return f"""
<button id="{safe_id}" style="padding:.45rem .8rem;border-radius:.45rem;border:1px solid #888;cursor:pointer">
  {safe_label}
</button>
<span id="{safe_id}-status" style="margin-left:.5rem"></span>
<script>
document.getElementById("{safe_id}").addEventListener("click", async () => {{
  const bytes = Uint8Array.from(atob("{encoded}"), value => value.charCodeAt(0));
  const text = new TextDecoder().decode(bytes);
  const status = document.getElementById("{safe_id}-status");
  try {{
    await navigator.clipboard.writeText(text);
    status.textContent = "Copied";
  }} catch (error) {{
    status.textContent = "Use the copy icon in Raw Markdown below";
  }}
}});
</script>
""".strip()


def _progress(callback: Callable[[int, str], None] | None, value: int, label: str) -> None:
    if callback:
        callback(value, label)
