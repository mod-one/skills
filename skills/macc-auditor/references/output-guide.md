# Audit output guide

Canonical artifact: `.macc/reports/implementation-audit.md`.

Always produce or update this Markdown report when the user requests a final implementation audit. JSON is optional and only a machine-readable sidecar.

Required report sections:

1. Decision: `approved`, `changes_requested`, or `blocked`.
2. Scope.
3. Auditor independence statement: no fixes implemented by auditor.
4. Inputs reviewed:
   - Original requirements/specifications.
   - Original PRD.
   - Final integrated implementation.
   - Tests/results.
   - Relevant architecture/design constraints.
5. Summary.
6. Traceability matrix.
7. Findings grouped by severity.
8. Unverified items.
9. Regression and integration risk.
10. Recommended next steps.

Human response after writing the report:

1. Decision: `approved`, `changes_requested`, or `blocked`.
2. Path to `.macc/reports/implementation-audit.md`.
3. One-sentence summary.
4. Findings grouped by severity.
5. Traceability gaps or unverified items.
6. Smallest next steps.

Finding format:

```text
[severity] Requirement or criterion
Where: path/module/flow
Expected: required result
Observed: final behavior
Evidence: concrete artifact or missing evidence
Impact: why this matters
Suggested fix: smallest correction
```

Do not implement the suggested fix during the auditor pass. Suggested fixes are instructions for a later performer/fix task.

JSON report fields:

- `decision`: final audit decision.
- `scope`: audited feature/foundation/release.
- `summary`: concise result.
- `traceability`: requirement rows.
- `findings`: compliance findings.
- `evidence_reviewed`: artifacts inspected.
- `unverified_items`: items that could not be proven.
- `recommended_next_steps`: minimal next actions.

Do not mix speculative improvements into blocking findings. Keep non-required improvements as advisory.
