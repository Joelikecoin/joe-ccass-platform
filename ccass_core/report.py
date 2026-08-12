
from __future__ import annotations

import re
import warnings
from collections.abc import Sequence

from app.data_quality import parse_warning
from app.models import (
    AnnouncementsResponse,
    CapitalInformationResponse,
    CcassResponse,
    OfficersResponse,
    PriceHistoryResponse,
    StockEventsResponse,
)
from ccass_core.compute import AnalysisResult, HoldingChange

DEFAULT_LOCALE = "zh_HK"
SUPPORTED_LOCALES = ("zh_HK", "en")

TRANSLATION_REGISTRY: dict[str, dict[str, str]] = {
    "en": {
        "locale.name.zh_HK": "Traditional Chinese (Hong Kong)",
        "locale.name.en": "English",
        "ui.app_title": "HK CCASS Shareholding Analysis Tool",
        "ui.app_caption": (
            "Low-frequency research tool. CCASS is settlement-layer nominee data, normally subject to T+2."
        ),
        "ui.jump_links_caption": "Jump links follow the report headings rendered below.",
        "ui.sidebar_header": "Options",
        "ui.sidebar_language": "Language",
        "ui.sidebar_input_type": "Input Type",
        "ui.sidebar_stock_code_issue_id": "Stock Code / Issue ID",
        "ui.sidebar_query_input_caption": "Enter a stock code for direct lookup, or switch to Webb-site Issue ID to resolve the stock code before fetching. Validation errors are shown below the form.",
        "ui.fetch_guidance_caption": "Enter a stock code or Webb-site Issue ID, then press Fetch. The app validates the input, resolves the source, and renders the report below.",
        "ui.sidebar_timeout": "Timeout",
        "ui.sidebar_big_change_threshold": "Big change threshold (shares)",
        "ui.sidebar_announcement_period": "Announcement Period",
        "ui.sidebar_source_mode": "Source Mode",
        "ui.sidebar_data_date": "Data Date",
        "ui.sidebar_history_range": "History Range",
        "ui.sidebar_top_n": "Top N",
        "ui.sidebar_percentage_basis": "Percentage Basis",
        "ui.sidebar_show_rendered_markdown": "Show rendered Markdown",
        "ui.sidebar_use_local_history": "Use local SQLite history for Changes",
        "ui.sidebar_load_price_history": "Load price history",
        "ui.sidebar_source_mode_caption": (
            "Source mode: {source_mode} | Timeout: {timeout_seconds:g}s | Announcement period: {announcement_period} | Data date: {data_date} | History range: {history_range} | Percentage basis: {percentage_basis}"
        ),
        "ui.data_source_mode": "Data source mode: {source_mode}",
        "ui.hkex_manual_verification": "HKEX SDW: manual verification only; no automated access.",
        "ui.chart_help_heading": "Chart Interpretation / Help",
        "ui.chart_help_caption": "These notes explain how to read the product charts and what to cross-check.",
        "ui.chart_help_surface_caption": "Review the four notes below before drawing any conclusion. Compare the chart pattern with holdings, announcements, and price context.",
        "ui.chart_help_rainbow_title": "Rainbow",
        "ui.chart_help_rainbow_body": "Use the stacked area chart to observe how each participant's share changes over time. Check the snapshot dates, participant color continuity, and whether the same participant remains visible across the chosen range. Do not infer buying or selling from the chart alone.",
        "ui.chart_help_concentration_title": "Concentration",
        "ui.chart_help_concentration_body": "Use concentration lines to observe how the top holders' share is distributed. Compare the line with the underlying holdings and with nearby announcements. Concentration can describe distribution; it does not prove motive or source of change.",
        "ui.chart_help_price_title": "Price",
        "ui.chart_help_price_body": "Use price history to compare market movement with dated holdings or announcements. Check volume, turnover, and the timing of changes. A price move by itself does not confirm an ownership change.",
        "ui.chart_help_announcements_title": "Announcements",
        "ui.chart_help_announcements_body": "Use official announcement dates, titles, sources, and links to align events with holdings and price movement. Links are factual references; they are not conclusions.",
        "ui.hkex_announcements_heading": "HKEX Announcements",
        "ui.hkex_announcements_caption": "Read-only surface for official announcements. Columns cover announcement date, title, source, and link when available.",
        "ui.company_information_heading": "Company Information",
        "ui.company_information_caption": "Company information sections are grouped here as expandable surfaces.",
        "ui.report_details_heading": "Report Details",
        "ui.report_details_caption": "Expandable sections keep the detailed report available without overwhelming the first view.",
        "ui.report_details_unavailable": "Full Report Detail is unavailable until a result has been fetched.",
        "ui.data_confidence_heading": "Data Confidence Snapshot",
        "ui.data_confidence_caption": "Only existing source, freshness, provenance, and warning signals are shown here.",
        "ui.data_confidence_freshness": "Freshness",
        "ui.data_confidence_provenance": "Provenance",
        "ui.data_confidence_fallback": "Fallback",
        "ui.report_flow_heading": "Report Flow",
        "ui.report_flow_caption": "Visible-first sections stay on the page; detailed and optional content stays collapsed until needed.",
        "ui.report_flow_visible_first": "Visible first",
        "ui.report_flow_collapsed_details": "Collapsed details",
        "ui.report_flow_actions": "Actions",
        "ui.report_detail_holdings_detail": "Holdings Detail",
        "ui.report_detail_historical_information": "Historical Information",
        "ui.report_detail_download_copy": "Download / Copy",
        "ui.visualization_heading": "Visualization Details",
        "ui.visualization_caption": "Historical views and optional chart controls are separated so the core report can load first.",
        "ui.rendered_markdown": "Rendered Markdown",
        "ui.rendered_markdown_caption": "Open the fully rendered report only when you need the complete Markdown view.",
        "ui.dt_rainbow_heading": "DT Rainbow",
        "ui.dt_rainbow_caption": "Optional view only. The interaction frame is available, but the calculation engine is not included in this build.",
        "ui.dt_rainbow_enable": "Enable DT Rainbow",
        "ui.dt_rainbow_generate": "Generate DT Rainbow",
        "ui.dt_rainbow_loading": "Preparing the optional DT Rainbow view...",
        "ui.dt_rainbow_unavailable": "DT Rainbow calculation is not implemented in this build.",
        "ui.hkex_announcements_count": "Announcement count",
        "ui.hkex_announcements_rows_label": "Announcement rows",
        "ui.hkex_announcements_sorting_note": "Sorted by announcement date, newest first.",
        "ui.hkex_announcements_empty": "No announcement rows are available in the approved read-only surface.",
        "ui.hkex_announcements_unavailable": "Announcement data is unavailable in the current fetch result.",
        "ui.stock_events_heading": "Stock Events",
        "ui.stock_events_caption": "Objective event records are grouped here when available.",
        "ui.stock_events_rows_label": "Stock event rows",
        "ui.stock_events_sorting_note": "Rows will be ordered by event date, newest first, when live data is available.",
        "ui.stock_events_source_ready": "Stock events source is connected.",
        "ui.stock_events_source_pending": "Stock events source is pending; the read path is wired but no live source is connected yet.",
        "ui.stock_events_empty": "No stock event rows are available in the current result.",
        "ui.stock_events_unavailable": "Stock event data is unavailable in the current fetch result.",
        "ui.capital_information_heading": "Capital Information",
        "ui.capital_information_caption": "Capital structure facts are grouped here when available.",
        "ui.capital_information_rows_label": "Capital information rows",
        "ui.capital_information_sorting_note": "Rows will be ordered by label when live data is available.",
        "ui.capital_information_source_ready": "Capital information source is connected.",
        "ui.capital_information_source_pending": "Capital information source is pending; the read path is wired but no live source is connected yet.",
        "ui.capital_information_empty": "No capital information rows are available in the current result.",
        "ui.capital_information_unavailable": "Capital information data is unavailable in the current fetch result.",
        "ui.officers_heading": "Officers",
        "ui.officers_caption": "Officer information is grouped here when available.",
        "ui.officers_source_ready": "Officers source is connected.",
        "ui.officers_unavailable": "Officer data is unavailable in the current fetch result.",
        "ui.officers_source_pending": "Officers source is pending; the read path is wired but no live source is connected yet.",
        "ui.officers_empty": "No officer rows are available in the current result.",
        "ui.officers_rows_label": "Officer rows",
        "ui.officers_sorting_note": "Rows will be ordered by current status and tenure dates when live data is available.",
        "ui.officers_table_name": "Name",
        "ui.officers_table_positions": "Positions",
        "ui.officers_table_tenure_from": "Tenure from",
        "ui.officers_table_tenure_to": "Tenure to",
        "ui.officers_table_is_current": "Current",
        "ui.officers_table_sex": "Sex",
        "ui.officers_table_age": "Age",
        "ui.officers_table_education": "Education",
        "ui.officers_table_salary": "Salary",
        "ui.officers_table_biography": "Biography",
        "ui.hkex_announcements_export_heading": "Export labels",
        "ui.hkex_announcements_export_note": "Export-related labels remain available even when announcement rows are empty.",
        "ui.hkex_announcements_export_csv_label": "CSV export",
        "ui.hkex_announcements_export_excel_label": "Excel workbook export",
        "ui.hkex_announcements_table_announcement_date": "Announcement date",
        "ui.hkex_announcements_table_title": "Title",
        "ui.hkex_announcements_table_source": "Source",
        "ui.hkex_announcements_table_link": "Link",
        "ui.stock_events_table_event_date": "Event date",
        "ui.stock_events_table_title": "Title",
        "ui.stock_events_table_type": "Type",
        "ui.stock_events_table_source": "Source",
        "ui.stock_events_table_link": "Link",
        "ui.stock_events_table_details": "Details",
        "ui.capital_information_table_label": "Label",
        "ui.capital_information_table_value": "Value",
        "ui.capital_information_table_unit": "Unit",
        "ui.capital_information_table_as_of": "As of",
        "ui.capital_information_table_source": "Source",
        "ui.capital_information_table_note": "Note",
        "ui.capital_information_table_link": "Link",
        "report.link_label": "Link",
        "ui.report_navigation_heading": "Report Navigation",
        "ui.report_navigation_caption": "Jump links follow the rendered report sections below.",
        "ui.data_quality_heading": "Data Quality / Warnings",
        "ui.data_quality_caption": "Objective warnings, unavailable states, and missing-data notes.",
        "ui.data_quality_help_caption": "These warnings describe completeness, quality, and system limitations. They are not investment advice, trading signals, or stock ratings.",
        "ui.data_quality_no_warnings": "No data quality warnings were generated.",
        "ui.data_quality_unavailable": "Data quality warnings are unavailable for this result.",
        "ui.full_summary_heading": "Full Summary",
        "ui.full_summary_caption": "總結顯示目前載入結果及可見區段的概覽。",
        "ui.full_summary_table_section": "Section",
        "ui.full_summary_table_status": "Status",
        "ui.full_summary_table_note": "Note",
        "ui.full_summary_status_available": "available",
        "ui.full_summary_status_unavailable": "unavailable",
        "ui.full_summary_unavailable": "Full Summary is unavailable until a result has been fetched.",
        "ui.full_summary_note_analysis_ready_summary": "Analysis-ready summary is available.",
        "ui.full_summary_note_fetch_summary": "Report sections and metadata are ready.",
        "ui.full_summary_note_metadata": "Source, data as of, and provenance details are available.",
        "ui.full_summary_note_company": "Code {code} / Issue ID {issue_id}",
        "ui.full_summary_note_announcements": "Announcement surface is unavailable in the current result.",
        "ui.full_summary_note_announcements_available": "{announcement_count} announcement rows are available.",
        "ui.full_summary_note_stock_events": "Stock event surface is unavailable in the current result.",
        "ui.full_summary_note_stock_events_ready": "Stock event surface is available from {source_name}.",
        "ui.full_summary_note_stock_events_pending": "Stock event surface is present but the source is still pending.",
        "ui.full_summary_note_capital_information": "Capital information surface is unavailable in the current result.",
        "ui.full_summary_note_capital_information_ready": "Capital information surface is available from {source_name}.",
        "ui.full_summary_note_capital_information_pending": "Capital information surface is present but the source is still pending.",
        "ui.full_summary_note_officers": "Officer surface is unavailable in the current result.",
        "ui.full_summary_note_officers_pending": "Officer surface is present but the source is still pending.",
        "ui.full_summary_note_officers_ready": "Officer surface is available from {source_name}.",
        "ui.full_summary_note_holdings": "{participant_count} participant rows.",
        "ui.full_summary_note_changes_available": "Previous snapshot is available.",
        "ui.full_summary_note_changes_unavailable": "Previous snapshot is unavailable.",
        "ui.full_summary_note_big_changes_available": "Thresholded change review is available.",
        "ui.full_summary_note_big_changes_unavailable": "Thresholded change review is unavailable.",
        "ui.full_summary_note_concentration": "Top 5 / issued {top5_pct_of_issued} | Top 10 / issued {top10_pct_of_issued}",
        "ui.full_summary_note_concentration_history": "{snapshot_count} dated snapshots.",
        "ui.full_summary_note_price_history": "Price history is unavailable in the current result.",
        "ui.full_summary_note_price_history_available": (
            "Price history is available from {price_date_from} to {price_date_to} via {source_name}."
        ),
        "ui.full_summary_note_price_history_unavailable": "Price history is unavailable in the current result.",
        "ui.full_summary_note_raw_previews": "{table_count} parsed tables.",
        "ui.full_summary_note_copy_functions": "Copy the report or ChatGPT payload from the current result.",
        "ui.full_summary_note_downloads": "Combined CSV, workbook, and Markdown report.",
        "ui.full_summary_note_data_quality_no_warnings": "No data quality warnings were generated.",
        "ui.full_summary_note_data_quality_warnings": "{warning_count} data quality warning(s).",
        "ui.related_context_heading": "Related context",
        "ui.related_context_caption": "Use the linked surfaces to move between adjacent report sections.",
        "ui.related_context_company": "Company context",
        "ui.related_context_movement": "Movement context",
        "ui.related_context_history": "Historical context",
        "ui.related_context_operations": "Operational context",
        "ui.research_workflow_heading": "Research Workflow",
        "ui.research_workflow_caption": "Workflow state, session metadata, and context readiness for the current research session.",
        "ui.research_workflow_unavailable": "Research workflow is unavailable until the current result has been prepared.",
        "ui.research_workflow_state": "Workflow state",
        "ui.research_workflow_state_created": "created",
        "ui.research_workflow_state_loaded": "loaded",
        "ui.research_workflow_state_ready": "ready",
        "ui.research_workflow_session_id": "Session ID",
        "ui.research_workflow_stock_code": "Stock code",
        "ui.research_workflow_created_at": "Created at",
        "ui.research_workflow_loaded_at": "Loaded at",
        "ui.research_workflow_ready_at": "Ready at",
        "ui.research_workflow_context_availability": "Context availability",
        "ui.research_workflow_context_available": "available",
        "ui.research_workflow_context_unavailable": "unavailable",
        "ui.research_workflow_package_reference": "Linked ResearchContextPackage",
        "ui.research_workflow_quality_reference": "Quality reference",
        "ui.research_workflow_freshness_reference": "Freshness reference",
        "ui.research_workflow_provenance_reference": "Provenance reference",
        "ui.research_workflow_warnings_summary": "Warnings summary",
        "ui.research_workflow_warnings_none": "No warnings.",
        "ui.research_dashboard_heading": "Research Dashboard",
        "ui.research_dashboard_caption": "A compact working view for the loaded stock, snapshot state, concentration, and next-step links.",
        "ui.research_dashboard_stock_code": "Stock code",
        "ui.research_dashboard_stock_name": "Stock name",
        "ui.research_dashboard_snapshot_date": "Snapshot date",
        "ui.research_dashboard_snapshot_count": "Snapshot count",
        "ui.research_dashboard_freshness": "Freshness",
        "ui.research_dashboard_provenance": "Provenance",
        "ui.research_dashboard_concentration": "Concentration",
        "ui.research_dashboard_comparison": "Comparison",
        "ui.research_dashboard_report_output": "Report output",
        "ui.research_dashboard_quick_links": "Quick links",
        "ui.research_dashboard_link_holdings": "Holdings detail",
        "ui.research_dashboard_link_concentration": "Concentration",
        "ui.research_dashboard_link_changes": "Changes",
        "ui.research_dashboard_link_big_changes": "Big changes",
        "ui.research_dashboard_link_copy": "Copy / Download",
        "ui.research_dashboard_link_raw_markdown": "Raw markdown",
        "ui.research_intelligence_current_state_heading": "Current CCASS situation",
        "ui.research_intelligence_current_state_body": "Use the concentration, holdings, and summary sections to understand the current state.",
        "ui.research_intelligence_changes_heading": "What changed compared with previous data?",
        "ui.research_intelligence_changes_body": "Use the Changes and Big Changes sections when a previous snapshot is available.",
        "ui.research_intelligence_deeper_look_heading": "Where should I look deeper?",
        "ui.research_intelligence_deeper_look_body": "Use the linked sections below for holder movement, thresholded changes, and concentration history.",
        "ui.all_parsed_tables_heading": "Full Report Detail",
        "ui.all_parsed_tables_caption": "The rendered report sections below follow the approved detail hierarchy.",
        "ui.chart_help_cross_check_title": "Cross-check guidance",
        "ui.chart_help_cross_check_body": "Always compare charts with the report, raw tables, and official announcement context. If data is partial or missing, rely on the warnings and avoid drawing a final conclusion.",
        "ui.input_type.stock_code": "Stock Code",
        "ui.input_type.webb_site_issue_id": "Webb-site Issue ID",
        "ui.source_mode.auto": "Auto",
        "ui.source_mode.webbsite": "Webb-site",
        "ui.source_mode.google_drive_csv": "Google Drive CSV",
        "ui.announcement_period.all": "All",
        "ui.announcement_period.7_days": "7 days",
        "ui.announcement_period.30_days": "30 days",
        "ui.announcement_period.90_days": "90 days",
        "ui.history_range.latest": "Latest",
        "ui.history_range.7_days": "7 days",
        "ui.history_range.30_days": "30 days",
        "ui.history_range.90_days": "90 days",
        "ui.history_range.custom": "Custom",
        "ui.percentage_basis.ccass": "CCASS",
        "ui.percentage_basis.issued_shares": "Issued Shares",
        "ui.fetch": "Fetch",
        "ui.validation_error_prefix": "Validation error",
        "ui.unexpected_error_prefix": "UNEXPECTED_ERROR",
        "ui.fetch_summary_remaining": "The Fetch Summary and every required report section remain available below.",
        "ui.fetch_status_running": "Fetching {source_mode} data for code {code}.",
        "ui.fetch_status_success": "Fetch complete from {source}; data as of {data_as_of}.",
        "ui.fetch_status_success_cached": "Fetch complete from cached/snapshot {source}; data as of {data_as_of}.",
        "ui.fetch_status_failure": "Fetch failed: {error}",
        "ui.progress_starting": "Starting",
        "ui.progress_validated_stock_code": "Validated stock code",
        "ui.progress_fetching_source": "Fetching low-frequency CCASS source",
        "ui.progress_source_unavailable": "Source unavailable; building a complete diagnostic report",
        "ui.progress_ready_with_error_details": "Report ready with source error details",
        "ui.progress_computing_analysis": "Computing concentration and comparison fields",
        "ui.progress_rendering_report": "Rendering Markdown report",
        "ui.progress_ready": "Report ready",
        "ui.raw_previews_heading": "Raw Previews",
        "ui.raw_previews_expander": "Parsed source tables",
        "ui.raw_previews_unavailable": "Raw previews are available after a successful fetch.",
        "ui.raw_previews_help_caption": "Open each parsed table below to inspect its index, shape, columns, and sample rows.",
        "ui.raw_previews_caption": "Inspection view for parsed source tables already present in the fetched response.",
        "ui.raw_previews_table_index": "Table Index",
        "ui.raw_previews_table_name": "Table Name",
        "ui.raw_previews_shape": "Shape",
        "ui.raw_previews_columns": "Columns",
        "ui.raw_previews_sample_rows": "Preview rows",
        "ui.raw_previews_no_sample_rows": "No preview rows available.",
        "ui.copy_for_chatgpt": "Copy for ChatGPT",
        "ui.copy_for_chatgpt_caption": "Copy the rendered report content for pasting into ChatGPT. The payload already includes the safety header and the current report text.",
        "ui.copy_report": "Copy report",
        "ui.downloads_heading": "Download This Stock",
        "ui.downloads_unavailable": "Downloads are available after a successful fetch.",
        "ui.downloads_caption": "Download the current report artifacts directly from the fetched response.",
        "ui.downloads_workflow_heading": "Export workflow",
        "ui.downloads_workflow_caption": "Choose the artifact you want to download. Combined CSV, Excel workbook, Markdown Report, and section-specific exports reuse the fetched result.",
        "ui.downloads_combined_csv": "All CCASS Data CSV",
        "ui.downloads_excel_workbook": "Excel - All Sections",
        "ui.downloads_report_markdown": "Markdown 報告",
        "ui.downloads_download_combined_csv": "Download All CCASS Data CSV",
        "ui.downloads_download_excel_workbook": "Download Excel",
        "ui.downloads_download_markdown_report": "Download Markdown Report",
        "ui.downloads_csv_preview": "CSV content preview",
        "ui.downloads_first_80_csv_lines": "First 80 CSV lines",
        "ui.downloads_section_specific": "Section-specific download controls",
        "ui.downloads_raw_preview_summary_csv": "Raw Preview Summary CSV",
        "ui.downloads_download_raw_preview_summary_csv": "Download Raw Preview Summary CSV",
        "ui.downloads_raw_preview_holdings_csv": "Raw Preview Holdings CSV",
        "ui.downloads_download_raw_preview_holdings_csv": "Download Raw Preview Holdings CSV",
        "ui.raw_markdown": "Raw Markdown",
        "ui.raw_previews_summary_title": "Parsed Holdings Summary",
        "ui.raw_previews_holdings_title": "Parsed Holdings Table",
        "ui.raw_previews_metric": "Metric",
        "ui.raw_previews_value": "Value",
        "ui.locale_name.zh_HK": "Traditional Chinese (Hong Kong)",
        "ui.locale_name.en": "English",
        "nav.fetch_summary": "Fetch Summary",
        "nav.full_summary": "Full Summary",
        "nav.all_tables": "Full Report Detail",
        "nav.dt_rainbow": "DT Rainbow",
        "nav.hkex_announcements": "HKEX Announcements",
        "nav.stock_events": "Stock Events",
        "nav.capital_information": "Capital Information",
        "nav.officers": "Officers",
        "nav.company": "Company",
        "nav.metadata": "Metadata",
        "nav.holdings": "Holdings",
        "nav.changes": "Changes",
        "nav.big_changes": "Big Changes",
        "nav.concentration": "Concentration",
        "nav.price": "Price & Turnover",
        "nav.raw_previews": "Raw Previews",
        "nav.copy_for_chatgpt": "Copy for ChatGPT",
        "nav.downloads": "Downloads",
        "report.title": "CCASS Report",
        "report.data_not_available": "DATA NOT AVAILABLE",
        "report.no_source_response": "No source response was available.",
        "report.analysis_summary": (
            "Snapshot {holdings_date} contains {participant_count} participant rows. Top 5 concentration is {top5_pct_of_issued} of issued shares and {top5_pct_of_ccass} of shares held in CCASS. Change comparison is {comparison}."
        ),
        "report.comparison.available": "available",
        "report.comparison.unavailable": "not available",
        "report.section.analysis_ready_summary": "## AI Analysis Ready Summary",
        "report.section.fetch_summary": "## Fetch Summary",
        "report.section.company": "## Company",
        "report.section.announcements": "## HKEX Announcements",
        "report.section.stock_events": "## Stock Events",
        "report.section.capital_information": "## Capital Information",
        "report.section.officers": "## Officers",
        "report.company.lookup_status": "- Lookup status: {value}",
        "report.company.lookup_method": "- Lookup method: {value}",
        "report.company.lookup_status.success": "success",
        "report.company.lookup_method.extracted_from_url": "extracted from URL",
        "report.company.metadata_resolution_note": "Resolved metadata and lookup details below are shown for verification only.",
        "report.section.metadata": "## Metadata",
        "report.section.holdings_summary": "## Holdings Summary",
        "report.section.holdings": "## Holdings",
        "report.section.changes": "## Changes",
        "report.section.big_changes": "## Big Changes",
        "report.section.concentration": "## Concentration",
        "report.section.concentration_history": "## Concentration History",
        "report.concentration_history.latest_values": "### Latest Values",
        "report.concentration_history.participant_count_history": "### Participant Count History",
        "report.concentration_history.table_date": "Date",
        "report.concentration_history.table_top5_issued": "Top 5 / issued",
        "report.concentration_history.table_top10_issued": "Top 10 / issued",
        "report.concentration_history.table_top5_ccass": "Top 5 / CCASS",
        "report.concentration_history.table_top10_ccass": "Top 10 / CCASS",
        "report.concentration_history.table_participant_count": "Participant count",
        "report.concentration_history.unavailable": "Concentration history is unavailable in the current result.",
        "report.section.price_history": "## Price History",
        "report.price_history.unavailable": "Price history is unavailable in the current result.",
        "report.price_history.metadata_heading": "### Metadata",
        "report.price_history.table_heading": "### Price Table",
        "report.price_history.table_date": "Date",
        "report.price_history.table_open": "Open",
        "report.price_history.table_high": "High",
        "report.price_history.table_low": "Low",
        "report.price_history.table_close": "Close",
        "report.price_history.table_adjusted_close": "Adjusted close",
        "report.price_history.table_volume": "Volume",
        "report.price_history.table_turnover": "Turnover",
        "report.price_history.metadata_source": "- Source: {value}",
        "report.price_history.metadata_source_url": "- Source URL: {value}",
        "report.price_history.metadata_price_date_from": "- Price date from: {value}",
        "report.price_history.metadata_price_date_to": "- Price date to: {value}",
        "report.price_history.metadata_adjustment_state": "- Adjustment state: {value}",
        "report.price_history.metadata_currency": "- Currency: {value}",
        "report.price_history.metadata_adjustment_note": "- Adjustment note: {value}",
        "report.price_history.metadata_fetched_at": "- Fetched at: {value}",
        "report.price_history.no_rows": "Price history is unavailable in the current result.",
        "report.warning.price_history_unavailable": "Price history is unavailable ({value}).",
        "report.section.data_quality_warnings": "## Data Quality Warnings",
        "report.fetch.status_success": "- Status: SUCCESS",
        "report.fetch.source": "- Source: {value}",
        "report.fetch.fetched_at": "- Fetched at: {value}",
        "report.fetch.data_as_of": "- Data as of: {value}",
        "report.fetch.cached_snapshot": "- Cached/snapshot: {value}",
        "report.metadata.source": "- Source: {value}",
        "report.metadata.data_as_of": "- Data as of: {value}",
        "report.metadata.code": "- Code: {value}",
        "report.metadata.stock_name": "- Stock name: {value}",
        "report.metadata.issue_id": "- Issue ID: {value}",
        "report.metadata.source_url": "- Source URL: {value}",
        "report.metadata.settlement_note": "- Settlement note: {value}",
        "report.metadata.attribution": "- Attribution: {value}",
        "report.metadata.warning_count": "- Warning count: {value}",
        "report.table.metric": "Metric",
        "report.table.value": "Value",
        "report.no_participant_rows": "No participant rows were returned.",
        "report.previous_snapshot_unavailable": "No previous snapshot was supplied for comparison.",
        "report.no_matching_transfer_pattern": "No matching transfer-like pattern was detected.",
        "report.mechanical_matches_disclaimer": "Possible patterns are mechanical matches only; they do not prove ownership transfer.",
        "report.no_changes_met_threshold": "No changes met the absolute threshold of {threshold:,} shares.",
        "report.no_participant_changes": "No participant-level changes were found.",
        "report.subheading.possible_transfer_patterns": "### Possible Transfer Patterns",
        "report.subheading.possible_transfer_patterns_disclaimer": "Possible patterns are mechanical matches only; they do not prove ownership transfer.",
        "report.no_additional_warning": "- No data quality warnings were generated.",
        "report.warning.cached_snapshot_source": "The current result came from a cached or snapshot data source.",
        "report.warning.holdings_date_unavailable": "The holdings date is unavailable.",
        "report.warning.change_analysis_unavailable": "Change analysis is unavailable because no previous snapshot was supplied.",
        "report.warning.previous_snapshot_enrichment_unavailable": "Previous-snapshot enrichment is unavailable ({exception_name}).",
        "report.change_table.ccass_id": "CCASS ID",
        "report.change_table.participant": "Participant",
        "report.change_table.previous": "Previous",
        "report.change_table.current": "Current",
        "report.change_table.change": "Change",
        "report.change_table.pp_change": "pp change",
        "report.change_table.status": "Status",
        "report.change_table.no_changes": "No participant-level changes were found.",
    },
    "zh_HK": {
        "locale.name.zh_HK": "????????",
        "locale.name.en": "English",
        "ui.app_title": "?? CCASS ??????",
        "ui.app_caption": "???????CCASS ????????????? T+2 ???",
        "ui.jump_links_caption": "??????????????????",
        "ui.sidebar_header": "??",
        "ui.locale_name.zh_HK": "????????",
        "ui.sidebar_language": "??",
        "ui.sidebar_input_type": "????",
        "ui.sidebar_stock_code_issue_id": "???? / Issue ID",
        "ui.sidebar_query_input_caption": "輸入股票代碼可直接查詢，或切換為 Webb-site Issue ID 以在查詢前解析股票代碼。無效輸入會在表單下方顯示。",
        "ui.fetch_guidance_caption": "輸入股票代碼或 Webb-site Issue ID，然後按下擷取。系統會先驗證輸入、解析來源，再在下方渲染報告。",
        "ui.sidebar_timeout": "??",
        "ui.sidebar_big_change_threshold": "????????",
        "ui.sidebar_announcement_period": "????",
        "ui.sidebar_source_mode": "??????",
        "ui.sidebar_data_date": "????",
        "ui.sidebar_history_range": "????",
        "ui.sidebar_top_n": "? N ?",
        "ui.sidebar_percentage_basis": "?????",
        "ui.sidebar_show_rendered_markdown": "????? Markdown",
        "ui.sidebar_use_local_history": "???? SQLite ????????",
        "ui.sidebar_load_price_history": "?????",
        "ui.sidebar_source_mode_caption": (
            "???????{source_mode} | ???{timeout_seconds:g}s | ?????{announcement_period} | ?????{data_date} | ?????{history_range} | ??????{percentage_basis}"
        ),
        "ui.data_source_mode": "???????{source_mode}",
        "ui.hkex_manual_verification": "HKEX SDW????????????????",
        "ui.chart_help_heading": "???? / ??",
        "ui.chart_help_caption": "?????????????????????????",
        "ui.chart_help_surface_caption": "????????????????????????????????????? holdings???????????????? price ??????????",
        "ui.chart_help_rainbow_title": "Rainbow",
        "ui.chart_help_rainbow_body": "?????????? participant ???????????????? snapshot ????????????? participant ??????????????????????????????",
        "ui.chart_help_concentration_title": "???",
        "ui.chart_help_concentration_body": "??????????????????????????????????????????????????????????????",
        "ui.chart_help_price_title": "??",
        "ui.chart_help_price_body": "??????????????????????????????????????????????????????????????",
        "ui.chart_help_announcements_title": "??",
        "ui.chart_help_announcements_body": "使用官方公告日期、標題、來源和連結去對照持倉與價格變化；連結只是客觀參考，不代表任何結論。",
        "ui.hkex_announcements_heading": "HKEX 公告",
        "ui.hkex_announcements_caption": "只讀公告表面，用於顯示官方公告。欄位涵蓋公告日期、標題、來源，以及可用時的連結。",
        "ui.company_information_heading": "公司資訊",
        "ui.company_information_caption": "公司資訊區塊會以可展開方式分組顯示。",
        "ui.report_details_heading": "報告詳情",
        "ui.report_details_caption": "可展開的章節讓詳細內容保留可讀性，同時不會在第一眼就造成資訊過載。",
        "ui.report_details_unavailable": "尚未擷取結果，無法顯示完整報告詳情。",
        "ui.data_confidence_heading": "資料信心快照",
        "ui.data_confidence_caption": "此處只顯示既有的來源、時效、溯源與警告訊號。",
        "ui.data_confidence_freshness": "時效",
        "ui.data_confidence_provenance": "溯源",
        "ui.data_confidence_fallback": "備援",
        "ui.report_flow_heading": "報告流程",
        "ui.report_flow_caption": "先顯示的章節留在頁面上；較詳細與可選內容維持收合，按需要再展開。",
        "ui.report_flow_visible_first": "先顯示",
        "ui.report_flow_collapsed_details": "收合詳情",
        "ui.report_flow_actions": "操作",
        "ui.report_detail_holdings_detail": "持股詳情",
        "ui.report_detail_historical_information": "歷史資訊",
        "ui.report_detail_download_copy": "下載／複製",
        "ui.visualization_heading": "視覺化詳情",
        "ui.visualization_caption": "歷史視圖與可選圖表控制分開呈現，讓核心報告可以先載入。",
        "ui.rendered_markdown": "已渲染 Markdown",
        "ui.rendered_markdown_caption": "只有在需要完整 Markdown 檢視時才打開。",
        "ui.dt_rainbow_heading": "DT Rainbow",
        "ui.dt_rainbow_caption": "僅提供可選互動框架；此版本不包含計算引擎。",
        "ui.dt_rainbow_enable": "啟用 DT Rainbow",
        "ui.dt_rainbow_generate": "產生 DT Rainbow",
        "ui.dt_rainbow_loading": "正在準備可選的 DT Rainbow 視圖……",
        "ui.dt_rainbow_unavailable": "此版本未實作 DT Rainbow 計算。",
        "ui.hkex_announcements_count": "公告數量",
        "ui.hkex_announcements_rows_label": "公告列表",
        "ui.hkex_announcements_sorting_note": "按公告日期排序，最新在前。",
        "ui.hkex_announcements_empty": "在已批准的只讀表面中，目前沒有可用的公告列。",
        "ui.hkex_announcements_unavailable": "目前的抓取結果沒有公告資料。",
        "ui.stock_events_heading": "股份事件",
        "ui.stock_events_caption": "如有可用，客觀事件紀錄會在此分組顯示。",
        "ui.stock_events_rows_label": "股份事件列表",
        "ui.stock_events_sorting_note": "當正式資料可用時，列會按事件日期由新到舊排序。",
        "ui.stock_events_source_ready": "股份事件資料來源已接通。",
        "ui.stock_events_source_pending": "股份事件資料來源仍在等待接通；讀取路徑已建立，但尚未連接正式資料源。",
        "ui.stock_events_empty": "目前結果沒有可用的股份事件列。",
        "ui.stock_events_unavailable": "目前的抓取結果沒有股份事件資料。",
        "ui.capital_information_heading": "資本資料",
        "ui.capital_information_caption": "如有可用，資本結構事實會在此分組顯示。",
        "ui.capital_information_rows_label": "資本資料列表",
        "ui.capital_information_sorting_note": "當正式資料可用時，列會按標題排序。",
        "ui.capital_information_source_ready": "資本資料來源已接通。",
        "ui.capital_information_source_pending": "資本資料來源仍在等待接通；讀取路徑已建立，但尚未連接正式資料源。",
        "ui.capital_information_empty": "目前結果沒有可用的資本資料列。",
        "ui.capital_information_unavailable": "目前的抓取結果沒有資本資料。",
        "ui.officers_heading": "高管資料",
        "ui.officers_caption": "如有可用，高管資訊會在此分組顯示。",
        "ui.officers_source_ready": "高管資料來源已接通。",
        "ui.officers_unavailable": "目前的抓取結果沒有高管資料。",
        "ui.officers_source_pending": "高管資料來源仍在等待接通；讀取路徑已建立，但尚未連接正式資料源。",
        "ui.officers_empty": "目前結果沒有可用的高管列。",
        "ui.officers_rows_label": "高管列表",
        "ui.officers_sorting_note": "正式資料可用時，列會依現任狀態與任期日期排序。",
        "ui.officers_table_name": "姓名",
        "ui.officers_table_positions": "職位",
        "ui.officers_table_tenure_from": "任期開始",
        "ui.officers_table_tenure_to": "任期結束",
        "ui.officers_table_is_current": "現任",
        "ui.officers_table_sex": "性別",
        "ui.officers_table_age": "年齡",
        "ui.officers_table_education": "學歷",
        "ui.officers_table_salary": "薪酬",
        "ui.officers_table_biography": "簡介",
        "ui.hkex_announcements_export_heading": "匯出標籤",
        "ui.hkex_announcements_export_note": "即使公告列為空，相關匯出標籤仍會保留。",
        "ui.hkex_announcements_export_csv_label": "CSV 匯出",
        "ui.hkex_announcements_export_excel_label": "Excel 活頁簿匯出",
        "ui.hkex_announcements_table_announcement_date": "公告日期",
        "ui.hkex_announcements_table_title": "標題",
        "ui.hkex_announcements_table_source": "來源",
        "ui.hkex_announcements_table_link": "連結",
        "ui.stock_events_table_event_date": "事件日期",
        "ui.stock_events_table_title": "標題",
        "ui.stock_events_table_type": "類型",
        "ui.stock_events_table_source": "來源",
        "ui.stock_events_table_link": "連結",
        "ui.stock_events_table_details": "詳情",
        "ui.capital_information_table_label": "標題",
        "ui.capital_information_table_value": "數值",
        "ui.capital_information_table_unit": "單位",
        "ui.capital_information_table_as_of": "截至",
        "ui.capital_information_table_source": "來源",
        "ui.capital_information_table_note": "備註",
        "ui.capital_information_table_link": "連結",
        "report.link_label": "連結",
        "ui.report_navigation_heading": "報告導航",
        "ui.report_navigation_caption": "以下連結對應已渲染的報告章節。",
        "ui.data_quality_heading": "資料質量／警告",
        "ui.data_quality_help_caption": "這些警告只說明完整性、資料質量及系統限制，不屬於投資建議、交易訊號或股票評級。",
        "ui.data_quality_caption": "顯示客觀警告、不可用狀態及缺漏資料提示。",
        "ui.data_quality_no_warnings": "沒有產生資料質量警告。",
        "ui.data_quality_unavailable": "目前結果沒有可供顯示的資料質量警告。",
        "ui.chart_help_cross_check_title": "????",
        "ui.chart_help_cross_check_body": "??????????????????????????????????? warnings ???????????",
        "ui.input_type.stock_code": "????",
        "ui.input_type.webb_site_issue_id": "Webb-site Issue ID",
        "ui.source_mode.auto": "??",
        "ui.source_mode.webbsite": "Webb-site",
        "ui.source_mode.google_drive_csv": "Google Drive CSV",
        "ui.announcement_period.all": "??",
        "ui.announcement_period.7_days": "7 ?",
        "ui.announcement_period.30_days": "30 ?",
        "ui.announcement_period.90_days": "90 ?",
        "ui.history_range.latest": "??",
        "ui.history_range.7_days": "7 ?",
        "ui.history_range.30_days": "30 ?",
        "ui.history_range.90_days": "90 ?",
        "ui.history_range.custom": "??",
        "ui.percentage_basis.ccass": "CCASS",
        "ui.percentage_basis.issued_shares": "?????",
        "ui.fetch": "??",
        "ui.validation_error_prefix": "????",
        "ui.unexpected_error_prefix": "UNEXPECTED_ERROR",
        "ui.fetch_summary_remaining": "擴取摘要與所有必要報告章節仍可在下方查看。",
        "ui.fetch_status_running": "正在擷取 {source_mode} 資料，代號 {code}。",
        "ui.fetch_status_success": "已從 {source} 完成擷取；資料截至 {data_as_of}。",
        "ui.fetch_status_success_cached": "已從快取／快照 {source} 完成擷取；資料截至 {data_as_of}。",
        "ui.fetch_status_failure": "擷取失敗：{error}",
        "ui.progress_starting": "開始中",
        "ui.progress_validated_stock_code": "已驗證股票代碼",
        "ui.progress_fetching_source": "正在擷取低頻 CCASS 資料來源",
        "ui.progress_source_unavailable": "來源不可用，正在建立完整診斷報告",
        "ui.progress_ready_with_error_details": "報告已就緒並附來源錯誤詳情",
        "ui.progress_computing_analysis": "正在計算集中度與比較欄位",
        "ui.progress_rendering_report": "正在渲染 Markdown 報告",
        "ui.progress_ready": "報告已就緒",
        "ui.raw_previews_heading": "原始預覽",
        "ui.raw_previews_expander": "解析後的來源表格",
        "ui.raw_previews_unavailable": "成功抓取後才可查看原始預覽。",
        "ui.raw_previews_help_caption": "????????????????????????????",
        "ui.raw_previews_caption": "?????????????????",
        "ui.raw_previews_table_index": "表格索引",
        "ui.raw_previews_table_name": "表格名稱",
        "ui.raw_previews_shape": "形狀",
        "ui.raw_previews_columns": "欄位",
        "ui.raw_previews_sample_rows": "預覽列",
        "ui.raw_previews_no_sample_rows": "沒有可用的預覽列。",
        "ui.copy_for_chatgpt": "??? ChatGPT",
        "ui.copy_for_chatgpt_caption": "複製已渲染的報告內容以貼到 ChatGPT。負載已包含安全標頭與目前報告文字。",
        "ui.copy_report": "????",
        "ui.downloads_heading": "下載本股票",
        "ui.downloads_unavailable": "成功抓取後才可下載。",
        "ui.downloads_caption": "合併 CSV 包含 Holdings、Changes、Big Changes 和 Concentration，並列出來源 URL、擷取時間與資料意義。下方按鈕會重用已擷取的結果，提供 CSV、Excel 工作簿、Markdown 報告及各章節匯出。",
        "ui.downloads_workflow_heading": "匯出流程",
        "ui.downloads_workflow_caption": "選擇要下載的項目。合併 CSV、Excel 工作簿、Markdown 報告，以及各章節匯出都會重用已擷取的結果。",
        "ui.downloads_combined_csv": "全部 CCASS 資料 CSV",
        "ui.downloads_excel_workbook": "Excel - 全部章節",
        "ui.downloads_report_markdown": "Markdown 報告",
        "ui.downloads_download_combined_csv": "下載全部 CCASS 資料 CSV",
        "ui.downloads_download_excel_workbook": "下載 Excel",
        "ui.downloads_download_markdown_report": "下載 Markdown 報告",
        "ui.downloads_csv_preview": "CSV 內容預覽",
        "ui.downloads_first_80_csv_lines": "前 80 行 CSV",
        "ui.downloads_section_specific": "各章節下載",
        "ui.downloads_raw_preview_summary_csv": "原始預覽摘要 CSV",
        "ui.downloads_download_raw_preview_summary_csv": "???????? CSV",
        "ui.downloads_raw_preview_holdings_csv": "?????? CSV",
        "ui.downloads_download_raw_preview_holdings_csv": "???????? CSV",
        "ui.raw_markdown": "?? Markdown",
        "ui.raw_previews_summary_title": "???????",
        "ui.raw_previews_holdings_title": "??????",
        "ui.raw_previews_metric": "??",
        "ui.raw_previews_value": "?",
        "ui.full_summary_heading": "????",
        "ui.full_summary_caption": "????????????????",
        "ui.full_summary_table_section": "??",
        "ui.full_summary_table_status": "??",
        "ui.full_summary_table_note": "??",
        "ui.full_summary_status_available": "??",
        "ui.full_summary_status_unavailable": "???",
        "ui.full_summary_unavailable": "???????????????",
        "ui.full_summary_note_analysis_ready_summary": "可提供可供分析的摘要。",
        "ui.full_summary_note_fetch_summary": "?????????????",
        "ui.full_summary_note_metadata": "來源、資料截至與溯源詳情可用。",
        "ui.full_summary_note_company": "公司 {code} / Issue ID {issue_id}",
        "ui.full_summary_note_announcements": "目前結果沒有可用的公告表面。",
        "ui.full_summary_note_announcements_available": "目前有 {announcement_count} 條公告可用。",
        "ui.full_summary_note_stock_events": "目前結果沒有可用的股份事件表面。",
        "ui.full_summary_note_stock_events_ready": "股份事件表面已由 {source_name} 提供。",
        "ui.full_summary_note_stock_events_pending": "股份事件表面已就位，但資料來源仍在等待接通。",
        "ui.full_summary_note_capital_information": "目前結果沒有可用的資本資料表面。",
        "ui.full_summary_note_capital_information_ready": "資本資料表面已由 {source_name} 提供。",
        "ui.full_summary_note_capital_information_pending": "資本資料表面已就位，但資料來源仍在等待接通。",
        "ui.full_summary_note_officers": "目前結果沒有可用的高管表面。",
        "ui.full_summary_note_officers_pending": "高管表面已就位，但資料來源仍在等待接通。",
        "ui.full_summary_note_officers_ready": "高管表面已由 {source_name} 提供。",
        "ui.full_summary_note_holdings": "{participant_count} ???????",
        "ui.full_summary_note_changes_available": "?????????",
        "ui.full_summary_note_changes_unavailable": "?????????",
        "ui.full_summary_note_big_changes_available": "??????????",
        "ui.full_summary_note_big_changes_unavailable": "??????????",
        "ui.full_summary_note_concentration": "? 5 / issued {top5_pct_of_issued} | ? 10 / issued {top10_pct_of_issued}",
        "ui.full_summary_note_concentration_history": "{snapshot_count} ??????",
        "ui.full_summary_note_price_history": "????????????",
        "ui.full_summary_note_price_history_available": "????????? {price_date_from} ? {price_date_to} ??? {source_name}?",
        "ui.full_summary_note_price_history_unavailable": "????????????",
        "ui.full_summary_note_raw_previews": "{table_count} ??????",
        "ui.full_summary_note_copy_functions": "可從目前結果複製報告或 ChatGPT 負載。",
        "ui.full_summary_note_downloads": "?? CSV????? Markdown ???",
        "ui.full_summary_note_data_quality_no_warnings": "??????????",
        "ui.full_summary_note_data_quality_warnings": "{warning_count} 項資料質量警告。",
        "ui.related_context_heading": "關聯脈絡",
        "ui.related_context_caption": "可使用下列連結在相鄰的報告區段之間切換。",
        "ui.related_context_company": "公司脈絡",
        "ui.related_context_movement": "持股變動脈絡",
        "ui.related_context_history": "歷史脈絡",
        "ui.related_context_operations": "營運脈絡",
        "ui.research_workflow_heading": "研究工作流程",
        "ui.research_workflow_caption": "為目前研究工作階段提供流程狀態、會話中繼資料與 context readiness。",
        "ui.research_workflow_unavailable": "目前結果尚未準備完成，研究工作流程不可用。",
        "ui.research_workflow_state": "工作流程狀態",
        "ui.research_workflow_state_created": "已建立",
        "ui.research_workflow_state_loaded": "已載入",
        "ui.research_workflow_state_ready": "已就緒",
        "ui.research_workflow_session_id": "會話 ID",
        "ui.research_workflow_stock_code": "股票編號",
        "ui.research_workflow_created_at": "建立時間",
        "ui.research_workflow_loaded_at": "載入時間",
        "ui.research_workflow_ready_at": "就緒時間",
        "ui.research_workflow_context_availability": "Context 可用性",
        "ui.research_workflow_context_available": "可用",
        "ui.research_workflow_context_unavailable": "不可用",
        "ui.research_workflow_package_reference": "關聯 ResearchContextPackage",
        "ui.research_workflow_quality_reference": "品質參考",
        "ui.research_workflow_freshness_reference": "新鮮度參考",
        "ui.research_workflow_provenance_reference": "來源參考",
        "ui.research_workflow_warnings_summary": "警告摘要",
        "ui.research_workflow_warnings_none": "沒有警告。",
        "ui.research_dashboard_heading": "研究儀表板",
        "ui.research_dashboard_caption": "將已載入股票、snapshot 狀態、集中度與下一步連結濃縮在一個工作視圖中。",
        "ui.research_dashboard_stock_code": "股票編號",
        "ui.research_dashboard_stock_name": "股票名稱",
        "ui.research_dashboard_snapshot_date": "Snapshot 日期",
        "ui.research_dashboard_snapshot_count": "Snapshot 數量",
        "ui.research_dashboard_freshness": "新鮮度",
        "ui.research_dashboard_provenance": "來源性",
        "ui.research_dashboard_concentration": "集中度",
        "ui.research_dashboard_comparison": "比較狀態",
        "ui.research_dashboard_report_output": "報告輸出",
        "ui.research_dashboard_quick_links": "快速連結",
        "ui.research_dashboard_link_holdings": "持有人詳情",
        "ui.research_dashboard_link_concentration": "集中度",
        "ui.research_dashboard_link_changes": "變動",
        "ui.research_dashboard_link_big_changes": "重大變動",
        "ui.research_dashboard_link_copy": "複製 / 下載",
        "ui.research_dashboard_link_raw_markdown": "原始 Markdown",
        "ui.research_intelligence_current_state_heading": "目前 CCASS 狀況",
        "ui.research_intelligence_current_state_body": "使用集中度、持有人與摘要區段來理解目前狀態。",
        "ui.research_intelligence_changes_heading": "跟前一份資料相比有什麼變化？",
        "ui.research_intelligence_changes_body": "當有前一個 snapshot 時，使用變動與重大變動區段來查看差異。",
        "ui.research_intelligence_deeper_look_heading": "接下來該看哪裡？",
        "ui.research_intelligence_deeper_look_body": "使用下方連結查看持有人變動、門檻變動與集中度歷史。",
        "ui.all_parsed_tables_heading": "完整報告詳情",
        "ui.all_parsed_tables_caption": "以下已渲染的報告章節依照已核准的詳情階層排列。",
        "nav.fetch_summary": "????",
        "nav.full_summary": "??????",
        "nav.all_tables": "完整報告詳情",
        "nav.dt_rainbow": "DT Rainbow",
        "nav.hkex_announcements": "HKEX 公告",
        "nav.stock_events": "股份事件",
        "nav.capital_information": "資本資料",
        "nav.officers": "高管資料",
        "nav.company": "??",
        "nav.metadata": "??",
        "nav.holdings": "??",
        "nav.changes": "??",
        "nav.big_changes": "???",
        "nav.concentration": "???",
        "nav.price": "價格與成交",
        "nav.raw_previews": "原始預覽",
        "nav.copy_for_chatgpt": "??? ChatGPT",
        "nav.downloads": "??",
        "report.title": "CCASS ??",
        "report.data_not_available": "?????",
        "report.no_source_response": "??????????",
        "report.analysis_summary": (
            "?? {holdings_date} ?? {participant_count} ??????? 5 ????????? {top5_pct_of_issued}?? CCASS ?? {top5_pct_of_ccass}??????{comparison}?"
        ),
        "report.comparison.available": "??",
        "report.comparison.unavailable": "???",
        "report.section.analysis_ready_summary": "## AI ??????",
        "report.section.fetch_summary": "## 擷取摘要",
        "report.section.company": "## 公司",
        "report.section.announcements": "## HKEX 公告",
        "report.section.stock_events": "## 股份事件",
        "report.section.capital_information": "## 資本資料",
        "report.section.officers": "## 高管資料",
        "report.company.lookup_status": "- 查詢狀態：{value}",
        "report.company.lookup_method": "- 查詢方法：{value}",
        "report.company.lookup_status.success": "成功",
        "report.company.lookup_method.extracted_from_url": "從 URL 擷取",
        "report.company.metadata_resolution_note": "已解析的 metadata 與查詢詳情僅供驗證用途。",
        "report.section.metadata": "## 元資料",
        "report.section.holdings_summary": "## ????",
        "report.section.holdings": "## ??",
        "report.section.changes": "## ??",
        "report.section.big_changes": "## ???",
        "report.section.concentration": "## ???",
        "report.section.concentration_history": "## 持股集中度歷史",
        "report.concentration_history.latest_values": "### 最新值",
        "report.concentration_history.participant_count_history": "### 參與者數量歷史",
        "report.concentration_history.table_date": "日期",
        "report.concentration_history.table_top5_issued": "前五大 / 已發行股份",
        "report.concentration_history.table_top10_issued": "前十大 / 已發行股份",
        "report.concentration_history.table_top5_ccass": "前五大 / CCASS",
        "report.concentration_history.table_top10_ccass": "前十大 / CCASS",
        "report.concentration_history.table_participant_count": "參與者數量",
        "report.concentration_history.unavailable": "目前結果沒有可用的持股集中度歷史資料。",
        "report.section.price_history": "## 價格歷史",
        "report.price_history.unavailable": "目前結果沒有可用的價格歷史資料。",
        "report.price_history.metadata_heading": "### 中繼資料",
        "report.price_history.table_heading": "### 價格表",
        "report.price_history.table_date": "日期",
        "report.price_history.table_open": "開市",
        "report.price_history.table_high": "最高",
        "report.price_history.table_low": "最低",
        "report.price_history.table_close": "收市",
        "report.price_history.table_adjusted_close": "調整後收市",
        "report.price_history.table_volume": "成交量",
        "report.price_history.table_turnover": "成交額",
        "report.price_history.metadata_source": "- 來源：{value}",
        "report.price_history.metadata_source_url": "- 來源網址：{value}",
        "report.price_history.metadata_price_date_from": "- 價格起始日：{value}",
        "report.price_history.metadata_price_date_to": "- 價格結束日：{value}",
        "report.price_history.metadata_adjustment_state": "- 調整狀態：{value}",
        "report.price_history.metadata_currency": "- 貨幣：{value}",
        "report.price_history.metadata_adjustment_note": "- 調整備註：{value}",
        "report.price_history.metadata_fetched_at": "- 擷取時間：{value}",
        "report.price_history.no_rows": "目前結果沒有可用的價格歷史資料。",
        "report.warning.price_history_unavailable": "價格歷史不可用（{value}）。",
        "report.section.data_quality_warnings": "## ??????",
        "report.fetch.status_success": "- ?????",
        "report.fetch.source": "- ???{value}",
        "report.fetch.fetched_at": "- ?????{value}",
        "report.fetch.data_as_of": "- 資料截至：{value}",
        "report.fetch.cached_snapshot": "- ??/???{value}",
        "report.metadata.source": "- 來源：{value}",
        "report.metadata.data_as_of": "- 資料截至：{value}",
        "report.metadata.code": "- ???{value}",
        "report.metadata.stock_name": "- ?????{value}",
        "report.metadata.issue_id": "- Issue ID?{value}",
        "report.metadata.source_url": "- ?????{value}",
        "report.metadata.settlement_note": "- ?????{value}",
        "report.metadata.attribution": "- ?????{value}",
        "report.metadata.warning_count": "- 警告數量：{value}",
        "report.table.metric": "??",
        "report.table.value": "?",
        "report.no_participant_rows": "?????????",
        "report.previous_snapshot_unavailable": "?????????????",
        "report.no_matching_transfer_pattern": "?????????????",
        "report.mechanical_matches_disclaimer": "???????????????????",
        "report.no_changes_met_threshold": "???????? {threshold:,} ???????",
        "report.no_participant_changes": "?????????????",
        "report.subheading.possible_transfer_patterns": "### ???????",
        "report.subheading.possible_transfer_patterns_disclaimer": "???????????????????",
        "report.no_additional_warning": "- 沒有產生資料質量警告。",
        "report.warning.cached_snapshot_source": "????????????????",
        "report.warning.holdings_date_unavailable": "????????",
        "report.warning.change_analysis_unavailable": "???????????????????",
        "report.warning.previous_snapshot_enrichment_unavailable": "???????????{exception_name}??",
        "report.change_table.ccass_id": "CCASS ID",
        "report.change_table.participant": "???",
        "report.change_table.previous": "??",
        "report.change_table.current": "??",
        "report.change_table.change": "??",
        "report.change_table.pp_change": "?????",
        "report.change_table.status": "??",
        "report.change_table.no_changes": "?????????????",
    },
}

REPORT_SECTION_KEYS = (
    "analysis_ready_summary",
    "company",
    "announcements",
    "stock_events",
    "capital_information",
    "officers",
    "metadata",
    "fetch_summary",
    "holdings_summary",
    "holdings",
    "changes",
    "big_changes",
    "concentration",
    "concentration_history",
    "price_history",
    "data_quality_warnings",
)

SECTION_HEADINGS = tuple(TRANSLATION_REGISTRY[DEFAULT_LOCALE][f"report.section.{key}"] for key in REPORT_SECTION_KEYS)
DATA_NOT_AVAILABLE = TRANSLATION_REGISTRY[DEFAULT_LOCALE]["report.data_not_available"]
CHATGPT_COPY_HEADER = (
    "Please analyse this HK CCASS report. Treat CCASS as settlement-layer nominee data, "
    "not proof of beneficial ownership. Do not invent unavailable facts or figures."
)


def translate_text(locale: str, key: str, /, **values: object) -> str:
    locale_map = TRANSLATION_REGISTRY.get(locale, {})
    template = locale_map.get(key)
    if template is None and locale != "en":
        template = TRANSLATION_REGISTRY["en"].get(key)
        if template is not None:
            warnings.warn(
                f"Missing translation for {key!r} in {locale}; falling back to English.",
                stacklevel=2,
            )
    if template is None:
        warnings.warn(
            f"Missing translation for {key!r} in {locale} and English fallback; using the key.",
            stacklevel=2,
        )
        template = key
    return template.format(**values)


def report_section_headings(locale: str = DEFAULT_LOCALE) -> tuple[str, ...]:
    return tuple(translate_text(locale, f"report.section.{key}") for key in REPORT_SECTION_KEYS)


def localized_report_anchor(section_key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", section_key.lower()).strip("-")


def section_related_context_markdown(locale: str, section_key: str) -> str:
    related = _related_sections_for(section_key)
    if not related:
        return ""
    links = " · ".join(
        f"[{translate_text(locale, f'report.section.{related_key}').removeprefix('## ')}](#{localized_report_anchor(related_key)})"
        for related_key in related
    )
    return f"{translate_text(locale, 'ui.related_context_caption')} {links}"


def cross_surface_context_markdown(locale: str) -> str:
    def group_line(label_key: str, items: tuple[tuple[str, str], ...]) -> str:
        links = " · ".join(f"[{label}](#{anchor_key})" for label, anchor_key in items)
        return f"{translate_text(locale, label_key)}: {links}"

    groups = (
        group_line(
            "ui.related_context_company",
            tuple(
                (
                    translate_text(locale, f"report.section.{key}").removeprefix("## "),
                    localized_report_anchor(key),
                )
                for key in ("announcements", "stock_events", "capital_information", "officers")
            ),
        ),
        group_line(
            "ui.related_context_movement",
            tuple(
                (
                    translate_text(locale, f"report.section.{key}").removeprefix("## "),
                    localized_report_anchor(key),
                )
                for key in ("holdings", "changes", "big_changes", "concentration")
            ),
        ),
        group_line(
            "ui.related_context_history",
            tuple(
                (
                    translate_text(locale, f"report.section.{key}").removeprefix("## "),
                    localized_report_anchor(key),
                )
                for key in ("concentration_history", "price_history")
            ),
        ),
        group_line(
            "ui.related_context_operations",
            (
                (translate_text(locale, "report.section.metadata").removeprefix("## "), localized_report_anchor("metadata")),
                (translate_text(locale, "report.section.fetch_summary").removeprefix("## "), localized_report_anchor("fetch_summary")),
                (translate_text(locale, "report.section.data_quality_warnings").removeprefix("## "), localized_report_anchor("data_quality_warnings")),
                (translate_text(locale, "ui.raw_previews_heading"), localized_report_anchor("raw_previews")),
                (translate_text(locale, "ui.copy_for_chatgpt"), localized_report_anchor("copy_for_chatgpt")),
                (translate_text(locale, "ui.downloads_heading"), localized_report_anchor("downloads")),
            ),
        ),
    )
    return f"{translate_text(locale, 'ui.related_context_caption')} " + " ; ".join(groups)


def _related_sections_for(section_key: str) -> tuple[str, ...]:
    related_map: dict[str, tuple[str, ...]] = {
        "company": ("announcements", "stock_events", "capital_information", "officers"),
        "announcements": ("company", "stock_events", "capital_information", "officers"),
        "stock_events": ("company", "announcements", "capital_information", "officers"),
        "capital_information": ("company", "announcements", "stock_events", "officers"),
        "officers": ("company", "announcements", "stock_events", "capital_information"),
        "holdings": ("changes", "big_changes", "concentration", "concentration_history"),
        "changes": ("holdings", "big_changes", "concentration_history"),
        "big_changes": ("holdings", "changes", "concentration_history"),
        "concentration": ("holdings", "concentration_history", "price_history"),
        "concentration_history": ("holdings", "concentration", "price_history"),
        "price_history": ("holdings", "concentration_history", "announcements"),
    }
    return related_map.get(section_key, ())


def build_markdown_report(
    response: CcassResponse | None,
    *,
    code: str,
    analysis: AnalysisResult | None = None,
    fetch_error: str | None = None,
    history_snapshots: Sequence[CcassResponse] | None = None,
    announcements: AnnouncementsResponse | None = None,
    stock_events: StockEventsResponse | None = None,
    capital_information: CapitalInformationResponse | None = None,
    officers: OfficersResponse | None = None,
    price_history: PriceHistoryResponse | None = None,
    research_workflow: object | None = None,
    research_context_entry: object | None = None,
    locale: str = DEFAULT_LOCALE,
) -> str:
    stock_name = response.metadata.name if response and response.metadata.name else translate_text(locale, "report.data_not_available")
    lines = [f"# {translate_text(locale, 'report.title')} ? {code} {stock_name}", ""]
    if research_workflow is not None:
        from ccass_core.research_workflow_presentation import build_research_workflow_summary_markdown

        lines.extend([build_research_workflow_summary_markdown(research_workflow, locale=locale), ""])
    if research_context_entry is not None:
        from ccass_core.ai_research_context_entry import build_ai_research_context_consumer_entry_markdown

        lines.extend([build_ai_research_context_consumer_entry_markdown(research_context_entry), ""])

    if response is None:
        reason = fetch_error or translate_text(locale, "report.no_source_response")
        unavailable = f"{translate_text(locale, 'report.data_not_available')} ? {reason}"
        for key in REPORT_SECTION_KEYS:
            lines.extend([
                f"<a id='{localized_report_anchor(key)}'></a>",
                translate_text(locale, f"report.section.{key}"),
                "",
                unavailable,
                "",
            ])
        return "\n".join(lines).rstrip() + "\n"

    computed = analysis or AnalysisResult()
    summary = response.holdings_summary
    metadata = response.metadata
    lines.extend(
        [
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[0])}'></a>",
            translate_text(locale, "report.section.analysis_ready_summary"),
            "",
            _analysis_summary(response, computed, locale),
            "",
            cross_surface_context_markdown(locale),
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[1])}'></a>",
            translate_text(locale, "report.section.company"),
            "",
            section_related_context_markdown(locale, "company"),
            "",
            translate_text(locale, "report.metadata.stock_name", value=_text(metadata.name, locale)),
            translate_text(locale, "report.metadata.code", value=metadata.code),
            translate_text(locale, "report.metadata.issue_id", value=metadata.issue_id),
            translate_text(locale, "report.company.lookup_status", value=translate_text(locale, "report.company.lookup_status.success")),
            translate_text(locale, "report.company.lookup_method", value=translate_text(locale, "report.company.lookup_method.extracted_from_url")),
            translate_text(locale, "report.company.metadata_resolution_note"),
            "",
        ]
    )
    lines.extend(_company_information_section(announcements, stock_events, capital_information, officers, locale))
    lines.extend(
        [
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[6])}'></a>",
            translate_text(locale, "report.section.metadata"),
            "",
            translate_text(locale, "report.metadata.source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.metadata.data_as_of", value=_text(metadata.data_as_of, locale)),
            translate_text(locale, "report.metadata.source_url", value=_text(metadata.source_url, locale)),
            translate_text(locale, "report.metadata.settlement_note", value=_text(metadata.settlement_note, locale)),
            translate_text(locale, "report.metadata.attribution", value=_text(metadata.attribution, locale)),
            translate_text(locale, "report.metadata.warning_count", value=len(computed.warnings)),
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[7])}'></a>",
            translate_text(locale, "report.section.fetch_summary"),
            "",
            translate_text(locale, "report.fetch.status_success"),
            translate_text(locale, "report.fetch.source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.fetch.fetched_at", value=_datetime(metadata.fetched_at, locale)),
            translate_text(locale, "report.fetch.data_as_of", value=_text(metadata.data_as_of, locale)),
            translate_text(locale, "report.fetch.cached_snapshot", value=_yes_no(metadata.cached, locale)),
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[8])}'></a>",
            translate_text(locale, "report.section.holdings_summary"),
            "",
            f"| {translate_text(locale, 'report.table.metric')} | {translate_text(locale, 'report.table.value')} |",
            "|---|---:|",
            f"| Total in CCASS shares | {_integer(summary.total_in_ccass_shares, locale)} |",
            f"| Total in CCASS / issued | {_percent(summary.total_in_ccass_pct_of_issued, locale)} |",
            f"| Issued shares | {_integer(summary.issued_shares, locale)} |",
            f"| Issued shares as of | {_text(summary.issued_shares_as_of, locale)} |",
            f"| Non-CCASS shares | {_integer(summary.non_ccass_shares, locale)} |",
            f"| Non-CCASS / issued | {_percent(summary.non_ccass_pct_of_issued, locale)} |",
            f"| Participant count | {summary.participant_count} |",
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[9])}'></a>",
            translate_text(locale, "report.section.holdings"),
            "",
            section_related_context_markdown(locale, "holdings"),
            "",
        ]
    )
    lines.extend(_holdings_table(response, locale))
    lines.extend([
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[10])}'></a>",
        translate_text(locale, "report.section.changes"),
        "",
    ])
    lines.extend(_changes_section(computed, locale))
    lines.extend([
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[11])}'></a>",
        translate_text(locale, "report.section.big_changes"),
        "",
    ])
    lines.extend(_big_changes_section(computed, locale))
    lines.extend(
        [
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[12])}'></a>",
            translate_text(locale, "report.section.concentration"),
            "",
            section_related_context_markdown(locale, "concentration"),
            "",
            f"| {translate_text(locale, 'report.table.metric')} | {translate_text(locale, 'report.table.value')} |",
            "|---|---:|",
            f"| Top 5 / issued | {_percent(summary.top5_pct_of_issued, locale)} |",
            f"| Top 10 / issued | {_percent(summary.top10_pct_of_issued, locale)} |",
            f"| Top 5 / CCASS | {_percent(summary.top5_pct_of_ccass, locale)} |",
            f"| Top 10 / CCASS | {_percent(summary.top10_pct_of_ccass, locale)} |",
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[13])}'></a>",
            translate_text(locale, "report.section.concentration_history"),
            "",
            section_related_context_markdown(locale, "concentration_history"),
            "",
        ]
    )
    lines.extend(_concentration_history_section(response, history_snapshots, locale))
    lines.extend(_price_history_section(price_history, locale))
    lines.extend([
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[15])}'></a>",
        translate_text(locale, "report.section.data_quality_warnings"),
        "",
    ])
    warnings_list = list(computed.warnings)
    if not warnings_list:
        lines.append(translate_text(locale, "report.no_additional_warning"))
    else:
        lines.extend(f"- {_localize_warning(warning, locale)}" for warning in warnings_list)
    return "\n".join(lines).rstrip() + "\n"


def build_chatgpt_copy_payload(report: str) -> str:
    return f"{CHATGPT_COPY_HEADER}\n\n{report.strip()}\n"


def report_filename(code: str) -> str:
    return f"{code}_ccass_report.md"


def _analysis_summary(response: CcassResponse, analysis: AnalysisResult, locale: str) -> str:
    summary = response.holdings_summary
    return translate_text(
        locale,
        "report.analysis_summary",
        holdings_date=_text(response.metadata.holdings_date, locale),
        participant_count=summary.participant_count,
        top5_pct_of_issued=_percent(summary.top5_pct_of_issued, locale),
        top5_pct_of_ccass=_percent(summary.top5_pct_of_ccass, locale),
        comparison=translate_text(
            locale,
            "report.comparison.available" if analysis.previous_available else "report.comparison.unavailable",
        ),
    )


def _holdings_table(response: CcassResponse, locale: str) -> list[str]:
    if not response.holdings:
        return [f"{translate_text(locale, 'report.data_not_available')} ? {translate_text(locale, 'report.no_participant_rows')}"]
    lines = [
        f"| {translate_text(locale, 'report.change_table.ccass_id')} | {translate_text(locale, 'report.change_table.participant')} | Shares | Last change | % issued | % CCASS | Cumulative % | Category |",
        "|---|---|---:|---|---:|---:|---:|---|",
    ]
    for row in response.holdings:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.rank),
                    _escape(row.participant_id),
                    _escape(row.participant),
                    f"{row.shares:,}",
                    _text(row.last_change, locale),
                    _percent(row.pct_of_issued, locale),
                    _percent(row.pct_of_ccass, locale),
                    _percent(row.cumulative_pct_of_issued, locale),
                    _escape(row.participant_category or translate_text(locale, 'report.data_not_available')),
                ]
            )
            + " |"
        )
    return lines


def _changes_section(analysis: AnalysisResult, locale: str) -> list[str]:
    if not analysis.previous_available:
        return [
            f"{translate_text(locale, 'report.data_not_available')} ? {translate_text(locale, 'report.previous_snapshot_unavailable')}"
        ]
    lines = [
        section_related_context_markdown(locale, "changes"),
        "",
    ]
    lines.extend(_change_table(analysis.changes, locale))
    lines.extend([
        "",
        translate_text(locale, "report.subheading.possible_transfer_patterns"),
        "",
    ])
    if not analysis.transfer_patterns:
        lines.append(
            f"{translate_text(locale, 'report.data_not_available')} ? {translate_text(locale, 'report.no_matching_transfer_pattern')}"
        )
    else:
        lines.append(translate_text(locale, "report.subheading.possible_transfer_patterns_disclaimer"))
        for pattern in analysis.transfer_patterns:
            lines.append(
                f"- {_escape(pattern.from_participant)} ? {_escape(pattern.to_participant)}: "
                f"approximately {pattern.approximate_shares:,} shares (difference {pattern.difference:,})."
            )
    return lines


def _big_changes_section(analysis: AnalysisResult, locale: str) -> list[str]:
    if not analysis.previous_available:
        return [
            f"{translate_text(locale, 'report.data_not_available')} ? {translate_text(locale, 'report.previous_snapshot_unavailable')}"
        ]
    if not analysis.big_changes:
        return [translate_text(locale, "report.no_changes_met_threshold", threshold=analysis.big_change_threshold)]
    return [
        section_related_context_markdown(locale, "big_changes"),
        "",
        *_change_table(analysis.big_changes, locale),
    ]


def _concentration_history_section(
    response: CcassResponse,
    history_snapshots: Sequence[CcassResponse] | None,
    locale: str,
) -> list[str]:
    snapshots_by_date: dict[str, CcassResponse] = {}
    for snapshot in [*(history_snapshots or ()), response]:
        holdings_date = snapshot.metadata.holdings_date
        if holdings_date is None:
            continue
        snapshots_by_date[holdings_date.isoformat()] = snapshot
    if not snapshots_by_date:
        return [translate_text(locale, "report.concentration_history.unavailable")]

    ordered_snapshots = [snapshots_by_date[key] for key in sorted(snapshots_by_date)]
    latest_values_lines = [
        section_related_context_markdown(locale, "concentration_history"),
        "",
        translate_text(locale, "report.concentration_history.latest_values"),
        "",
        f"| {translate_text(locale, 'report.concentration_history.table_date')} | {translate_text(locale, 'report.concentration_history.table_top5_issued')} | {translate_text(locale, 'report.concentration_history.table_top10_issued')} | {translate_text(locale, 'report.concentration_history.table_top5_ccass')} | {translate_text(locale, 'report.concentration_history.table_top10_ccass')} |",
        "|---|---:|---:|---:|---:|",
    ]
    for snapshot in ordered_snapshots:
        summary = snapshot.holdings_summary
        latest_values_lines.append(
            f"| {_text(snapshot.metadata.holdings_date, locale)} | {_percent(summary.top5_pct_of_issued, locale)} | {_percent(summary.top10_pct_of_issued, locale)} | {_percent(summary.top5_pct_of_ccass, locale)} | {_percent(summary.top10_pct_of_ccass, locale)} |"
        )

    participant_count_lines = [
        "",
        translate_text(locale, "report.concentration_history.participant_count_history"),
        "",
        f"| {translate_text(locale, 'report.concentration_history.table_date')} | {translate_text(locale, 'report.concentration_history.table_participant_count')} |",
        "|---|---:|",
    ]
    for snapshot in ordered_snapshots:
        participant_count_lines.append(
            f"| {_text(snapshot.metadata.holdings_date, locale)} | {snapshot.holdings_summary.participant_count} |"
        )

    return latest_values_lines + participant_count_lines


def _company_information_section(
    announcements: AnnouncementsResponse | None,
    stock_events: StockEventsResponse | None,
    capital_information: CapitalInformationResponse | None,
    officers: OfficersResponse | None,
    locale: str,
) -> list[str]:
    return [
        *_announcements_section(announcements, locale),
        *_stock_events_section(stock_events, locale),
        *_capital_information_section(capital_information, locale),
        *_officers_section(officers, locale),
    ]


def _announcements_section(
    announcements: AnnouncementsResponse | None,
    locale: str,
) -> list[str]:
    lines = [
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[2])}'></a>",
        translate_text(locale, "report.section.announcements"),
        "",
        section_related_context_markdown(locale, "announcements"),
        "",
    ]
    if announcements is None:
        lines.append(translate_text(locale, "ui.hkex_announcements_unavailable"))
        lines.append("")
        return lines

    metadata = announcements.metadata
    lines.extend(
        [
            translate_text(locale, "report.metadata.source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.metadata.data_as_of", value=_text(metadata.data_as_of, locale)),
            translate_text(locale, "report.fetch.fetched_at", value=_datetime(metadata.fetched_at, locale)),
            f"{translate_text(locale, 'ui.hkex_announcements_count')}: {metadata.announcement_count}",
            "",
        ]
    )
    if not announcements.announcements:
        lines.extend([translate_text(locale, "ui.hkex_announcements_empty"), ""])
        return lines

    lines.extend(
        [
            f"| {translate_text(locale, 'ui.hkex_announcements_table_announcement_date')} | {translate_text(locale, 'ui.hkex_announcements_table_title')} | {translate_text(locale, 'ui.hkex_announcements_table_source')} | {translate_text(locale, 'ui.hkex_announcements_table_link')} |",
            "|---|---|---|---|",
        ]
    )
    for row in announcements.announcements:
        link = (
            f"[{translate_text(locale, 'report.link_label')}]({row.link})"
            if row.link
            else translate_text(locale, "report.data_not_available")
        )
        lines.append(
            f"| {_text(row.announcement_date, locale)} | {_escape(row.title)} | {_escape(row.source)} | {link} |"
        )
    lines.append("")
    return lines


def _stock_events_section(
    stock_events: StockEventsResponse | None,
    locale: str,
) -> list[str]:
    lines = [
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[3])}'></a>",
        translate_text(locale, "report.section.stock_events"),
        "",
        section_related_context_markdown(locale, "stock_events"),
        "",
    ]
    if stock_events is None:
        lines.extend([translate_text(locale, "ui.stock_events_unavailable"), ""])
        return lines

    metadata = stock_events.metadata
    source_status = getattr(metadata, "source_status", "pending")
    if source_status == "ready":
        source_note = translate_text(
            locale,
            "ui.stock_events_source_ready",
        )
    elif source_status == "pending":
        source_note = translate_text(locale, "ui.stock_events_source_pending")
    else:
        source_note = translate_text(locale, "ui.stock_events_unavailable")

    lines.extend(
        [
            translate_text(locale, "report.metadata.source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.fetch.fetched_at", value=_datetime(metadata.fetched_at, locale)),
            translate_text(locale, "report.fetch.data_as_of", value=_text(metadata.data_as_of, locale)),
            f"{translate_text(locale, 'ui.stock_events_rows_label')}: {metadata.stock_events_count}",
            source_note,
            translate_text(locale, "ui.stock_events_sorting_note"),
            "",
        ]
    )
    if source_status == "unavailable" and not stock_events.stock_events:
        lines.extend([translate_text(locale, "ui.stock_events_unavailable"), ""])
        return lines
    if not stock_events.stock_events:
        lines.extend([translate_text(locale, "ui.stock_events_empty"), ""])
        return lines

    lines.extend(
        [
            f"| {translate_text(locale, 'ui.stock_events_table_event_date')} | {translate_text(locale, 'ui.stock_events_table_title')} | {translate_text(locale, 'ui.stock_events_table_type')} | {translate_text(locale, 'ui.stock_events_table_source')} | {translate_text(locale, 'ui.stock_events_table_link')} | {translate_text(locale, 'ui.stock_events_table_details')} |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in stock_events.stock_events:
        link = (
            f"[{translate_text(locale, 'report.link_label')}]({row.link})"
            if row.link
            else translate_text(locale, "report.data_not_available")
        )
        lines.append(
            f"| {_text(row.event_date, locale)} | {_escape(row.title)} | {_escape(row.event_type or translate_text(locale, 'report.data_not_available'))} | {_escape(row.source)} | {link} | {_escape(row.details or translate_text(locale, 'report.data_not_available'))} |"
        )
    lines.append("")
    return lines


def _capital_information_section(
    capital_information: CapitalInformationResponse | None,
    locale: str,
) -> list[str]:
    lines = [
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[4])}'></a>",
        translate_text(locale, "report.section.capital_information"),
        "",
        section_related_context_markdown(locale, "capital_information"),
        "",
    ]
    if capital_information is None:
        lines.extend([translate_text(locale, "ui.capital_information_unavailable"), ""])
        return lines

    metadata = capital_information.metadata
    source_status = getattr(metadata, "source_status", "pending")
    if source_status == "ready":
        source_note = translate_text(locale, "ui.capital_information_source_ready")
    elif source_status == "pending":
        source_note = translate_text(locale, "ui.capital_information_source_pending")
    else:
        source_note = translate_text(locale, "ui.capital_information_unavailable")

    lines.extend(
        [
            translate_text(locale, "report.metadata.source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.fetch.fetched_at", value=_datetime(metadata.fetched_at, locale)),
            translate_text(locale, "report.fetch.data_as_of", value=_text(metadata.data_as_of, locale)),
            f"{translate_text(locale, 'ui.capital_information_rows_label')}: {metadata.capital_information_count}",
            source_note,
            translate_text(locale, "ui.capital_information_sorting_note"),
            "",
        ]
    )
    if source_status == "unavailable" and not capital_information.capital_information:
        lines.extend([translate_text(locale, "ui.capital_information_unavailable"), ""])
        return lines
    if not capital_information.capital_information:
        lines.extend([translate_text(locale, "ui.capital_information_empty"), ""])
        return lines

    lines.extend(
        [
            f"| {translate_text(locale, 'ui.capital_information_table_label')} | {translate_text(locale, 'ui.capital_information_table_value')} | {translate_text(locale, 'ui.capital_information_table_unit')} | {translate_text(locale, 'ui.capital_information_table_as_of')} | {translate_text(locale, 'ui.capital_information_table_source')} | {translate_text(locale, 'ui.capital_information_table_note')} | {translate_text(locale, 'ui.capital_information_table_link')} |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in capital_information.capital_information:
        link = (
            f"[{translate_text(locale, 'report.link_label')}]({row.link})"
            if row.link
            else translate_text(locale, "report.data_not_available")
        )
        lines.append(
            f"| {_escape(row.label)} | {_escape(_text(row.value, locale))} | {_escape(_text(row.unit, locale))} | {_escape(_text(row.as_of, locale))} | {_escape(_text(row.source, locale))} | {_escape(_text(row.note, locale))} | {link} |"
        )
    lines.append("")
    return lines


def _officers_section(
    officers: OfficersResponse | None,
    locale: str,
) -> list[str]:
    lines = [
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[5])}'></a>",
        translate_text(locale, "report.section.officers"),
        "",
        section_related_context_markdown(locale, "officers"),
        "",
    ]
    if officers is None:
        lines.extend([translate_text(locale, "ui.officers_unavailable"), ""])
        return lines

    metadata = officers.metadata
    if metadata.source_status == "ready":
        source_note = translate_text(locale, "ui.officers_source_ready")
    elif metadata.source_status == "pending":
        source_note = translate_text(locale, "ui.officers_source_pending")
    else:
        source_note = translate_text(locale, "ui.officers_unavailable")
    lines.extend(
        [
            translate_text(locale, "report.metadata.source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.fetch.fetched_at", value=_datetime(metadata.fetched_at, locale)),
            translate_text(locale, "report.fetch.data_as_of", value=_text(metadata.data_as_of, locale)),
            f"{translate_text(locale, 'ui.officers_rows_label')}: {metadata.officers_count}",
            source_note,
            "",
        ]
    )
    if not officers.officers:
        lines.extend([translate_text(locale, "ui.officers_empty"), ""])
        return lines

    lines.extend(
        [
            f"| {translate_text(locale, 'ui.officers_table_name')} | {translate_text(locale, 'ui.officers_table_positions')} | {translate_text(locale, 'ui.officers_table_tenure_from')} | {translate_text(locale, 'ui.officers_table_tenure_to')} | {translate_text(locale, 'ui.officers_table_is_current')} | {translate_text(locale, 'ui.officers_table_sex')} | {translate_text(locale, 'ui.officers_table_age')} | {translate_text(locale, 'ui.officers_table_education')} | {translate_text(locale, 'ui.officers_table_salary')} | {translate_text(locale, 'ui.officers_table_biography')} |",
            "|---|---|---|---|---|---|---:|---|---|---|",
        ]
    )
    for row in officers.officers:
        positions = ", ".join(row.positions) if row.positions else translate_text(locale, "report.data_not_available")
        lines.append(
            "| "
            f"{_escape(row.name)} | "
            f"{_escape(positions)} | "
            f"{_escape(_text(row.tenure_from, locale))} | "
            f"{_escape(_text(row.tenure_to, locale))} | "
            f"{_yes_no(row.is_current, locale)} | "
            f"{_escape(_text(row.sex, locale))} | "
            f"{_escape(_text(row.age, locale))} | "
            f"{_escape(_text(row.education, locale))} | "
            f"{_escape(_text(row.salary, locale))} | "
            f"{_escape(_text(row.biography, locale))} |"
        )
    lines.append("")
    return lines


def _price_history_section(price_history: PriceHistoryResponse | None, locale: str) -> list[str]:
    lines = [
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[14])}'></a>",
        translate_text(locale, "report.section.price_history"),
        "",
        section_related_context_markdown(locale, "price_history"),
        "",
    ]
    if price_history is None:
        lines.append(translate_text(locale, "report.price_history.unavailable"))
        return lines + [""]

    metadata = price_history.metadata
    lines.extend(
        [
            translate_text(locale, "report.price_history.metadata_heading"),
            "",
            f"| {translate_text(locale, 'report.table.metric')} | {translate_text(locale, 'report.table.value')} |",
            "|---|---|",
            translate_text(locale, "report.price_history.metadata_source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.price_history.metadata_source_url", value=_text(metadata.source_url, locale)),
            translate_text(locale, "report.price_history.metadata_price_date_from", value=_text(metadata.price_date_from, locale)),
            translate_text(locale, "report.price_history.metadata_price_date_to", value=_text(metadata.price_date_to, locale)),
            translate_text(locale, "report.price_history.metadata_adjustment_state", value=metadata.adjustment_state),
            translate_text(locale, "report.price_history.metadata_currency", value=_text(metadata.currency, locale)),
            translate_text(locale, "report.price_history.metadata_adjustment_note", value=_text(metadata.adjustment_note, locale)),
            translate_text(locale, "report.price_history.metadata_fetched_at", value=_datetime(metadata.fetched_at, locale)),
            "",
            translate_text(locale, "report.price_history.table_heading"),
            "",
        ]
    )
    if not price_history.prices:
        lines.extend([translate_text(locale, "report.price_history.no_rows"), ""])
        return lines

    lines.extend(
        [
            f"| {translate_text(locale, 'report.price_history.table_date')} | {translate_text(locale, 'report.price_history.table_open')} | {translate_text(locale, 'report.price_history.table_high')} | {translate_text(locale, 'report.price_history.table_low')} | {translate_text(locale, 'report.price_history.table_close')} | {translate_text(locale, 'report.price_history.table_adjusted_close')} | {translate_text(locale, 'report.price_history.table_volume')} | {translate_text(locale, 'report.price_history.table_turnover')} |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in price_history.prices:
        lines.append(
            "| "
            + " | ".join(
                [
                    _text(row.price_date, locale),
                    _decimal(row.open, locale),
                    _decimal(row.high, locale),
                    _decimal(row.low, locale),
                    _decimal(row.close, locale),
                    _decimal(row.adjusted_close, locale),
                    _integer(row.volume, locale),
                    _money(row.turnover, locale),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _change_table(changes: tuple[HoldingChange, ...], locale: str) -> list[str]:
    if not changes:
        return [translate_text(locale, "report.no_participant_changes")]
    lines = [
        f"| {translate_text(locale, 'report.change_table.ccass_id')} | {translate_text(locale, 'report.change_table.participant')} | {translate_text(locale, 'report.change_table.previous')} | {translate_text(locale, 'report.change_table.current')} | {translate_text(locale, 'report.change_table.change')} | {translate_text(locale, 'report.change_table.pp_change')} | {translate_text(locale, 'report.change_table.status')} |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for change in changes:
        lines.append(
            f"| {_escape(change.participant_id)} | {_escape(change.participant)} | "
            f"{change.previous_shares:,} | {change.current_shares:,} | "
            f"{change.share_change:+,} | {change.pct_point_change:+.4f} | {change.status} |"
        )
    return lines


def _integer(value: int | None, locale: str) -> str:
    return f"{value:,}" if value is not None else translate_text(locale, "report.data_not_available")


def _decimal(value: float | None, locale: str) -> str:
    return f"{value:.4f}" if value is not None else translate_text(locale, "report.data_not_available")


def _money(value: float | None, locale: str) -> str:
    return f"{value:,.2f}" if value is not None else translate_text(locale, "report.data_not_available")


def _percent(value: float | None, locale: str) -> str:
    return f"{value:.4f}%" if value is not None else translate_text(locale, "report.data_not_available")


def _datetime(value, locale: str) -> str:
    return value.isoformat() if value else translate_text(locale, "report.data_not_available")


def _text(value: object | None, locale: str) -> str:
    return _escape(str(value)) if value is not None and str(value) else translate_text(locale, "report.data_not_available")


def _yes_no(value: bool, locale: str) -> str:
    return translate_text(locale, "report.comparison.available") if value else translate_text(locale, "report.comparison.unavailable")


def _localize_warning(warning: str, locale: str) -> str:
    parsed = parse_warning(warning)
    mapping = {
        "The current result came from a cached or snapshot data source.": "report.warning.cached_snapshot_source",
        "The holdings date is unavailable.": "report.warning.holdings_date_unavailable",
        "Change analysis is unavailable because no previous snapshot was supplied.": "report.warning.change_analysis_unavailable",
    }
    if warning in mapping:
        return translate_text(locale, mapping[warning])
    prefix = "Previous-snapshot enrichment is unavailable ("
    if warning.startswith(prefix) and warning.endswith(")."):
        exception_name = warning[len(prefix):-2]
        return translate_text(
            locale,
            "report.warning.previous_snapshot_enrichment_unavailable",
            exception_name=exception_name,
        )
    if parsed is not None and parsed.prefix == "DATA_LIMITATION" and parsed.code == "PREVIOUS_SNAPSHOT_ENRICHMENT_UNAVAILABLE":
        exception_name = parsed.message
        prefix = "Previous-snapshot enrichment is unavailable ("
        if exception_name.startswith(prefix) and exception_name.endswith(")."):
            exception_name = exception_name[len(prefix):-2]
        return translate_text(
            locale,
            "report.warning.previous_snapshot_enrichment_unavailable",
            exception_name=exception_name,
        )
    if parsed is not None and parsed.prefix == "DATA_LIMITATION" and parsed.code == "PRICE_HISTORY_UNAVAILABLE":
        return translate_text(locale, "report.warning.price_history_unavailable", value=parsed.message or parsed.code)
    if parsed is not None and parsed.message:
        return parsed.message
    if parsed is not None:
        if parsed.prefix == "SOURCE_ERROR_CODE":
            return f"Source error code: {parsed.code}"
        if parsed.prefix == "SOURCE_ERROR_MESSAGE":
            return f"Source error message: {parsed.code}"
        if parsed.prefix == "SOURCE_ERROR_RETRY_RECOMMENDED":
            return f"Source retry recommended: {parsed.code}"
        if parsed.prefix == "SOURCE_ERROR_RETRY_AFTER_SECONDS":
            return f"Source retry-after seconds: {parsed.code}"
        if parsed.prefix == "LKG_RETRIEVED_AT":
            return f"Last-known-good retrieved at: {parsed.code}"
        if parsed.prefix == "LKG_AGE_SECONDS":
            return f"Last-known-good age seconds: {parsed.code}"
        if parsed.prefix == "SERVED_AT":
            return f"Served at: {parsed.code}"
        if parsed.prefix == "DATA_LIMITATION" and parsed.code == "PARTIAL_DATA":
            return "Partial data: participant rows are truncated or incomplete; missing rows remain absent."
        if parsed.prefix == "PARTIAL_DATA":
            return f"Partial data: {parsed.code}"
        if parsed.prefix == "FRESHNESS_STATUS" and parsed.code == "FRESH":
            return "The current result came from a fresh live source."
        if parsed.prefix == "FRESHNESS_STATUS" and parsed.code == "STALE_LKG":
            return "The current result came from a cached or snapshot data source."
    return warning


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
