from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_delivery import AIResearchContextDelivery
from ccass_core.ai_research_context_historical_delivery import AIResearchContextHistoricalDelivery

AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_CONTEXT_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_CONTEXT_SURFACE = "ai_research_context_consumer_entry_context"


class AIResearchContextConsumerEntryContextContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_CONTEXT_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_CONTEXT_SURFACE


class AIResearchContextConsumerEntryContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    current_context: AIResearchContextDelivery | None = None
    historical_context: AIResearchContextHistoricalDelivery | None = None
    current_context_reference: str = "not available"
    historical_context_reference: str = "not available"
    current_context_visible: bool = False
    historical_context_visible: bool = False
    comparison_visible: bool = False
    timeline_visible: bool = False
    quality_visible: bool = False
    summary_visible: bool = False
    context_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    summary: str = "AI research context consumer entry context is unavailable."
    contract_meta: AIResearchContextConsumerEntryContextContractMeta = Field(
        default_factory=AIResearchContextConsumerEntryContextContractMeta
    )


def build_ai_research_context_consumer_entry_context(
    current_context: AIResearchContextDelivery | None,
    historical_context: AIResearchContextHistoricalDelivery | None,
    *,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_CONTEXT_SURFACE,
) -> AIResearchContextConsumerEntryContext:
    available = any(
        [
            current_context is not None and current_context.available,
            historical_context is not None and historical_context.available,
        ]
    )
    if not available:
        return AIResearchContextConsumerEntryContext(
            summary="AI research context consumer entry context is unavailable.",
            contract_meta=AIResearchContextConsumerEntryContextContractMeta(surface=surface),
        )

    current_context_visible = current_context is not None and current_context.available
    historical_context_visible = historical_context is not None and historical_context.available
    comparison_visible = bool(
        historical_context is not None and historical_context.comparison_visible
    )
    timeline_visible = bool(historical_context is not None and historical_context.timeline_visible)
    quality_visible = bool(current_context is not None and current_context.quality_visible)
    summary_visible = bool(historical_context is not None and historical_context.summary_visible)
    context_state = _context_state(
        current_context=current_context,
        historical_context=historical_context,
    )
    summary = _summary_text(
        current_context=current_context,
        historical_context=historical_context,
        current_context_visible=current_context_visible,
        historical_context_visible=historical_context_visible,
        comparison_visible=comparison_visible,
        timeline_visible=timeline_visible,
        quality_visible=quality_visible,
        summary_visible=summary_visible,
    )
    return AIResearchContextConsumerEntryContext(
        available=True,
        current_context=current_context,
        historical_context=historical_context,
        current_context_reference=(
            current_context.summary if current_context is not None and current_context.available else "not available"
        ),
        historical_context_reference=(
            historical_context.summary
            if historical_context is not None and historical_context.available
            else "not available"
        ),
        current_context_visible=current_context_visible,
        historical_context_visible=historical_context_visible,
        comparison_visible=comparison_visible,
        timeline_visible=timeline_visible,
        quality_visible=quality_visible,
        summary_visible=summary_visible,
        context_state=context_state,
        summary=summary,
        contract_meta=AIResearchContextConsumerEntryContextContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_entry_context_markdown(
    consumer_entry_context: AIResearchContextConsumerEntryContext | None,
) -> str:
    if consumer_entry_context is None or not consumer_entry_context.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Entry Context",
                "",
                "AI research context consumer entry context is unavailable.",
            ]
        )

    rows = [
        ("Current context visible", "Yes" if consumer_entry_context.current_context_visible else "No"),
        (
            "Historical context visible",
            "Yes" if consumer_entry_context.historical_context_visible else "No",
        ),
        ("Comparison visible", "Yes" if consumer_entry_context.comparison_visible else "No"),
        ("Timeline visible", "Yes" if consumer_entry_context.timeline_visible else "No"),
        ("Quality visible", "Yes" if consumer_entry_context.quality_visible else "No"),
        ("Summary visible", "Yes" if consumer_entry_context.summary_visible else "No"),
        ("Context state", consumer_entry_context.context_state),
        ("Current context reference", consumer_entry_context.current_context_reference),
        ("Historical context reference", consumer_entry_context.historical_context_reference),
        (
            "Consumer entry context contract",
            (
                f"{consumer_entry_context.contract_meta.version} / "
                f"{consumer_entry_context.contract_meta.surface}"
            ),
        ),
    ]
    lines = [
        "### AI Research Context Consumer Entry Context",
        "",
        f"*{consumer_entry_context.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _context_state(
    *,
    current_context: AIResearchContextDelivery | None,
    historical_context: AIResearchContextHistoricalDelivery | None,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    states = [
        current_context.available if current_context is not None else False,
        historical_context.available if historical_context is not None else False,
    ]
    if all(states):
        return "available"
    if any(states):
        return "partial"
    return "partial"


def _summary_text(
    *,
    current_context: AIResearchContextDelivery | None,
    historical_context: AIResearchContextHistoricalDelivery | None,
    current_context_visible: bool,
    historical_context_visible: bool,
    comparison_visible: bool,
    timeline_visible: bool,
    quality_visible: bool,
    summary_visible: bool,
) -> str:
    return (
        "AI research context consumer entry context: "
        f"current_context_visible={current_context_visible}; "
        f"historical_context_visible={historical_context_visible}; "
        f"comparison_visible={comparison_visible}; "
        f"timeline_visible={timeline_visible}; "
        f"quality_visible={quality_visible}; "
        f"summary_visible={summary_visible}; "
        f"current_context={(current_context.summary if current_context is not None else 'not available')}; "
        f"historical_context={(historical_context.summary if historical_context is not None else 'not available')}"
    )
