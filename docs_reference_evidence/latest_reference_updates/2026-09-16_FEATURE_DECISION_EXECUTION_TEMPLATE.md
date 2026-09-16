# Feature Decision Execution Template

Use one completed block per approved feature batch after Joe decides. Do not execute a batch without explicit decisions.

```
JOE_APPROVED_FEATURE_IDS=
JOE_DECISION_PER_FEATURE=KEEP | HIDE_ONLY | DISABLE_RUNTIME | REMOVE
REFERENCE_CHECK=
CURRENT_BEHAVIOR=
EXPECTED_CHANGE=
P0_IMPACT_CHECK=
MINIMAL_FILES=
TEST_PLAN=
RUNTIME_VERIFY=
ROLLBACK_PLAN=
```

Required checks before implementation:

1. Preserve the P0 trusted chain unless the approved change explicitly targets it.
2. Separate frontend hiding from backend runtime disable and removal.
3. Record API, MCP, export, scheduler, persistence, and shared-core effects.
4. Run the smallest relevant tests, then production verification if runtime behavior changes.
5. Record rollback steps and leave unselected features unchanged.

Current state: all feature decisions are `UNDECIDED`; no feature visibility, runtime, or implementation change is authorized by this preparation package.
