from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from functools import lru_cache

from app.config import get_settings
from app.models import IntelligenceEventsResponse, OwnershipTimelineResponse
from app.services.intelligence_events import IntelligenceEventsService, get_intelligence_events_service
from app.services.ownership_timeline import OwnershipTimelineService
from app.storage.document_entities import DocumentEntityRepository
from app.storage.fundamentals import FundamentalsRepository
from app.storage.history import NormalizedSnapshotRepository
from app.storage.intelligence_events import IntelligenceEventRepository
from app.storage.share_capital_history import ShareCapitalHistoryRepository
from ccass_core.normalize import normalize_stock_code

DEFAULT_LOOKBACK_DAYS = 5 * 365


class ResearchContextService:
    """Packages every persisted intelligence domain for one stock into a
    single AI-consumable research context (JSON dict + markdown rendering).
    Persisted-read-only: heavy refreshes belong to the admin jobs."""

    def __init__(
        self,
        events_service: IntelligenceEventsService | None = None,
        timeline_service: OwnershipTimelineService | None = None,
        fundamentals_repository: FundamentalsRepository | None = None,
        entity_repository: DocumentEntityRepository | None = None,
        share_capital_repository: ShareCapitalHistoryRepository | None = None,
        snapshot_repository: NormalizedSnapshotRepository | None = None,
    ):
        settings = get_settings()
        normalized_repository = snapshot_repository or NormalizedSnapshotRepository(settings.ccass_sqlite_path)
        self.events_service = events_service or get_intelligence_events_service()
        self.timeline_service = timeline_service or OwnershipTimelineService(
            DisclosureInterestRepositoryShim(normalized_repository)
        )
        self.fundamentals_repository = fundamentals_repository or FundamentalsRepository(normalized_repository)
        self.entity_repository = entity_repository or DocumentEntityRepository(normalized_repository)
        self.share_capital_repository = share_capital_repository or ShareCapitalHistoryRepository(normalized_repository)
        self.snapshot_repository = normalized_repository

    async def build(self, code: str | int, *, start_date: date | None = None, end_date: date | None = None) -> dict:
        normalized = normalize_stock_code(code)
        end = end_date or datetime.now(UTC).date()
        start = start_date or end - timedelta(days=DEFAULT_LOOKBACK_DAYS)
        warnings: list[str] = []

        events: IntelligenceEventsResponse | None = None
        try:
            events = await self.events_service.get_events(normalized, start_date=start, end_date=end)
        except Exception as exc:
            warnings.append(f"EVENTS_SECTION_FAILED:{type(exc).__name__}")
        timeline: OwnershipTimelineResponse | None = None
        try:
            timeline = await self.timeline_service.get_timeline(normalized, start_date=start, end_date=end)
        except Exception as exc:
            warnings.append(f"OWNERSHIP_SECTION_FAILED:{type(exc).__name__}")

        fundamentals = None
        try:
            fundamentals = self.fundamentals_repository.load(normalized)
        except Exception as exc:
            warnings.append(f"FUNDAMENTALS_SECTION_FAILED:{type(exc).__name__}")
        entities = []
        try:
            entities = self.entity_repository.load_rows(normalized, start_date=start, end_date=end)
        except Exception as exc:
            warnings.append(f"ENTITIES_SECTION_FAILED:{type(exc).__name__}")
        share_capital = None
        try:
            share_capital = self.share_capital_repository.load(normalized, start_date=start, end_date=end)
        except Exception as exc:
            warnings.append(f"SHARE_CAPITAL_SECTION_FAILED:{type(exc).__name__}")

        latest_snapshot = None
        try:
            latest_snapshot = self.snapshot_repository.latest(normalized)
        except Exception as exc:
            warnings.append(f"CCASS_SECTION_FAILED:{type(exc).__name__}")

        event_items = [
            {
                "event_type": event.event_type,
                "announce_date": event.announce_date.isoformat(),
                "effective_date": event.effective_date.isoformat() if event.effective_date else None,
                "shares_after": event.shares_after,
                "price": event.price,
                "counterparty": event.counterparty,
                "entity_name": event.entity_name,
                "confidence": event.confidence,
                "source_document": event.source_document,
                "source_url": event.source_url,
            }
            for event in (events.events if events else [])
        ]
        ownership_filers = [
            {
                "filer": t.filer,
                "classification": t.classification,
                "movements_count": t.movements_count,
                "increases": t.increases,
                "decreases": t.decreases,
                "latest_present_balance": t.latest_present_balance,
                "latest_percentage": t.latest_percentage,
                "movements": [
                    {
                        "event_date": m.event_date.isoformat(),
                        "direction": m.direction,
                        "change_shares": m.change_shares,
                        "present_balance": m.present_balance,
                        "percentage": m.percentage,
                        "average_price": m.average_price,
                        "reason": m.reason,
                        "filing_id": m.filing_id,
                        "source_url": m.source_url,
                    }
                    for m in t.movements
                ],
            }
            for t in (timeline.timelines if timeline else [])
        ]
        ccass = None
        if latest_snapshot is not None:
            holdings = sorted(latest_snapshot.holdings, key=lambda h: h.shares, reverse=True)
            total = sum(h.shares for h in holdings) or 1
            ccass = {
                "snapshot_date": latest_snapshot.snapshot_date.isoformat(),
                "source": str(getattr(latest_snapshot, "source", "")),
                "participants": len(holdings),
                "top10": [
                    {"participant_id": h.participant_id, "participant": str(getattr(h, "participant_name", None) or getattr(h, "participant", "") or h.participant_id), "shares": h.shares, "pct": round(h.shares / total * 100, 2)}
                    for h in holdings[:10]
                ],
            }

        coverage = {
            "events": len(event_items),
            "ownership_filers": len(ownership_filers),
            "ownership_movements": sum(f["movements_count"] for f in ownership_filers),
            "fundamentals_periods": len(fundamentals.rows) if fundamentals else 0,
            "document_entities": len(entities),
            "share_capital_rows": len(share_capital.rows) if share_capital else 0,
            "ccass_snapshot": ccass["snapshot_date"] if ccass else None,
        }

        return {
            "code": normalized,
            "generated_at": datetime.now(UTC).isoformat(),
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "events": {
                "count": events.metadata.event_count if events else 0,
                "by_type": _count_by(event_items, "event_type"),
                "by_confidence": _count_by(event_items, "confidence"),
                "items": event_items,
            },
            "ownership": {
                "filers": len(ownership_filers),
                "movements": sum(f["movements_count"] for f in ownership_filers),
                "filers_detail": ownership_filers,
            },
            "fundamentals": {
                "status": fundamentals.metadata.source_status if fundamentals else "unavailable",
                "rows": [row.model_dump(mode="json") for row in (fundamentals.rows if fundamentals else [])],
            },
            "document_entities": [
                {
                    "document_type": row.document_type,
                    "entity_type": row.entity_type,
                    "entity_name": row.entity_name,
                    "announcement_date": row.announcement_date.isoformat(),
                    "direct_source_fact": row.direct_source_fact[:300],
                    "source_url": row.source_url,
                }
                for row in entities
            ],
            "share_capital": [
                {
                    "announce_date": row.announce_date.isoformat(),
                    "shares_million": row.shares_million,
                    "shares_approx": row.shares_approx,
                    "reason": row.reason,
                    "reason_tags": row.reason_tags,
                    "change_date": row.change_date.isoformat() if row.change_date else None,
                }
                for row in (share_capital.rows if share_capital else [])
            ],
            "ccass_latest": ccass,
            "coverage": coverage,
            "data_quality_warnings": warnings,
        }

    def to_markdown(self, context: dict) -> str:
        code = context["code"]
        lines: list[str] = [
            f"# {code} — AI 研究包（5 年財技故事線素材）",
            f"生成：{context['generated_at']}｜窗口：{context['window']['start']} → {context['window']['end']}",
            "",
            "> 誠實聲明：以下全部為官方申報/官方公告抽取嘅事實，每項帶來源；覆蓋不足之處已標籤，唔好推斷缺失數據。",
            "",
            "## 1. 覆蓋總覽",
            "",
            "```",
            json_pretty(context["coverage"]),
            "```",
            "",
            "## 2. 股權披露時間線（官方 DION 申報）",
            "",
        ]
        ownership = context["ownership"]
        lines.append(f"filers={ownership['filers']}｜movements={ownership['movements']}")
        for filer in ownership["filers_detail"]:
            lines.append(
                f"\n### {filer['filer']}（{filer['classification']}）— {filer['movements_count']} 次申報（+{filer['increases']}/-{filer['decreases']}），最新 {filer['latest_present_balance']} 股（{filer['latest_percentage']}%）"
            )
            for m in filer["movements"][:30]:
                lines.append(
                    f"- {m['event_date']} {m['direction']} {m['change_shares'] or '?'} 股 → 現持 {m['present_balance']}（{m['percentage']}%）@{m['average_price'] or '?'}｜{m['reason'] or ''}｜{m['filing_id']}"
                )
            if filer["movements_count"] > 30:
                lines.append(f"- …（其餘 {filer['movements_count'] - 30} 筆見 JSON）")
        lines.append("")
        lines.append("## 3. 統一事件層")
        lines.append(
            f"\n總數 {context['events']['count']}｜類型：{context['events']['by_type']}｜信心：{context['events']['by_confidence']}"
        )
        for event in context["events"]["items"][:120]:
            lines.append(
                f"- {event['announce_date']} [{event['confidence']}] {event['event_type']}｜{event['counterparty'] or event['entity_name'] or ''}｜現持 {event['shares_after'] or ''}｜{event['source_document']}"
            )
        if context["events"]["count"] > 120:
            lines.append(f"- …（其餘 {context['events']['count'] - 120} 筆見 JSON）")
        lines.append("")
        lines.append("## 4. 基本面（官方業績文件抽取）")
        for row in context["fundamentals"]["rows"]:
            lines.append(
                f"- {row['reporting_period']}（{row['report_type']}）收入 {row['revenue']}｜純利 {row['net_profit_loss']}｜equity {row['equity']}｜OCF {row['operating_cash_flow']}｜ completeness={row['completeness_status']}"
            )
        lines.append("")
        lines.append("## 5. 企業行動文件實體（PDF 抽取）")
        for row in context["document_entities"]:
            lines.append(f"- {row['announcement_date']} [{row['entity_type']}] {row['entity_name'] or '(unnamed)'}｜{row['document_type']}｜事實：{row['direct_source_fact'][:150]}")
        lines.append("")
        lines.append("## 6. 股本變動")
        for row in context["share_capital"]:
            lines.append(f"- {row['announce_date']} 股本 {row['shares_million']}M｜{row['reason']}｜tags={row['reason_tags']}")
        lines.append("")
        lines.append("## 7. CCASS 最新快照")
        ccass = context["ccass_latest"]
        if ccass:
            lines.append(f"\n日期 {ccass['snapshot_date']}（{ccass['source']}）｜participants={ccass['participants']}")
            for entry in ccass["top10"]:
                lines.append(f"- {entry['participant'][:40]}：{entry['shares']}（{entry['pct']}%）")
        else:
            lines.append("\n無持久化快照。")
        lines.append("")
        lines.append("## 8. 資料品質警告")
        lines.append("")
        for warning in context["data_quality_warnings"]:
            lines.append(f"- {warning}")
        if not context["data_quality_warnings"]:
            lines.append("- 無")
        return "\n".join(lines)


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[str(item.get(key))] = counts.get(str(item.get(key)), 0) + 1
    return counts


def json_pretty(value: dict) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=1)


@lru_cache
def get_research_context_service() -> ResearchContextService:
    return ResearchContextService()


class DisclosureInterestRepositoryShim:
    """Adapts the normalized repository to the disclosure repo interface the
    ownership timeline expects."""

    def __init__(self, repository: NormalizedSnapshotRepository):
        from app.storage.disclosure_interests import DisclosureInterestRepository

        self._inner = DisclosureInterestRepository(repository)

    def load_rows(self, stock_code: str, *, start_date: date, end_date: date):
        return self._inner.load_rows(stock_code, start_date=start_date, end_date=end_date)
