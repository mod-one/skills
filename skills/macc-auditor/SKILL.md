---
name: macc-auditor
description: >
  Perform an independent final MACC compliance audit to determine whether the delivered feature, shared
  foundation, or final integrated implementation truly matches the original requirements/specifications,
  original PRD, tests/results, UI/design sources, design-system constraints, architecture decisions, and
  integration expectations. Produces the canonical `.macc/reports/implementation-audit.md` report.
  Use after implementation/review phases, before final acceptance, merge, or release. Do not use to
  implement fixes or generate a PRD.
---

# MACC Auditor

Audit final compliance. Answer one question with evidence: did the delivered result actually satisfy what was requested?

Fundamental rule: Do not implement fixes. Audit, collect evidence, classify findings, and produce the canonical report only.

The auditor must remain independent. Do not edit implementation files, tests, design assets, PRD content, architecture docs, or generated artifacts to make the audit pass. If the audit discovers a defect, report it; do not repair it in the same auditor pass.

## Audit input model

Examine these inputs together:

```text
Original requirements/specifications
                 +
Original PRD
                 +
Final integrated implementation
                 +
Tests/results
                 +
Relevant architecture/design constraints
                 ↓
        Compliance analysis
                 ↓
     .macc/reports/implementation-audit.md
```

The final integrated implementation is the post-task, integrated repository/product state, not only one isolated task diff. Verify local correctness and global coherence.

## Required workflow

1. Identify the audit target and required inputs:
   - original requirements/specifications: user request, issue, ticket, brief, design request, or product spec;
   - original PRD: `prd.json`, `worktree.prd.json`, PRD examples, task list, acceptance criteria, scope contract;
   - final integrated implementation: final branch/diff, merged worktree state, build artifact, screenshots, logs, final task outputs;
   - tests/results: automated test output, manual verification, screenshots, review artifacts, CI results;
   - architecture/design constraints: ADRs, design sources, design system, tokens, component contracts, integration boundaries.
2. Inspect local context before judging:

   ```bash
   python3 <skill-root>/scripts/macc_auditor.py inspect --root . --prd prd.json
   ```

   Also inspect `worktree.prd.json`, `.macc/tool.json`, `.macc/worktree.json`, `.macc/log/`, task result files, review result files, design references, screenshots, and relevant test output when present.
3. Build an evidence inventory from all five input groups. Mark absent input groups explicitly in `.macc/reports/implementation-audit.md`.
4. Build a traceability matrix: every requirement, acceptance criterion, user case, design constraint, architecture decision, integration expectation, and non-goal maps to implementation evidence and verification evidence.
5. Audit by dimension:
   - specification coverage;
   - PRD scope and acceptance-criteria coverage;
   - behavior completeness;
   - missing user cases and edge cases;
   - UI/design fidelity;
   - design-system compliance;
   - architecture decision drift;
   - global integration coherence;
   - regression risk beyond targeted tests;
   - debt, workaround, or scope creep introduced during tasks.
6. Classify findings with [audit-rubric.md](references/audit-rubric.md).
7. Produce the canonical Markdown report `.macc/reports/implementation-audit.md`. Start from [implementation-audit.md](templates/implementation-audit.md) or generate a skeleton:

   ```bash
   python3 <skill-root>/scripts/macc_auditor.py markdown --root . --prd prd.json
   ```

8. Optionally produce a machine-readable JSON sidecar. Use [audit-report.schema.json](schemas/audit-report.schema.json) and [audit-report.json](templates/audit-report.json) when the caller wants automation.
9. Validate the JSON sidecar when emitting JSON:

   ```bash
   python3 <skill-root>/scripts/macc_auditor.py validate --file audit-report.json
   ```

10. Return a concise decision and the evidence-backed findings. Do not approve if blocking or major compliance gaps remain.

The CLI emits deterministic JSON diagnostics. Use `explain` for a code:

```bash
python3 <skill-root>/scripts/macc_auditor.py explain --diagnostic MACC-AUDIT-3002
```

## Evidence hierarchy

Prefer primary evidence over inference:

1. Original requirements/specifications, original PRD, acceptance criteria, explicit design source, ADR, or architecture decision.
2. Final diff, implementation files, tests, screenshots, logs, built app behavior, task/review reports.
3. Repository conventions and existing patterns.
4. Reasoned inference, explicitly labeled as inference.

If a requirement cannot be verified because evidence is missing, mark it `unverified`, not `passed`.

See [evidence-guide.md](references/evidence-guide.md) for evidence collection and traceability rules.

## Audit decisions

Use exactly one decision:

- `approved`: no blocking or major compliance gap remains; minor/advisory items may exist.
- `changes_requested`: at least one blocking or major finding exists.
- `blocked`: required evidence is missing, unavailable, contradictory, or impossible to inspect.

Do not use “approved with blocking issues”. Do not hide uncertainty.

## Finding severity

- `blocking`: the result does not satisfy a required spec/acceptance criterion, breaks a critical user path, violates an imposed design source or design system, contradicts an architecture decision, or introduces high release risk.
- `major`: a required behavior is partial, a user case is missing, integration is inconsistent, coverage is materially weak, or debt/workaround creates near-term risk.
- `minor`: local defect or polish issue that does not invalidate the main result.
- `advisory`: non-blocking recommendation, follow-up, or risk observation.

Every finding must include:

- requirement or criterion violated;
- location;
- expected result;
- observed result;
- evidence;
- impact;
- smallest suggested fix or follow-up.

## Compliance dimensions

### Specification and acceptance criteria

Check that every explicit requirement and acceptance criterion is represented in the final result. Split compound requirements into auditable rows. Reject “implemented” claims without code, behavior, test, screenshot, or log evidence.

### Functional behavior and user cases

Check the happy path, required alternate paths, empty/error/loading states, permissions, invalid inputs, retries, cancellation, concurrency, persistence, and cross-session behavior when relevant. Do not require cases outside the requested scope; do flag omitted cases that the spec implied.

### UI, design, and design system

When the work has UI impact, compare final behavior and screenshots against required sources. Check information architecture, layout, typography, spacing, copy, tokens, components, states, responsiveness, accessibility, interaction semantics, and protected paths. Use [ui-design-audit.md](references/ui-design-audit.md) when visual fidelity or design-system compliance matters.

### Architecture and integration

Check whether implementation still follows the accepted architectural decision, boundaries, contracts, data flow, error model, observability, and MACC worktree expectations. Flag drift when the final result solves the local task but violates the global design.

### Tests, regressions, and debt

Verify that tests cover changed behavior and required acceptance criteria, but do not assume targeted tests catch integration regressions. Inspect for untested paths, brittle mocks, skipped tests, TODOs, temporary flags, hardcoded shortcuts, broad refactors, and workaround comments.

## Output format

Always produce or update `.macc/reports/implementation-audit.md` as the canonical report. Use a concise human summary plus structured findings. The report must state that the auditor did not implement fixes.

For optional JSON sidecars, use:

```json
{
  "decision": "changes_requested",
  "scope": {"kind": "feature", "id": "feature-slug", "name": "Feature name"},
  "summary": "One-sentence audit result.",
  "traceability": [],
  "findings": [],
  "evidence_reviewed": [],
  "unverified_items": [],
  "recommended_next_steps": []
}
```

See [output-guide.md](references/output-guide.md) for the exact report shape.

## Escalate instead of guessing

Stop and report `blocked` when the original request/spec is unavailable, the delivered state cannot be inspected, required design sources are missing, build/test evidence is absent for a high-risk change, screenshots cannot be produced for required UI fidelity, or contradictory sources make compliance impossible to decide.
