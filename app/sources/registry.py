"""Configuration-driven metadata and capability registry for existing sources."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, Mapping
from urllib.parse import urlsplit

from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.sources.google_drive_csv import google_drive_download_url
from app.sources.webbsite_parser import (
    WEBBSITE_PARSER_ID,
    WEBBSITE_PARSER_VERSION,
    WEBBSITE_SCHEMA_VERSION,
)

WEBBSITE_SOURCE_ID = "webbsite"
GOOGLE_DRIVE_CSV_SOURCE_ID = "google_drive_csv"
SourceMode = Literal["auto", "webbsite", "google_drive_csv"]


class SourceCapability(StrEnum):
    LATEST = "latest"
    REQUESTED_DATE = "requested-date"
    HISTORICAL = "historical"
    MANUAL_IMPORT = "manual-import"


class SourceAuditState(StrEnum):
    APPROVED = "approved"
    DISABLED = "disabled"
    UNVERIFIED = "unverified"


class SourceStatus(StrEnum):
    ACTIVE = "active"
    FALLBACK = "fallback"
    DISABLED = "disabled"
    UNVERIFIED = "unverified"


@dataclass(frozen=True, slots=True)
class SourcePolicy:
    timeout_seconds: float
    max_bytes: int
    retry_attempts: int
    minimum_interval_seconds: float
    cache_ttl_seconds: int
    cache_policy: str
    last_known_good_policy: str
    lkg_max_age_seconds: int
    max_pages: int = 1

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("source timeout must be positive")
        if (
            self.max_bytes <= 0
            or self.retry_attempts <= 0
            or self.max_pages <= 0
            or self.lkg_max_age_seconds <= 0
        ):
            raise ValueError("source size, retry, and page bounds must be positive")
        if self.minimum_interval_seconds < 0 or self.cache_ttl_seconds < 0:
            raise ValueError("source interval and cache TTL cannot be negative")


@dataclass(frozen=True, slots=True)
class SourceAudit:
    state: SourceAuditState
    audited_at: date | None
    attribution: str
    terms_review: str
    robots_review: str
    known_limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    source_id: str
    display_name: str
    priority: int
    enabled: bool
    configured: bool
    status: SourceStatus
    audit: SourceAudit
    capabilities: frozenset[SourceCapability]
    supported_sections: frozenset[str]
    fallback_eligible: bool
    parser_id: str
    parser_version: str
    schema_version: str
    policy: SourcePolicy
    safe_hostname: str | None
    disabled_reason: str | None = None

    def supports(self, capability: SourceCapability) -> bool:
        return self.enabled and capability in self.capabilities

    def safe_diagnostic(self) -> dict[str, object]:
        """Return static safe metadata without performing a network probe."""
        return {
            "source_id": self.source_id,
            "display_name": self.display_name,
            "status": self.status.value,
            "enabled": self.enabled,
            "configured": self.configured,
            "priority": self.priority,
            "capabilities": tuple(sorted(value.value for value in self.capabilities)),
            "supported_sections": tuple(sorted(self.supported_sections)),
            "fallback_eligible": self.fallback_eligible,
            "parser_id": self.parser_id,
            "parser_version": self.parser_version,
            "schema_version": self.schema_version,
            "audit_state": self.audit.state.value,
            "audit_date": self.audit.audited_at.isoformat() if self.audit.audited_at else None,
            "attribution": self.audit.attribution,
            "terms_review": self.audit.terms_review,
            "robots_review": self.audit.robots_review,
            "known_limitations": self.audit.known_limitations,
            "safe_hostname": self.safe_hostname,
            "disabled_reason": self.disabled_reason,
        }


class SourceRegistry:
    def __init__(self, sources: Mapping[str, SourceDefinition]) -> None:
        self._sources = MappingProxyType(dict(sources))

    def get(self, source_id: str) -> SourceDefinition:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise PlatformError(
                ErrorCode.SOURCE_DISABLED,
                "Requested source is not registered.",
                status_code=400,
            ) from exc

    def require(
        self,
        source_id: str,
        capability: SourceCapability,
    ) -> SourceDefinition:
        source = self.get(source_id)
        if not source.enabled:
            raise PlatformError(
                ErrorCode.SOURCE_DISABLED,
                f"Source {source_id} is unavailable: {source.disabled_reason or source.status.value}.",
                status_code=400,
            )
        if capability not in source.capabilities:
            code = (
                ErrorCode.DATE_UNAVAILABLE
                if capability
                in {
                    SourceCapability.REQUESTED_DATE,
                    SourceCapability.HISTORICAL,
                }
                else ErrorCode.SOURCE_DISABLED
            )
            raise PlatformError(
                code,
                f"Source {source_id} does not support capability {capability.value}.",
                status_code=400,
            )
        return source

    def select_holdings(self, mode: SourceMode) -> tuple[SourceDefinition, ...]:
        if mode != "auto":
            return (self.require(mode, SourceCapability.LATEST),)
        selected = tuple(
            source
            for source in sorted(self._sources.values(), key=lambda value: value.priority)
            if source.supports(SourceCapability.LATEST)
        )
        if not selected:
            raise PlatformError(
                ErrorCode.SOURCE_DISABLED,
                "No registered source can provide latest CCASS holdings.",
                status_code=503,
            )
        return selected

    def select_historical(self, mode: SourceMode) -> SourceDefinition:
        if mode != "auto":
            return self.require(mode, SourceCapability.REQUESTED_DATE)
        selected = tuple(
            source
            for source in sorted(self._sources.values(), key=lambda value: value.priority)
            if source.supports(SourceCapability.REQUESTED_DATE)
        )
        if not selected:
            raise PlatformError(
                ErrorCode.DATE_UNAVAILABLE,
                "No registered source can provide a verified requested-date snapshot.",
                status_code=400,
            )
        return selected[0]

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return tuple(
            source.safe_diagnostic()
            for source in sorted(self._sources.values(), key=lambda value: value.priority)
        )


def build_source_registry(settings: Settings) -> SourceRegistry:
    webbsite_configured, webbsite_hostname = _webbsite_configuration(settings)
    google_configured, google_hostname = _google_configuration(settings.ccass_csv_url)
    webbsite = _definition(
        source_id=WEBBSITE_SOURCE_ID,
        display_name="Webb-site mirror",
        priority=10,
        configured=webbsite_configured,
        setting_enabled=settings.webbsite_enabled,
        audit_state=SourceAuditState(settings.webbsite_audit_state),
        audit_date=settings.webbsite_audit_date,
        active_status=SourceStatus.ACTIVE,
        capabilities=frozenset({SourceCapability.LATEST}),
        fallback_eligible=False,
        parser_id=WEBBSITE_PARSER_ID,
        parser_version=WEBBSITE_PARSER_VERSION,
        schema_version=WEBBSITE_SCHEMA_VERSION,
        policy=SourcePolicy(
            timeout_seconds=settings.request_timeout_seconds,
            max_bytes=settings.webbsite_max_bytes,
            retry_attempts=settings.source_retry_attempts,
            minimum_interval_seconds=settings.min_request_interval_seconds,
            cache_ttl_seconds=settings.cache_ttl_seconds,
            cache_policy="process_memory",
            last_known_good_policy="persistent_normalized_snapshot",
            lkg_max_age_seconds=settings.holdings_lkg_max_age_seconds,
        ),
        hostname=webbsite_hostname,
        attribution="Data from Renavon/Webb-site mirror, originally compiled by Webb-site.com | CC-BY 4.0",
        terms_review="approved_existing_source_scope",
        robots_review="approved_existing_source_scope",
        limitations=(
            "latest Holdings only",
            "requested-date history is unavailable",
            "percentage values use the source page's issued-share basis",
            "persistent LKG is guarded by configured age and transient-error policy",
        ),
    )
    google = _definition(
        source_id=GOOGLE_DRIVE_CSV_SOURCE_ID,
        display_name="Google Drive CSV",
        priority=20,
        configured=google_configured,
        setting_enabled=settings.google_drive_csv_enabled,
        audit_state=SourceAuditState(settings.google_drive_csv_audit_state),
        audit_date=settings.google_drive_csv_audit_date,
        active_status=SourceStatus.FALLBACK,
        capabilities=frozenset(
            {
                SourceCapability.LATEST,
                SourceCapability.REQUESTED_DATE,
                SourceCapability.HISTORICAL,
                SourceCapability.MANUAL_IMPORT,
            }
        ),
        fallback_eligible=True,
        parser_id="google-drive-ccass-csv",
        parser_version="1",
        schema_version="ccass-csv-v1",
        policy=SourcePolicy(
            timeout_seconds=settings.request_timeout_seconds,
            max_bytes=settings.ccass_csv_max_bytes,
            retry_attempts=settings.source_retry_attempts,
            minimum_interval_seconds=settings.backfill_request_sleep_seconds,
            cache_ttl_seconds=settings.cache_ttl_seconds,
            cache_policy="process_memory",
            last_known_good_policy="persistent_normalized_snapshot",
            lkg_max_age_seconds=settings.holdings_lkg_max_age_seconds,
            max_pages=settings.backfill_max_pages,
        ),
        hostname=google_hostname,
        attribution="Configured Google Drive/CSV import",
        terms_review="approved_configured_import_scope",
        robots_review="not_applicable_no_crawling",
        limitations=(
            "imported data; Google Drive does not increase source authority",
            "capabilities require a valid configured CCASS_CSV_URL",
            "persistent normalized LKG is collector/service managed",
        ),
    )
    return SourceRegistry({webbsite.source_id: webbsite, google.source_id: google})


def _definition(
    *,
    source_id: str,
    display_name: str,
    priority: int,
    configured: bool,
    setting_enabled: bool,
    audit_state: SourceAuditState,
    audit_date: date | None,
    active_status: SourceStatus,
    capabilities: frozenset[SourceCapability],
    fallback_eligible: bool,
    parser_id: str,
    parser_version: str,
    schema_version: str,
    policy: SourcePolicy,
    hostname: str | None,
    attribution: str,
    terms_review: str,
    robots_review: str,
    limitations: tuple[str, ...],
) -> SourceDefinition:
    enabled = setting_enabled and configured and audit_state == SourceAuditState.APPROVED
    if enabled:
        status = active_status
        disabled_reason = None
        effective_capabilities = capabilities
    elif audit_state == SourceAuditState.UNVERIFIED:
        status = SourceStatus.UNVERIFIED
        disabled_reason = "audit_unverified"
        effective_capabilities = frozenset()
    else:
        status = SourceStatus.DISABLED
        if audit_state == SourceAuditState.DISABLED:
            disabled_reason = "audit_disabled"
        elif not setting_enabled:
            disabled_reason = "disabled_by_configuration"
        else:
            disabled_reason = "invalid_or_missing_configuration"
        effective_capabilities = frozenset()
    return SourceDefinition(
        source_id=source_id,
        display_name=display_name,
        priority=priority,
        enabled=enabled,
        configured=configured,
        status=status,
        audit=SourceAudit(
            state=audit_state,
            audited_at=audit_date,
            attribution=attribution,
            terms_review=terms_review,
            robots_review=robots_review,
            known_limitations=limitations,
        ),
        capabilities=effective_capabilities,
        supported_sections=frozenset({"holdings"}) if effective_capabilities else frozenset(),
        fallback_eligible=fallback_eligible,
        parser_id=parser_id,
        parser_version=parser_version,
        schema_version=schema_version,
        policy=policy,
        safe_hostname=hostname,
        disabled_reason=disabled_reason,
    )


def _webbsite_configuration(settings: Settings) -> tuple[bool, str | None]:
    hostnames: list[str] = []
    for value in (settings.webbsite_base_url, settings.webbsite_fallback_base_url):
        try:
            parsed = urlsplit(value.strip())
        except ValueError:
            return False, None
        if parsed.scheme != "https" or not parsed.hostname:
            return False, None
        hostnames.append(parsed.hostname.lower())
    return True, ",".join(hostnames)


def _google_configuration(value: str) -> tuple[bool, str | None]:
    if not value.strip():
        return False, None
    try:
        safe_url = google_drive_download_url(value)
    except PlatformError:
        return False, None
    return True, urlsplit(safe_url).hostname