from datetime import date

from app.services.cross_source_intelligence import (
    Confidence,
    CrossSourceIntelligence,
    EntityRecord,
    EvidenceRef,
    EvidenceState,
    EventRecord,
    RelationshipRecord,
)


REF = EvidenceRef("hkex", "doc-1", "N-1")


def _engine() -> CrossSourceIntelligence:
    entities = (
        EntityRecord("p-1", "PERSON", "Alex Chan", "hkex", "P-1", lineage=(REF,)),
        EntityRecord("p-2", "PERSON", "Alex Chan", "hkex", "P-2", lineage=(REF,)),
    )
    securities = (
        # The same person is linked to two stocks by explicit evidence.
        __import__("app.services.cross_source_intelligence", fromlist=["SecurityRecord"]).SecurityRecord("s-1", "HK", "00001"),
        __import__("app.services.cross_source_intelligence", fromlist=["SecurityRecord"]).SecurityRecord("s-2", "HK", "00002"),
    )
    relationships = (
        RelationshipRecord("r-1", "p-1", "s-1", "PERSON_COMPANY", None, None, None, Confidence.EXACT, EvidenceState.SUPPORTED, (REF,)),
        RelationshipRecord("r-2", "p-1", "s-2", "PERSON_COMPANY", None, None, None, Confidence.SUPPORTED, EvidenceState.SUPPORTED, (REF,)),
    )
    events = (
        EventRecord("e-1", "PLACEMENT", "s-1", announcement_date=date(2025, 1, 2), evidence_state=EvidenceState.SUPPORTED, lineage=(REF,)),
        EventRecord("e-1-duplicate", "PLACEMENT", "s-1", announcement_date=date(2025, 1, 2), evidence_state=EvidenceState.SUPPORTED, lineage=(REF,)),
        EventRecord("e-2", "HOLDING_SNAPSHOT", "s-1", holdings_date=date(2025, 1, 5), evidence_state=EvidenceState.SUPPORTED, lineage=(REF,)),
    )
    return CrossSourceIntelligence(entities=entities, securities=securities, relationships=relationships, events=events)


def test_same_name_is_not_same_person_and_explicit_identity_search_is_cross_stock():
    engine = _engine()
    assert engine.resolve_entity(source_id="hkex", source_native_id="P-1", entity_type="PERSON").confidence == Confidence.EXACT
    assert engine.resolve_entity(source_id="hkex", source_native_id="missing", entity_type="PERSON").evidence_state == EvidenceState.UNKNOWN
    assert [s.stock_code for s in engine.cross_stock_search("p-1")] == ["00001", "00002"]
    assert engine.cross_stock_search("p-2") == ()


def test_timeline_dedup_and_sequence():
    engine = _engine()
    timeline = engine.unified_timeline(security_id="s-1", start=date(2025, 1, 1), end=date(2025, 1, 10))
    assert len(timeline.events) == 2
    assert timeline.duplicate_event_ids == ("e-1-duplicate",)
    sequence = engine.sequence_search(security_id="s-1", predicates=[lambda e: e.event_type == "PLACEMENT", lambda e: e.event_type == "HOLDING_SNAPSHOT"], start=date(2025, 1, 1), end=date(2025, 1, 10), max_gap_days=5)
    assert sequence.matched_event_ids == ("e-1", "e-2")
    assert sequence.evidence_state == EvidenceState.SUPPORTED


def test_calendar_trading_interval_and_fingerprint_unknown():
    calendar = CrossSourceIntelligence.interval(anchor=date(2025, 1, 4), before=1, after=1, calendar="calendar")
    trading = CrossSourceIntelligence.interval(anchor=date(2025, 1, 3), before=1, after=3, calendar="trading")
    assert len(calendar.included_dates) == 3
    assert all(day.weekday() < 5 for day in trading.included_dates)
    result = CrossSourceIntelligence.fingerprint_compare({"placement": 1, "ownership_pct": None}, {"placement": 1, "ownership_pct": 10}, lineage=(REF,))
    assert result.matched == ("placement",)
    assert result.unknown == ("ownership_pct",)
    assert result.evidence_state == EvidenceState.UNKNOWN
    assert result.label == "RESEARCH_PRIOR"
    assert result.lineage == (REF,)
