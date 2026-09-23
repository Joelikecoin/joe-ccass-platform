"""Deterministic Cross-Source Intelligence V1 core.

The engine is deliberately source-neutral and append-only: callers provide
already validated records and receive lineage-preserving derived views.  It
does not write a database or infer identity from names alone.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from typing import Callable, Iterable, Sequence


class EvidenceState(StrEnum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTION = "CONTRADICTION"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Confidence(StrEnum):
    EXACT = "EXACT"
    SUPPORTED = "SUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    CONTRADICTED = "CONTRADICTED"


@dataclass(frozen=True)
class EvidenceRef:
    source_id: str
    source_reference: str
    source_native_id: str | None = None
    retrieved_at: str | None = None
    observed_at: str | None = None
    artifact_sha256: str | None = None
    parser_version: str | None = None
    rule_version: str | None = None


@dataclass(frozen=True)
class EntityRecord:
    entity_id: str
    entity_type: str
    canonical_name: str
    source_id: str
    source_native_id: str | None
    valid_from: date | None = None
    valid_to: date | None = None
    observed_at: date | None = None
    confidence: Confidence = Confidence.UNRESOLVED
    status: str = "ACTIVE"
    lineage: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class SecurityRecord:
    security_id: str
    market: str
    stock_code: str
    issue_id: str | None = None
    listed_class: str | None = None
    canonical_name: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    source_mappings: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class RelationshipRecord:
    relationship_id: str
    from_entity_id: str
    to_entity_id: str
    relationship_type: str
    valid_from: date | None
    valid_to: date | None
    observed_at: date | None
    confidence: Confidence
    evidence_state: EvidenceState
    lineage: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    event_type: str
    security_id: str
    related_entity_ids: tuple[str, ...] = ()
    announcement_date: date | None = None
    effective_date: date | None = None
    completion_date: date | None = None
    settlement_date: date | None = None
    holdings_date: date | None = None
    trade_date: date | None = None
    source_observed_at: date | None = None
    evidence_state: EvidenceState = EvidenceState.UNKNOWN
    lineage: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class RuleRecord:
    rule_id: str
    lineage_type: str
    origin_case_ids: tuple[str, ...]
    origin_source_ids: tuple[str, ...]
    first_observed_at: str
    last_revalidated_at: str | None
    superseded_by: tuple[str, ...]
    supersedes: tuple[str, ...]
    validation_run_ids: tuple[str, ...]
    rule_version: str
    status: str


@dataclass(frozen=True)
class ResolutionResult:
    query: str
    candidates: tuple[EntityRecord, ...]
    confidence: Confidence
    evidence_state: EvidenceState
    missing_input_ids: tuple[str, ...] = ()
    lineage: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class TimelineResult:
    events: tuple[EventRecord, ...]
    evidence_state: EvidenceState
    duplicate_event_ids: tuple[str, ...] = ()
    lineage: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class SequenceResult:
    matched_event_ids: tuple[str, ...]
    evidence_state: EvidenceState
    missing_predicates: tuple[str, ...] = ()
    lineage: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class IntervalResult:
    anchor: date
    start: date
    end: date
    calendar: str
    included_dates: tuple[date, ...]
    evidence_state: EvidenceState
    missing_input_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FingerprintResult:
    matched: tuple[str, ...]
    unmatched_left: tuple[str, ...]
    unmatched_right: tuple[str, ...]
    unknown: tuple[str, ...]
    score: float | None
    label: str = "RESEARCH_PRIOR"
    evidence_state: EvidenceState = EvidenceState.UNKNOWN
    lineage: tuple[EvidenceRef, ...] = ()


class CrossSourceIntelligence:
    """In-memory deterministic MVP; persistence is intentionally external."""

    def __init__(
        self,
        *,
        entities: Iterable[EntityRecord] = (),
        securities: Iterable[SecurityRecord] = (),
        relationships: Iterable[RelationshipRecord] = (),
        events: Iterable[EventRecord] = (),
    ) -> None:
        self.entities = tuple(entities)
        self.securities = tuple(securities)
        self.relationships = tuple(relationships)
        self.events = tuple(events)

    def resolve_entity(self, *, source_id: str, source_native_id: str, entity_type: str) -> ResolutionResult:
        candidates = tuple(
            e for e in self.entities
            if e.source_id == source_id and e.source_native_id == source_native_id and e.entity_type == entity_type
        )
        if len(candidates) == 1:
            return ResolutionResult(source_native_id, candidates, Confidence.EXACT, EvidenceState.SUPPORTED, lineage=candidates[0].lineage)
        if len(candidates) > 1:
            return ResolutionResult(source_native_id, candidates, Confidence.AMBIGUOUS, EvidenceState.CONTRADICTION)
        return ResolutionResult(source_native_id, (), Confidence.UNRESOLVED, EvidenceState.UNKNOWN, ("source_native_id",))

    def cross_stock_search(self, entity_id: str, *, as_of: date | None = None) -> tuple[SecurityRecord, ...]:
        valid_relationships = [r for r in self.relationships if r.from_entity_id == entity_id and r.confidence in {Confidence.EXACT, Confidence.SUPPORTED} and r.evidence_state == EvidenceState.SUPPORTED]
        result: list[SecurityRecord] = []
        for rel in valid_relationships:
            if as_of is not None and ((rel.valid_from and as_of < rel.valid_from) or (rel.valid_to and as_of >= rel.valid_to)):
                continue
            result.extend(s for s in self.securities if s.security_id == rel.to_entity_id)
        return tuple(dict((s.security_id, s) for s in result).values())

    def unified_timeline(self, *, security_id: str, start: date, end: date) -> TimelineResult:
        selected = [e for e in self.events if e.security_id == security_id and _event_date(e) is not None and start <= _event_date(e) <= end]
        selected.sort(key=lambda e: (_event_date(e) or date.max, e.event_id))
        seen: dict[tuple[object, ...], EventRecord] = {}
        duplicates: list[str] = []
        for event in selected:
            key = (event.event_type, event.security_id, event.announcement_date, event.effective_date, event.completion_date, event.holdings_date, event.trade_date)
            if key in seen:
                duplicates.append(event.event_id)
                continue
            seen[key] = event
        timeline = tuple(seen.values())
        state = EvidenceState.SUPPORTED if timeline else EvidenceState.UNKNOWN
        return TimelineResult(timeline, state, tuple(duplicates), tuple(ref for e in timeline for ref in e.lineage))

    def sequence_search(self, *, security_id: str, predicates: Sequence[Callable[[EventRecord], bool]], start: date, end: date, max_gap_days: int) -> SequenceResult:
        timeline = self.unified_timeline(security_id=security_id, start=start, end=end).events
        cursor = 0; matched: list[str] = []; missing: list[str] = []; last: date | None = None
        for index, predicate in enumerate(predicates):
            found = next((event for event in timeline[cursor:] if predicate(event) and (last is None or ((_event_date(event) or date.max) - last).days <= max_gap_days)), None)
            if found is None:
                missing.append(f"predicate_{index}")
                continue
            matched.append(found.event_id); cursor = timeline.index(found) + 1; last = _event_date(found)
        state = EvidenceState.SUPPORTED if not missing else (EvidenceState.UNKNOWN if matched else EvidenceState.UNKNOWN)
        return SequenceResult(tuple(matched), state, tuple(missing), tuple(ref for e in timeline if e.event_id in matched for ref in e.lineage))

    @staticmethod
    def interval(*, anchor: date, before: int, after: int, calendar: str = "calendar") -> IntervalResult:
        if calendar not in {"calendar", "trading"}:
            raise ValueError("calendar must be calendar or trading")
        dates: list[date] = []
        for offset in range(-before, after + 1):
            current = anchor + timedelta(days=offset)
            if calendar == "calendar" or current.weekday() < 5:
                dates.append(current)
        return IntervalResult(anchor, dates[0], dates[-1], calendar, tuple(dates), EvidenceState.SUPPORTED)

    @staticmethod
    def fingerprint_compare(left: dict[str, object], right: dict[str, object], *, lineage: Iterable[EvidenceRef] = ()) -> FingerprintResult:
        keys = sorted(set(left) | set(right)); matched: list[str] = []; left_only: list[str] = []; right_only: list[str] = []; unknown: list[str] = []
        for key in keys:
            lv, rv = left.get(key), right.get(key)
            if lv is None or rv is None:
                unknown.append(key)
            elif lv == rv:
                matched.append(key)
            else:
                left_only.append(key); right_only.append(key)
        comparable = len(matched) + len(left_only)
        score = len(matched) / comparable if comparable else None
        state = EvidenceState.UNKNOWN if unknown else (EvidenceState.CONTRADICTION if left_only else EvidenceState.SUPPORTED)
        return FingerprintResult(tuple(matched), tuple(left_only), tuple(right_only), tuple(unknown), score, lineage=tuple(lineage), evidence_state=state)


def _event_date(event: EventRecord) -> date | None:
    return event.effective_date or event.completion_date or event.announcement_date or event.holdings_date or event.trade_date
