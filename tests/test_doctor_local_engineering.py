from datetime import date

from app.services.cross_source_intelligence import EvidenceRef, EvidenceState, EventRecord, CrossSourceIntelligence
from app.services.job_runner import JobStore, STAGE_REGISTRY
from app.services.doctor_local_engineering import (
    DoctorLocalStore, build_fingerprint, build_historical_ccass_rows, build_interval,
    field_match_historical, normalize_ccass_code, persist_fingerprint,
    persist_historical_ccass, persist_interval, persist_sequence, query_sequence,
)


REF = EvidenceRef("archive", "archive.csv", "row-1")


def _sequence(tmp_path):
    store = DoctorLocalStore(tmp_path / "doctor.sqlite")
    result = CrossSourceIntelligence(events=(
        EventRecord("e2", "B", "s", announcement_date=date(2025, 1, 2), lineage=(REF,)),
        EventRecord("e1", "A", "s", announcement_date=date(2025, 1, 1), lineage=(REF,)),
    )).sequence_search(security_id="s", predicates=[lambda e: e.event_type == "A", lambda e: e.event_type == "B"], start=date(2025, 1, 1), end=date(2025, 1, 3), max_gap_days=3)
    return store, result


def test_sequence_build(tmp_path):
    _, result = _sequence(tmp_path)
    assert result.matched_event_ids == ("e1", "e2")


def test_sequence_query(tmp_path):
    store, result = _sequence(tmp_path); key = persist_sequence(store, security_id="s", result=result)
    assert query_sequence(store, key)["payload"]["matched_event_ids"] == ["e1", "e2"]


def test_sequence_order_validation(tmp_path):
    _, result = _sequence(tmp_path); assert result.matched_event_ids == ("e1", "e2")


def test_sequence_idempotency(tmp_path):
    store, result = _sequence(tmp_path); key = persist_sequence(store, security_id="s", result=result); persist_sequence(store, security_id="s", result=result)
    assert store.count("sequence") == 1 and query_sequence(store, key)["lineage"][0]["source_id"] == "archive"


def test_sequence_lineage(tmp_path):
    store, result = _sequence(tmp_path); key = persist_sequence(store, security_id="s", result=result, lineage=(REF,))
    assert query_sequence(store, key)["lineage"][0]["source_reference"] == "archive.csv"


def test_sequence_missing_event_unknown():
    result = CrossSourceIntelligence(events=()).sequence_search(security_id="s", predicates=[lambda e: True], start=date(2025, 1, 1), end=date(2025, 1, 2), max_gap_days=1)
    assert result.evidence_state == EvidenceState.UNKNOWN and result.missing_predicates == ("predicate_0",)


def test_calendar_interval():
    result = build_interval(anchor=date(2025, 1, 2), before=1, after=1, date_semantic="announcement")
    assert len(result.included_dates) == 3 and result.evidence_state == EvidenceState.SUPPORTED


def test_trading_interval():
    result = build_interval(anchor=date(2025, 1, 3), before=1, after=3, date_semantic="trade", calendar="trading", known_holidays=set())
    assert all(day.weekday() < 5 for day in result.included_dates) and result.evidence_state == EvidenceState.SUPPORTED


def test_interval_unknown_partial_without_holiday_knowledge():
    result = build_interval(anchor=date(2025, 1, 3), before=1, after=3, date_semantic="trade", calendar="trading")
    assert result.evidence_state == EvidenceState.UNKNOWN and "exchange_holidays" in result.missing_input_ids


def test_interval_date_semantic_distinct():
    assert build_interval(anchor=date(2025, 1, 2), before=0, after=0, date_semantic="effective").included_dates == (date(2025, 1, 2),)


def test_interval_persistence(tmp_path):
    store = DoctorLocalStore(tmp_path / "doctor.sqlite"); result = build_interval(anchor=date(2025, 1, 2), before=1, after=1, date_semantic="completion"); key = persist_interval(store, result, date_semantic="completion", lineage=(REF,))
    assert store.get("interval", key)["lineage"][0]["source_id"] == "archive"


def test_fingerprint_build():
    result = build_fingerprint({"a": 1}, {"a": 1}, lineage=(REF,)); assert result.matched == ("a",)


def test_fingerprint_compare_positive():
    result = build_fingerprint({"a": 1, "b": 2}, {"a": 1, "b": 2}); assert result.evidence_state == EvidenceState.SUPPORTED and result.score == 1.0


def test_fingerprint_compare_non_match():
    result = build_fingerprint({"a": 1}, {"a": 2}); assert result.evidence_state == EvidenceState.CONTRADICTION and result.unmatched_left == ("a",)


def test_fingerprint_unknown_safety():
    result = build_fingerprint({"a": None}, {"a": 2}); assert result.evidence_state == EvidenceState.UNKNOWN and result.unknown == ("a",)


def test_fingerprint_lineage_and_persistence(tmp_path):
    store = DoctorLocalStore(tmp_path / "doctor.sqlite"); result = build_fingerprint({"a": 1}, {"a": 1}, lineage=(REF,)); key = persist_fingerprint(store, result)
    assert store.get("fingerprint", key)["lineage"][0]["source_native_id"] == "row-1"


def test_historical_schema_mapping():
    row = build_historical_ccass_rows([{"trade_date": "2025-01-02", "security_code": "388", "participant_id": "P1", "holding": 10}], source_id="webb", source_reference="archive.sql")[0]
    assert set(("trade_date", "source_security_code", "normalized_security_code", "participant_id", "holding", "source_id", "source_reference")) <= set(row)


def test_historical_normalization():
    assert normalize_ccass_code("0388") == "00388" and normalize_ccass_code(1211) == "01211"


def test_historical_field_match():
    row = build_historical_ccass_rows([{"trade_date": "2025-01-02", "security_code": "388", "participant_id": "P1", "holding": 10}], source_id="webb", source_reference="x")[0]
    assert field_match_historical(row, dict(row))["match_pass"] is True


def test_historical_idempotency(tmp_path):
    store = DoctorLocalStore(tmp_path / "doctor.sqlite"); rows = build_historical_ccass_rows([{"trade_date": "2025-01-02", "security_code": "388", "participant_id": "P1", "holding": 10}], source_id="webb", source_reference="x")
    assert persist_historical_ccass(store, rows) == 1 and persist_historical_ccass(store, rows) == 0 and store.count("historical_ccass") == 1


def test_historical_lineage_fields(tmp_path):
    store = DoctorLocalStore(tmp_path / "doctor.sqlite"); rows = build_historical_ccass_rows([{"trade_date": "2025-01-02", "security_code": "388", "participant_id": "P1", "holding": 10}], source_id="webb", source_reference="x"); persist_historical_ccass(store, rows)
    assert store.get("historical_ccass", rows[0]["natural_key"])["payload"]["source_reference"] == "x"


def test_retry_limit_regression():
    assert STAGE_REGISTRY["sequence_query"]["retry_limit"] == 3


def test_version_invalidation_regression(tmp_path):
    store = JobStore(tmp_path / "acceptance.sqlite"); job = store.create("LOCAL"); store.record_stage(job, "sequence_query", "PASS"); store.invalidate_stage(job, "sequence_query")
    assert not store.stage_passed(job, "sequence_query")
