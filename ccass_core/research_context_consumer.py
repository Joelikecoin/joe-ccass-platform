from __future__ import annotations

from pydantic import BaseModel, Field

from ccass_core.research_context import (
    ResearchContextCompanyContext,
    ResearchContextContractMeta,
    ResearchContextHistoricalContext,
    ResearchContextMarketContext,
    ResearchContextOwnershipContext,
    ResearchContextPackage,
    ResearchContextQualityContext,
)
from ccass_core.research_governance_bridge import (
    ResearchGovernanceContext,
    build_research_governance_context,
)
from ccass_core.research_governance_interpretation import (
    ResearchGovernanceInterpretation,
    build_research_governance_interpretation,
)
from ccass_core.source_trace import SourceTraceView


class ResearchContextConsumerView(BaseModel):
    available: bool = False
    identity: object | None = None
    ownership_context: ResearchContextOwnershipContext | None = None
    market_context: ResearchContextMarketContext | None = None
    company_context: ResearchContextCompanyContext | None = None
    historical_context: ResearchContextHistoricalContext | None = None
    quality_context: ResearchContextQualityContext | None = None
    contract_meta: ResearchContextContractMeta | None = None
    governance_context: ResearchGovernanceContext | None = None
    governance_interpretation: ResearchGovernanceInterpretation | None = None
    warnings: list[str] = Field(default_factory=list)


def build_research_context_consumer_view(
    package: ResearchContextPackage | None,
    *,
    source_trace: SourceTraceView | None = None,
) -> ResearchContextConsumerView:
    if package is None:
        return ResearchContextConsumerView()

    warnings = list(package.quality_context.warnings)
    governance_context = (
        build_research_governance_context(package, source_trace)
        if source_trace is not None
        else None
    )
    governance_interpretation = (
        build_research_governance_interpretation(
            ResearchContextConsumerView(
                available=True,
                identity=package.identity,
                ownership_context=package.ownership_context,
                market_context=package.market_context,
                company_context=package.company_context,
                historical_context=package.historical_context,
                quality_context=package.quality_context,
                contract_meta=package.contract_meta,
                governance_context=governance_context,
                warnings=warnings,
            ),
            governance_context,
        )
        if governance_context is not None
        else None
    )
    return ResearchContextConsumerView(
        available=True,
        identity=package.identity,
        ownership_context=package.ownership_context,
        market_context=package.market_context,
        company_context=package.company_context,
        historical_context=package.historical_context,
        quality_context=package.quality_context,
        contract_meta=package.contract_meta,
        governance_context=governance_context,
        governance_interpretation=governance_interpretation,
        warnings=warnings,
    )
