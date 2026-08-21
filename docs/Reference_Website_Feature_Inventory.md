# Reference Website Feature Inventory

Discovery scope: actual reference website behavior observed with stock `00700` and `01592` through Browser / Playwright MCP.

Status legend:

- Matched
- Partial
- Missing
- Different
- Unconfirmed

## Feature Inventory

| Feature | Page / Section | User Action | Input | Visible Output | Data / Fields | URL / Route | Current Joe Implementation 對應 | Status | Gap / Note |
|---|---|---|---|---|---|---|---|---|---|
| Stock search / fetch | Input / top form | Enter stock and fetch | Stock Code or Webb-site Issue ID, timeout, HKEX announcement period, headless switch | Fetch starts and page populates with sections | code, issue id, timeout, announcement period, headless flag | Same page, in-page fetch; no visible route change | Stock input / fetch flow exists in 8504-like UI | Partial | Reference has two input modes and more explicit runtime controls |
| Metadata resolution | Resolved Metadata | Inspect identity and source path | stock code / issue id | Stock name, issue id, source mode, source used, mirror status, mapping method | stock code, name, issue id, lookup status, source mode, source used, mirror base URL, local history depth | In-page section | Metadata section exists in Joe clone | Partial | Reference shows detailed source-resolution provenance |
| Holdings | Holdings | Review CCASS holdings table | fetched stock | Holdings summary cards + holdings table | rank, participant, CCASS id, holding, stake %, cumulative % | `#holdings` | Holdings section exists | Partial | 00700 holdings failed/fallback; 01592 populated from local snapshot DB |
| Changes | Changes | Review participant movement | fetched stock | Changes table / fallback warning | participant, change, change %, holding after, stake after | `#changes` | Changes section exists | Partial | 00700 daily changes failed; 01592 changes limited by local history |
| Big Changes | Big Changes | Review large movers | fetched stock | Big Changes table | date, participant, change %, change in shares, metadata | `#big-changes` | Big Changes section exists | Matched | Same major concept visible; current source path may differ |
| Concentration | Concentration | Review concentration stats | fetched stock | Concentration table + summary | Top 5, Top 10, Top 10+NCIP, stake in CCASS, warnings | `#concentration` | Concentration section exists | Partial | 01592 showed abnormal stale/scale warning; issued-share semantics need mapping |
| Concentration history / rainbow | DT Rainbow | Generate historical rainbow | top N, history count, merge price option | Rainbow control + generated chart | historical dates, major participants, price overlay | `#dt-rainbow` | Rainbow surface exists or equivalent | Partial | Reference exposes explicit generation controls and history depth |
| Price / turnover history | Price & Turnover History | Inspect price chart / ranges | range, bars, event lines | KPI cards + chart + download PNG/fullscreen | date, close, open/high/low, volume, turnover, VWAP, estimates | `#price-turnover` / `#price-history` | Price history section exists | Partial | Reference has richer chart controls and quote link integration |
| HKEX announcements | HKEX Announcements | Inspect announcement list | fetched stock, date period | announcement table/list | publish time, category, title, file info, URL, count | `#hkex-announcements` | Announcements section exists | Matched | Public HKEXnews source exposed in reference |
| Corporate events | 財技事件 Events | Inspect events section | fetched stock | events section / table | event fields, warning / empty state | `#corporate-events` | Corporate events section exists | Partial | Visible section exists; row data and source continuity need mapping |
| Share capital changes | Share capital changes | Inspect capital changes | fetched stock | capital table / warning | date, capital / issued shares, change, reason/type, source, URL, language | section anchor visible | Capital section exists | Partial | Visible section exists; source fidelity not fully confirmed |
| Officers / managers | 董事高管 Officers | Inspect officers | fetched stock | officers table / warning | name, role, dates, source | `#officers` | Officers section exists | Partial | Visible section exists; source/fields need alignment |
| Company / orgdata | Company | Inspect company metadata | fetched stock | company metadata table | company name, identifiers, metadata | `#company` | Company section exists | Partial | Reference has explicit company section with parsed tables |
| Raw table previews | Raw Table Previews | Expand raw tables | fetched stock | raw table previews | raw upstream tables and shapes | `#raw-table-previews` | Raw preview surface exists | Matched | Important diagnostic surface present |
| Fetch summary | Fetch Summary | Review data quality / warnings | fetched stock | warnings, notes, diagnostics | source diagnostics, failures, fallback notices | `#fetch-summary` | Fetch summary exists | Matched | Reference preserves failure visibility rather than hiding it |
| Copy for ChatGPT | Copy for ChatGPT | Copy report text | fetched stock | copy-to-clipboard / report text | markdown report and summary text | `#copy-for-chat-gpt` | Copy / report surface exists | Matched | Same high-value handoff surface visible |
| Downloads / export | Download Files | Download outputs | fetched stock | CSV / Excel / JSON / markdown buttons | section exports, raw tables | `#download-files` | Download section exists | Matched | Reference exposes multiple export formats |
| Sidebar / controls | Sidebar / top controls | Change fetch options before loading | input mode, timeout, period, headless | clear control cluster | switch, spinbutton, combobox, buttons | top form | Joe clone has comparable controls in 8504 | Partial | Reference control layout is more explicit and polished |
| URL / route pattern | In-page anchors | Jump to section | anchor links | one-page anchor navigation | `#fetch-summary`, `#holdings`, etc. | same page anchors | Joe clone has analogous sections | Partial | Reference is anchor-driven single-page flow |

## Main Missing / Different Items

- 00700 exposes a clear split between populated price/announcement data and failed holdings/changes fetches; Joe clone needs the same fail-loud, section-preserving behavior.
- Reference has stronger metadata/provenance surfacing around source mode, mirror status, and lookup method.
- Reference exposes richer chart controls for price/turnover and a DT Rainbow generation path.
- Corporate events, share capital changes, and officers are visible as first-class sections, but the exact row-level content and source fidelity still need mapping against Joe.
- The reference website is anchor-driven and single-page; Joe clone mapping is close, but exact visual fidelity remains partial.

## HC-04 Targeted Gap Fill

### Observed UI Evidence

- The reference site still exposes the same top-level one-page layout and anchor-driven flow already listed above.
- The input surface is visible immediately on load and includes:
  - `Stock Code` / `Webb-site Issue ID` mode switch
  - stock / issue text input
  - timeout control
  - HKEX announcements period control
  - Playwright headless switch
  - `Fetch Webb-site Data` action
- The page also exposes loading / status feedback during fetch, including the visible `Resolving Webb-site issue ID...` state and the initial guidance text prompting the user to enter an input and click fetch.
- The page title / heading and resolved-metadata block remain visible before downstream data sections load.

### Upstream Note

- In this browser pass, fetch attempts for `01592` and `00700` remained in the visible loading state and did not advance to downstream tables.
- That upstream outcome is recorded here only as operational evidence for this pass; it is not being used to classify the UI feature itself as failed.

### Remaining UI Evidence Gap

- Downstream row-level UI evidence for `Corporate Events`, `Share Capital Changes`, `Officers / managers`, and the deeper `DT Rainbow` controls was not refreshed in this pass because the browser session did not advance past the loading state.
- `Corporate Events` stays locked in the inventory as a visible first-class section; it is not being re-opened by this UI-only pass.
- `Share Capital Changes` and `Officers / managers` remain Partial with incomplete UI evidence rather than a confirmed UI failure.
- **Recommended next mainline feature:** `Share Capital Changes`, because it still has the clearest mix of visible section presence and incomplete row-level UI evidence in the inventory.

## Source Documents Conflict

No hard conflict was confirmed in this discovery pass.

Observed reference behavior and source-document intent are broadly aligned at the UI/product-surface level, but some source-routing and data-population behavior still need explicit mapping before they can be treated as implementation requirements.

## Ready for Source Documents → 8504 Mapping?

Yes.

We have enough live reference evidence to begin the next mapping step.
