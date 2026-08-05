from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from app.data_quality import structured_warning
from app.models import (
    CapitalInformationResponse,
    OfficersResponse,
    StockEventsResponse,
)

OFFICERS_VALIDATION_PREFIX = "OFFICERS_VALIDATION"
STOCK_EVENTS_VALIDATION_PREFIX = "STOCK_EVENTS_VALIDATION"
CAPITAL_INFORMATION_VALIDATION_PREFIX = "CAPITAL_INFORMATION_VALIDATION"

_CAPITAL_EXPECTED_UNITS = {
    "Total shares": {"股"},
    "Board lot size": {"股"},
    "Diluted ROE": {"%"},
    "Debt ratio": {"%"},
}


def validate_officers_response(response: OfficersResponse) -> OfficersResponse:
    if response.metadata.source_status != "ready":
        return response
    result = response.model_copy(deep=True)
    warnings = list(result.data_quality_warnings)
    invalid_rows = 0
    for index, row in enumerate(result.officers, start=1):
        row_invalid = False
        if not _has_text(row.name):
            row_invalid = True
            warnings.append(
                structured_warning(
                    OFFICERS_VALIDATION_PREFIX,
                    "OFFICERS_NAME_MISSING",
                    f"Officer row {index} is missing a stable name.",
                )
            )
        if not _non_empty_items(row.positions):
            row_invalid = True
            warnings.append(
                structured_warning(
                    OFFICERS_VALIDATION_PREFIX,
                    "OFFICERS_POSITION_MISSING",
                    f"Officer row {index} is missing a stable position list.",
                )
            )
        if row_invalid:
            invalid_rows += 1
    if invalid_rows:
        warnings.append(
            structured_warning(
                OFFICERS_VALIDATION_PREFIX,
                "OFFICERS_INVALID_ROW",
                f"{invalid_rows} officer row(s) failed completeness validation.",
            )
        )
    result.data_quality_warnings = list(dict.fromkeys(warnings))
    return result


def validate_stock_events_response(response: StockEventsResponse) -> StockEventsResponse:
    if response.metadata.source_status != "ready":
        return response
    result = response.model_copy(deep=True)
    warnings = list(result.data_quality_warnings)
    invalid_rows = 0
    for index, row in enumerate(result.stock_events, start=1):
        row_invalid = False
        if not isinstance(row.event_date, date):
            row_invalid = True
            warnings.append(
                structured_warning(
                    STOCK_EVENTS_VALIDATION_PREFIX,
                    "STOCK_EVENTS_EVENT_DATE_INVALID",
                    f"Stock event row {index} has an invalid event date.",
                )
            )
        if not _has_text(row.title):
            row_invalid = True
            warnings.append(
                structured_warning(
                    STOCK_EVENTS_VALIDATION_PREFIX,
                    "STOCK_EVENTS_TITLE_MISSING",
                    f"Stock event row {index} is missing a stable title.",
                )
            )
        if row_invalid:
            invalid_rows += 1
    if invalid_rows:
        warnings.append(
            structured_warning(
                STOCK_EVENTS_VALIDATION_PREFIX,
                "STOCK_EVENTS_INVALID_ROW",
                f"{invalid_rows} stock event row(s) failed validation.",
            )
        )
    result.data_quality_warnings = list(dict.fromkeys(warnings))
    return result


def validate_capital_information_response(
    response: CapitalInformationResponse,
) -> CapitalInformationResponse:
    if response.metadata.source_status != "ready":
        return response
    result = response.model_copy(deep=True)
    warnings = list(result.data_quality_warnings)
    rows_by_label = {row.label: row for row in result.capital_information}
    missing_labels = [label for label in _CAPITAL_EXPECTED_UNITS if label not in rows_by_label]
    for label in missing_labels:
        warnings.append(
            structured_warning(
                CAPITAL_INFORMATION_VALIDATION_PREFIX,
                "CAPITAL_INFORMATION_METRIC_MISSING",
                f"Capital information is missing {label.lower()}.",
            )
        )
    for label, row in rows_by_label.items():
        expected_units = _CAPITAL_EXPECTED_UNITS.get(label)
        if expected_units is None:
            continue
        if row.value is None or not _is_numeric_text(row.value):
            warnings.append(
                structured_warning(
                    CAPITAL_INFORMATION_VALIDATION_PREFIX,
                    "CAPITAL_INFORMATION_NUMERIC_VALUE_INVALID",
                    f"Capital information row '{label}' has a non-numeric value.",
                )
            )
        if row.unit is not None and row.unit not in expected_units:
            warnings.append(
                structured_warning(
                    CAPITAL_INFORMATION_VALIDATION_PREFIX,
                    "CAPITAL_INFORMATION_UNIT_INCONSISTENT",
                    f"Capital information row '{label}' uses an unexpected unit '{row.unit}'.",
                )
            )
    result.data_quality_warnings = list(dict.fromkeys(warnings))
    return result


def _non_empty_items(values: Iterable[str]) -> list[str]:
    return [item for item in values if _has_text(item)]


def _is_numeric_text(value: str) -> bool:
    text = str(value).strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1].strip()
    if not text:
        return False
    try:
        float(text)
    except ValueError:
        return False
    return True


def _has_text(value: object) -> bool:
    return bool(str(value).strip())
