# ND-03 Implementation Plan

## 1. Objective

Define future evaluation and implementation direction for remaining capability gaps.

This plan is based on the available ND-01 and ND-02 review evidence and `REFERENCE_EVIDENCE.md`. The referenced `ND-03_SCOPE_DECISION.md` file was not present in the repository at the time of drafting, so this document is intentionally limited to planning and evaluation direction only.

---

## 2. Planned Work Items

### ND-03-I001 DT Rainbow Full Capability Evaluation

Include:

- required data
- calculation dependency review
- performance consideration
- user-triggered loading design

Exclude:

- unknown algorithm reproduction
- immediate implementation

Evaluation focus:

- identify whether a stable and explainable DT Rainbow data contract can be defined from approved sources
- separate visual presentation needs from any analytical or ranking logic
- confirm whether the user-triggered loading pattern from ND-02 is sufficient for future expansion

---

### ND-03-I002 Advanced Data Source Capability Evaluation

Include:

- source feasibility
- reliability
- maintenance cost
- data quality impact

Exclude:

- automatic source adoption

Evaluation focus:

- compare candidate sources against existing ND-01 source abstraction and provenance expectations
- confirm whether a new source improves coverage enough to justify the operational cost
- avoid any source-routing change until a source decision is explicitly approved

---

### ND-03-I003 Advanced Historical Analysis Evaluation

Include:

- historical depth
- cross-period comparison
- analytical capability

Evaluation focus:

- determine whether the current historical foundation can support deeper comparisons without changing the core V1 contract
- assess whether additional historical depth would materially improve report value
- identify any storage, query, or performance constraints before implementation is considered

---

### ND-03-I004 MCP / AI Consumer Interface Evaluation

Include:

- structured data access
- API/MCP capability review

Exclude:

- investment judgement
- trading automation

Evaluation focus:

- review whether the current AI-ready data contract can be extended into a more explicit consumer interface
- confirm that any structured access remains aligned with source metadata, `data_as_of`, warnings, and provenance
- keep the interface strictly informational and non-actionable

---

## 3. Priority Recommendation

Recommended order:

1. ND-03-I004 MCP / AI Consumer Interface Evaluation
2. ND-03-I003 Advanced Historical Analysis Evaluation
3. ND-03-I001 DT Rainbow Full Capability Evaluation
4. ND-03-I002 Advanced Data Source Capability Evaluation

Rationale:

- Platform value is highest for structured consumer access because it can reuse the ND-01 AI-ready contract and ND-02 presentation work.
- Historical analysis is the next best fit because ND-01 already established the storage and snapshot foundation, so the remaining work is mostly capability evaluation rather than new architecture.
- DT Rainbow remains valuable, but it is explicitly higher risk because the calculation side is still undefined and should not be reverse-engineered from the reference alone.
- Advanced data sources are important, but they carry the highest dependency and maintenance risk because source reliability, routing, and data-quality effects can expand scope quickly.

---

## 4. Dependencies

Include:

- ND-01 foundation
- ND-02 alignment work

Dependency notes:

- ND-01 provides the normalized historical storage, source abstraction, provenance metadata, and data-quality contract needed for later evaluation.
- ND-02 provides the report structure, user-flow alignment, and progressive disclosure patterns needed for future optional capability expansion.
- ND-03 should not introduce new requirements that bypass the ND-01/ND-02 contract surface.

---

## 5. Risks

Include:

- scope expansion
- unclear data sources
- over-engineering

Risk notes:

- Evaluation tasks can drift into implementation if the boundary is not kept explicit.
- Source-capability work can expand quickly if source ownership, fallback rules, or maintenance cost are not defined early.
- DT Rainbow and other historical/visualization ideas can become over-engineered if the plan tries to reproduce reference behavior without a validated contract.
- MCP / AI consumer work must remain read-only and informational so it does not become a hidden trading or recommendation system.

---

## 6. Acceptance Criteria

Before implementation:

- scope confirmed
- requirements separated from references
- no unapproved features added

Additional planning checks:

- each ND-03 item has a clearly bounded evaluation objective
- each item identifies what is explicitly excluded
- the implementation path remains compatible with the ND-01 and ND-02 contracts
- any later implementation proposal must be approved before code changes begin

---

## 7. Approval Status

Planning only.

Implementation pending approval.

