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


class ResearchContextConsumerView(BaseModel):
    available: bool = False
    identity: object | None = None
    ownership_context: ResearchContextOwnershipContext | None = None
    market_context: ResearchContextMarketContext | None = None
    company_context: ResearchContextCompanyContext | None = None
    historical_context: ResearchContextHistoricalContext | None = None
    quality_context: ResearchContextQualityContext | None = None
    contract_meta: ResearchContextContractMeta | None = None
    warnings: list[str] = Field(default_factory=list)


def build_research_context_consumer_view(
    package: ResearchContextPackage | None,
) -> ResearchContextConsumerView:
    if package is None:
        return ResearchContextConsumerView()

    warnings = list(package.quality_context.warnings)
    return ResearchContextConsumerView(
        available=True,
        identity=package.identity,
        ownership_context=package.ownership_context,
        market_context=package.market_context,
        company_context=package.company_context,
        historical_context=package.historical_context,
        quality_context=package.quality_context,
        contract_meta=package.contract_meta,
        warnings=warnings,
    )
