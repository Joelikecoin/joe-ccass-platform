from datetime import date, datetime, UTC
from types import SimpleNamespace

import pytest

from app.services.research_context import ResearchContextService


@pytest.mark.asyncio
async def test_research_context_builds_all_sections(tmp_path):
    from app.models import ShareCapitalHistoryMetadata, ShareCapitalHistoryResponse, ShareCapitalHistoryRow
    from app.storage.fundamentals import FundamentalsRepository
    from app.storage.history import NormalizedSnapshotRepository
    from app.storage.intelligence_events import IntelligenceEventRepository
    from app.storage.share_capital_history import ShareCapitalHistoryRepository as SCRepo

    repo = NormalizedSnapshotRepository(tmp_path / "rc.sqlite")
    sc_repo = SCRepo(repo)
    sc_repo.save(ShareCapitalHistoryResponse(
        metadata=ShareCapitalHistoryMetadata(code="02020", source_name="t", fetched_at=datetime.now(UTC), source_status="ready"),
        rows=[ShareCapitalHistoryRow(announce_date=date(2026, 8, 19), shares_million=10295.0, reason="results", source="HKEXnews", source_url="https://x.test/a.pdf")],
    ))

    class _Events:
        metadata = SimpleNamespace(event_count=2)

        async def get_events(self, code, *, start_date=None, end_date=None):
            return self
        events = [
            SimpleNamespace(event_type="disclosure_of_interest", announce_date=date(2026, 9, 3), effective_date=None, shares_after=100, price=None, counterparty="BlackRock, Inc.", entity_name=None, confidence="official", source_document="CS1", source_url="u"),
            SimpleNamespace(event_type="corporate_action:offeror", announce_date=date(2026, 8, 13), effective_date=None, shares_after=None, price=None, counterparty=None, entity_name="Ping An", confidence="extracted", source_document="D1", source_url="u"),
        ]
        data_quality_warnings = []

    class _Timeline:
        data_quality_warnings = []
        timelines = []

    class _TimelineService:
        async def get_timeline(self, code, *, start_date=None, end_date=None):
            return _Timeline()

    service = ResearchContextService(
        events_service=_Events(),
        timeline_service=_TimelineService(),
        fundamentals_repository=FundamentalsRepository(repo),
        entity_repository=None,
        share_capital_repository=SCRepo(repo),
        snapshot_repository=repo,
    )
    context = await service.build("02020", start_date=date(2024, 9, 19), end_date=date(2026, 9, 19))

    assert context["coverage"]["events"] == 2
    assert context["coverage"]["share_capital_rows"] == 1
    assert set(context["events"]["by_confidence"]) == {"official", "extracted"}
    md = service.to_markdown(context)
    assert "# 02020" in md
    assert "## 2. 股權披露時間線" in md
    assert "資料品質警告" in md
