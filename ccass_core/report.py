
from __future__ import annotations

import re
import warnings
from collections.abc import Sequence

from app.models import CcassResponse
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
        "ui.chart_help_announcements_body": "Use official announcement dates, categories, titles, file info, and URLs to align events with holdings and price movement. Tags are only objective classifications; they are not conclusions.",
        "ui.hkex_announcements_heading": "HKEX Announcements",
        "ui.hkex_announcements_caption": "Read-only surface for official announcements. Columns cover publish time, category, title, file info / size, official URL, and objective event tags.",
        "ui.hkex_announcements_count": "Announcement count",
        "ui.hkex_announcements_rows_label": "Announcement rows",
        "ui.hkex_announcements_sorting_note": "Sorted by publish time, newest first.",
        "ui.hkex_announcements_empty": "No announcement rows are available in the approved read-only surface.",
        "ui.hkex_announcements_unavailable": "Announcement data is unavailable in the current fetch result.",
        "ui.hkex_announcements_export_heading": "Export labels",
        "ui.hkex_announcements_export_note": "Export-related labels remain available even when announcement rows are empty.",
        "ui.hkex_announcements_export_csv_label": "CSV export",
        "ui.hkex_announcements_export_excel_label": "Excel workbook export",
        "ui.hkex_announcements_table_publish_time": "Publish time",
        "ui.hkex_announcements_table_category": "Category",
        "ui.hkex_announcements_table_title": "Title",
        "ui.hkex_announcements_table_file_info": "File info / size",
        "ui.hkex_announcements_table_official_url": "Official URL",
        "ui.hkex_announcements_table_event_tags": "Objective event tags",
        "ui.report_navigation_heading": "Report Navigation",
        "ui.report_navigation_caption": "Jump links follow the rendered report sections below.",
        "ui.data_quality_heading": "Data Quality / Warnings",
        "ui.data_quality_caption": "Objective warnings, unavailable states, and missing-data notes.",
        "ui.data_quality_help_caption": "These warnings describe completeness, quality, and system limitations. They are not investment advice, trading signals, or stock ratings.",
        "ui.data_quality_no_warnings": "No data quality warnings were generated.",
        "ui.data_quality_unavailable": "Data quality warnings are unavailable for this result.",
        "ui.full_summary_heading": "Full Summary",
        "ui.full_summary_caption": "Summary of the currently loaded result and visible surfaces.",
        "ui.full_summary_table_section": "Section",
        "ui.full_summary_table_status": "Status",
        "ui.full_summary_table_note": "Note",
        "ui.full_summary_status_available": "available",
        "ui.full_summary_status_unavailable": "unavailable",
        "ui.full_summary_unavailable": "Full Summary is unavailable until a result has been fetched.",
        "ui.full_summary_note_fetch_summary": "Report sections and metadata are ready.",
        "ui.full_summary_note_company": "Code {code} / Issue ID {issue_id}",
        "ui.full_summary_note_holdings": "{participant_count} participant rows.",
        "ui.full_summary_note_changes_available": "Previous snapshot is available.",
        "ui.full_summary_note_changes_unavailable": "Previous snapshot is unavailable.",
        "ui.full_summary_note_big_changes_available": "Thresholded change review is available.",
        "ui.full_summary_note_big_changes_unavailable": "Thresholded change review is unavailable.",
        "ui.full_summary_note_concentration": "Top 5 / issued {top5_pct_of_issued} | Top 10 / issued {top10_pct_of_issued}",
        "ui.full_summary_note_concentration_history": "{snapshot_count} dated snapshots.",
        "ui.full_summary_note_price_history": "Price history is unavailable in the current result.",
        "ui.full_summary_note_raw_previews": "{table_count} parsed tables.",
        "ui.full_summary_note_downloads": "Combined CSV, workbook, and Markdown report.",
        "ui.full_summary_note_data_quality_no_warnings": "No data quality warnings were generated.",
        "ui.full_summary_note_data_quality_warnings": "{warning_count} data quality warning(s).",
        "ui.all_parsed_tables_heading": "All Parsed Tables",
        "ui.all_parsed_tables_caption": "The rendered report sections below follow the parsed-table order.",
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
        "ui.raw_previews_heading": "Raw Table Previews",
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
        "ui.downloads_workflow_caption": "Choose the artifact you want to download. Combined CSV, Excel workbook, Markdown report, and section-specific exports reuse the fetched result.",
        "ui.downloads_combined_csv": "All CCASS Data CSV",
        "ui.downloads_excel_workbook": "Excel - All Sections",
        "ui.downloads_report_markdown": "Report Markdown",
        "ui.downloads_download_combined_csv": "Download All CCASS Data CSV",
        "ui.downloads_download_excel_workbook": "Download Excel",
        "ui.downloads_download_markdown_report": "Download Markdown report",
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
        "nav.all_tables": "All Tables",
        "nav.dt_rainbow": "DT Rainbow",
        "nav.hkex_announcements": "HKEX Announcements",
        "nav.company": "Company",
        "nav.holdings": "Holdings",
        "nav.changes": "Changes",
        "nav.big_changes": "Big Changes",
        "nav.concentration": "Concentration",
        "nav.price": "Price",
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
        "report.section.data_quality_warnings": "## Data Quality Warnings",
        "report.fetch.status_success": "- Status: SUCCESS",
        "report.fetch.source": "- Source: {value}",
        "report.fetch.fetched_at": "- Fetched at: {value}",
        "report.fetch.holdings_date": "- Holdings date: {value}",
        "report.fetch.cached_snapshot": "- Cached/snapshot: {value}",
        "report.metadata.code": "- Code: {value}",
        "report.metadata.stock_name": "- Stock name: {value}",
        "report.metadata.issue_id": "- Issue ID: {value}",
        "report.metadata.source_url": "- Source URL: {value}",
        "report.metadata.settlement_note": "- Settlement note: {value}",
        "report.metadata.attribution": "- Attribution: {value}",
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
        "ui.chart_help_announcements_body": "???????????????????? URL??????????????????????????????",
        "ui.hkex_announcements_heading": "HKEX 公告",
        "ui.hkex_announcements_caption": "只讀公告表面，用於顯示官方公告。欄位涵蓋發布時間、類別、標題、檔案資訊／大小、官方 URL 及客觀事件標籤。",
        "ui.hkex_announcements_count": "公告數量",
        "ui.hkex_announcements_rows_label": "公告列表",
        "ui.hkex_announcements_sorting_note": "按發布時間排序，最新在前。",
        "ui.hkex_announcements_empty": "在已批准的只讀表面中，目前沒有可用的公告列。",
        "ui.hkex_announcements_unavailable": "目前的抓取結果沒有公告資料。",
        "ui.hkex_announcements_export_heading": "匯出標籤",
        "ui.hkex_announcements_export_note": "即使公告列為空，相關匯出標籤仍會保留。",
        "ui.hkex_announcements_export_csv_label": "CSV 匯出",
        "ui.hkex_announcements_export_excel_label": "Excel 活頁簿匯出",
        "ui.hkex_announcements_table_publish_time": "發布時間",
        "ui.hkex_announcements_table_category": "類別",
        "ui.hkex_announcements_table_title": "標題",
        "ui.hkex_announcements_table_file_info": "檔案資訊／大小",
        "ui.hkex_announcements_table_official_url": "官方 URL",
        "ui.hkex_announcements_table_event_tags": "客觀事件標籤",
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
        "ui.fetch_summary_remaining": "?????????????????????",
        "ui.raw_previews_heading": "原始表格預覽",
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
        "ui.copy_for_chatgpt_caption": "?????????? ChatGPT?????????????????????????",
        "ui.copy_report": "????",
        "ui.downloads_heading": "下載本股票",
        "ui.downloads_unavailable": "成功抓取後才可下載。",
        "ui.downloads_caption": "直接從已抓取的回應下載目前報告產物。",
        "ui.downloads_workflow_heading": "????",
        "ui.downloads_workflow_caption": "??????????? CSV?Excel ????Markdown ????????????????",
        "ui.downloads_combined_csv": "全部 CCASS 資料 CSV",
        "ui.downloads_excel_workbook": "Excel - 全部章節",
        "ui.downloads_report_markdown": "報告 Markdown",
        "ui.downloads_download_combined_csv": "下載全部 CCASS 資料 CSV",
        "ui.downloads_download_excel_workbook": "下載 Excel",
        "ui.downloads_download_markdown_report": "下載 Markdown 報告",
        "ui.downloads_csv_preview": "CSV 內容預覽",
        "ui.downloads_first_80_csv_lines": "? 80 ? CSV",
        "ui.downloads_section_specific": "??????",
        "ui.downloads_raw_preview_summary_csv": "?????? CSV",
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
        "ui.full_summary_note_fetch_summary": "?????????????",
        "ui.full_summary_note_company": "?? {code} / Issue ID {issue_id}",
        "ui.full_summary_note_holdings": "{participant_count} ???????",
        "ui.full_summary_note_changes_available": "?????????",
        "ui.full_summary_note_changes_unavailable": "?????????",
        "ui.full_summary_note_big_changes_available": "??????????",
        "ui.full_summary_note_big_changes_unavailable": "??????????",
        "ui.full_summary_note_concentration": "? 5 / issued {top5_pct_of_issued} | ? 10 / issued {top10_pct_of_issued}",
        "ui.full_summary_note_concentration_history": "{snapshot_count} ??????",
        "ui.full_summary_note_price_history": "????????????",
        "ui.full_summary_note_raw_previews": "{table_count} ??????",
        "ui.full_summary_note_downloads": "?? CSV????? Markdown ???",
        "ui.full_summary_note_data_quality_no_warnings": "??????????",
        "ui.full_summary_note_data_quality_warnings": "{warning_count} ????????",
        "ui.all_parsed_tables_heading": "??????",
        "ui.all_parsed_tables_caption": "??????????????????",
        "nav.fetch_summary": "????",
        "nav.full_summary": "??????",
        "nav.all_tables": "????",
        "nav.dt_rainbow": "DT Rainbow",
        "nav.hkex_announcements": "HKEX ??",
        "nav.company": "??",
        "nav.holdings": "??",
        "nav.changes": "??",
        "nav.big_changes": "???",
        "nav.concentration": "???",
        "nav.price": "??",
        "nav.raw_previews": "????",
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
        "report.section.fetch_summary": "## ????",
        "report.section.company": "## 公司",
        "report.company.lookup_status": "- 查詢狀態：{value}",
        "report.company.lookup_method": "- 查詢方法：{value}",
        "report.company.lookup_status.success": "成功",
        "report.company.lookup_method.extracted_from_url": "從 URL 擷取",
        "report.company.metadata_resolution_note": "已解析的 metadata 與查詢詳情僅供驗證用途。",
        "report.section.metadata": "## ????",
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
        "report.section.data_quality_warnings": "## ??????",
        "report.fetch.status_success": "- ?????",
        "report.fetch.source": "- ???{value}",
        "report.fetch.fetched_at": "- ?????{value}",
        "report.fetch.holdings_date": "- ?????{value}",
        "report.fetch.cached_snapshot": "- ??/???{value}",
        "report.metadata.code": "- ???{value}",
        "report.metadata.stock_name": "- ?????{value}",
        "report.metadata.issue_id": "- Issue ID?{value}",
        "report.metadata.source_url": "- ?????{value}",
        "report.metadata.settlement_note": "- ?????{value}",
        "report.metadata.attribution": "- ?????{value}",
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
    "fetch_summary",
    "company",
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


def build_markdown_report(
    response: CcassResponse | None,
    *,
    code: str,
    analysis: AnalysisResult | None = None,
    fetch_error: str | None = None,
    history_snapshots: Sequence[CcassResponse] | None = None,
    locale: str = DEFAULT_LOCALE,
) -> str:
    stock_name = response.metadata.name if response and response.metadata.name else translate_text(locale, "report.data_not_available")
    lines = [f"# {translate_text(locale, 'report.title')} ? {code} {stock_name}", ""]

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
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[1])}'></a>",
            translate_text(locale, "report.section.fetch_summary"),
            "",
            translate_text(locale, "report.fetch.status_success"),
            translate_text(locale, "report.fetch.source", value=_text(metadata.source_name, locale)),
            translate_text(locale, "report.fetch.fetched_at", value=_datetime(metadata.fetched_at, locale)),
            translate_text(locale, "report.fetch.holdings_date", value=_text(metadata.holdings_date, locale)),
            translate_text(locale, "report.fetch.cached_snapshot", value=_yes_no(metadata.cached, locale)),
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[2])}'></a>",
            translate_text(locale, "report.section.company"),
            "",
            translate_text(locale, "report.metadata.stock_name", value=_text(metadata.name, locale)),
            translate_text(locale, "report.metadata.code", value=metadata.code),
            translate_text(locale, "report.metadata.issue_id", value=metadata.issue_id),
            translate_text(locale, "report.company.lookup_status", value=translate_text(locale, "report.company.lookup_status.success")),
            translate_text(locale, "report.company.lookup_method", value=translate_text(locale, "report.company.lookup_method.extracted_from_url")),
            translate_text(locale, "report.company.metadata_resolution_note"),
            translate_text(locale, "report.metadata.source_url", value=_text(metadata.source_url, locale)),
            translate_text(locale, "report.metadata.settlement_note", value=_text(metadata.settlement_note, locale)),
            translate_text(locale, "report.metadata.attribution", value=_text(metadata.attribution, locale)),
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[3])}'></a>",
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
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[4])}'></a>",
            translate_text(locale, "report.section.holdings"),
            "",
        ]
    )
    lines.extend(_holdings_table(response, locale))
    lines.extend([
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[5])}'></a>",
        translate_text(locale, "report.section.changes"),
        "",
    ])
    lines.extend(_changes_section(computed, locale))
    lines.extend([
        "",
        f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[6])}'></a>",
        translate_text(locale, "report.section.big_changes"),
        "",
    ])
    lines.extend(_big_changes_section(computed, locale))
    lines.extend(
        [
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[7])}'></a>",
            translate_text(locale, "report.section.concentration"),
            "",
            f"| {translate_text(locale, 'report.table.metric')} | {translate_text(locale, 'report.table.value')} |",
            "|---|---:|",
            f"| Top 5 / issued | {_percent(summary.top5_pct_of_issued, locale)} |",
            f"| Top 10 / issued | {_percent(summary.top10_pct_of_issued, locale)} |",
            f"| Top 5 / CCASS | {_percent(summary.top5_pct_of_ccass, locale)} |",
            f"| Top 10 / CCASS | {_percent(summary.top10_pct_of_ccass, locale)} |",
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[8])}'></a>",
            translate_text(locale, "report.section.concentration_history"),
            "",
        ]
    )
    lines.extend(_concentration_history_section(response, history_snapshots, locale))
    lines.extend([
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[9])}'></a>",
            translate_text(locale, "report.section.price_history"),
            "",
            translate_text(locale, "report.price_history.unavailable"),
            "",
            f"<a id='{localized_report_anchor(REPORT_SECTION_KEYS[10])}'></a>",
            translate_text(locale, "report.section.data_quality_warnings"),
            "",
        ]
    )
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
    lines = _change_table(analysis.changes, locale)
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
    return _change_table(analysis.big_changes, locale)


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


def _percent(value: float | None, locale: str) -> str:
    return f"{value:.4f}%" if value is not None else translate_text(locale, "report.data_not_available")


def _datetime(value, locale: str) -> str:
    return value.isoformat() if value else translate_text(locale, "report.data_not_available")


def _text(value: object | None, locale: str) -> str:
    return _escape(str(value)) if value is not None and str(value) else translate_text(locale, "report.data_not_available")


def _yes_no(value: bool, locale: str) -> str:
    return translate_text(locale, "report.comparison.available") if value else translate_text(locale, "report.comparison.unavailable")


def _localize_warning(warning: str, locale: str) -> str:
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
    return warning


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
