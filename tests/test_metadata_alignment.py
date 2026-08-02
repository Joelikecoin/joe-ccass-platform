from datetime import UTC, date, datetime

from app.models import ChangesSourceMetadata, SourceMetadata


def test_response_metadata_exposes_data_as_of_alias():
    source_metadata = SourceMetadata(
        code="01592",
        name="Example Holdings",
        issue_id=12345,
        holdings_date=date(2026, 8, 1),
        fetched_at=datetime(2026, 8, 1, 9, 30, tzinfo=UTC),
        source_url="https://example.invalid/ccass/holdings",
    )
    changes_metadata = ChangesSourceMetadata(
        source_id="webbsite",
        source_name="Webb-site mirror",
        safe_identifier="https://example.invalid/ccass/holdings",
        issue_id=12345,
        fetched_at=datetime(2026, 8, 1, 9, 30, tzinfo=UTC),
        parser_version="1",
        schema_version=1,
        checksum_sha256="0" * 64,
        attribution="Example attribution",
        issued_shares=1_000_000,
        issued_shares_as_of=date(2026, 7, 31),
        cached=False,
        stale=False,
        partial=False,
    )

    assert source_metadata.data_as_of == source_metadata.holdings_date
    assert changes_metadata.data_as_of == changes_metadata.issued_shares_as_of
    assert source_metadata.model_dump()["data_as_of"] == source_metadata.holdings_date
    assert changes_metadata.model_dump()["data_as_of"] == changes_metadata.issued_shares_as_of
