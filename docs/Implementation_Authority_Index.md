# Implementation Authority Index

This index routes implementation and test decisions to the right authority without re-reading source documents unless the evidence is unclear.

## Authority hierarchy

1. 8504 baseline evidence is the final UI / UX contract for presentation, labels, layout, section order, and interaction behavior.
2. `docs/Source_Documents_to_8504_Mapping.md` is the primary implementation map for data source, contract, and date-convention decisions.
3. `docs/Reference_Website_Feature_Inventory.md` is feature / flow / display reference only.
4. Original source documents are read only when the mapping or baseline evidence is `Unconfirmed`, `Conflict`, or insufficient.

Reference Website evidence never overrides the formal source documents for data source or contract decisions.

## Routing table

| Task Type | Primary Authority | Secondary Evidence | Source Document only if needed | Escalation Rule |
|---|---|---|---|---|
| UI / UX, headings, captions, section order, navigation anchors, button labels | 8504 baseline evidence | Reference Website Feature Inventory | No, unless the baseline itself is unclear | If 8504 and tests disagree, treat tests as stale unless the approved baseline says otherwise |
| Holdings | Source Documents → 8504 Mapping | 8504 baseline evidence | Holdings / CCASS requirement documents | If mapping says `Existing / Working`, do not reopen source docs |
| Changes | Source Documents → 8504 Mapping | 8504 baseline evidence | Changes / snapshot comparison requirement documents | If contract wording or T+2 semantics are unclear, read the relevant date-convention and holdings docs |
| Big Changes | Source Documents → 8504 Mapping | 8504 baseline evidence | Big Changes requirement documents | If threshold or compare basis is unclear, escalate to the formal requirement only |
| Concentration | Source Documents → 8504 Mapping | 8504 baseline evidence | Concentration requirement documents | If issued-shares basis, warning semantics, or denominator timing are unclear, read the formal date convention and concentration docs |
| Price / Turnover History | Source Documents → 8504 Mapping | 8504 baseline evidence | Price / turnover requirement documents | If source priority, fields, or fallback behavior are unclear, escalate to the source document set only |
| Company | Source Documents → 8504 Mapping | 8504 baseline evidence | Company / identity requirement documents | If lookup status or identity contract is `Unconfirmed`, read the source document set |
| HKEX Announcements | Source Documents → 8504 Mapping | 8504 baseline evidence, Reference inventory | Announcements source / format documents | If visible rows or field names conflict, follow the mapping and the formal document |
| Events | Source Documents → 8504 Mapping | 8504 baseline evidence, Reference inventory | Events source / format documents | If source approval or row schema is uncertain, mark as `Unconfirmed` until formal evidence exists |
| Officers | Source Documents → 8504 Mapping | 8504 baseline evidence, Reference inventory | Officers source / format documents | If visibility or current-state semantics are unclear, prefer the mapping and preserve warnings |
| Capital | Source Documents → 8504 Mapping | 8504 baseline evidence, Reference inventory | Capital-information source documents | If contract shape or date basis is unclear, keep the current surface and escalate only the uncertain field |
| Rainbow / DT Rainbow / history visuals | Source Documents → 8504 Mapping | Reference Website Feature Inventory | CCASS Rainbow / DT Rainbow evidence only if the mapping is insufficient | If a feature is reference-visible but not formally required, treat it as reference-only |
| Copy / Report / Downloads | Source Documents → 8504 Mapping | 8504 baseline evidence, Reference Website Feature Inventory | Export / report requirement docs | If export format or payload source is unclear, keep the report builder as the single source of truth |
| AI objective data / handoff / metadata / provenance | Source Documents → 8504 Mapping | Contract docs for AI read model / handoff | AI handoff / provenance contract docs only if needed | If the AI objective is about data handoff, do not infer investment logic; use the contract docs only |
| Performance / lazy loading / optional heavy sections | 8504 baseline evidence | Reference Website Feature Inventory | Performance requirement docs only if the baseline is unclear | If a section is optional or heavy in the baseline, keep it lazy / collapsed unless the contract says otherwise |

## Escalation rules

- If the mapping says `Existing / Working`, keep the existing implementation and do not reopen source docs.
- If the mapping says `Partial`, change only the minimum surface required by the approved baseline.
- If the mapping says `Missing`, change only the smallest code surface needed to satisfy the formal source requirement.
- If the mapping says `Existing but Wrong Source` or `Existing but Wrong Format`, treat it as a contract fix, not a UX redesign.
- If the mapping, baseline evidence, and tests conflict, treat the baseline evidence as the presentation authority and the source documents as the data authority.
- If an item is `Unconfirmed`, do not guess; route to the relevant source document and keep the current implementation stable until evidence is available.

## Practical use

Before editing code or tests:

1. Check `docs/Source_Documents_to_8504_Mapping.md`.
2. Check `docs/Reference_Website_Feature_Inventory.md` only for visible UI / flow reference.
3. Check the approved 8504 baseline evidence for the actual text / interaction contract.
4. Read original source documents only when the mapping says `Unconfirmed`, `Conflict`, or insufficient.

This index is for routing only. It does not redefine product scope or add new requirements.
