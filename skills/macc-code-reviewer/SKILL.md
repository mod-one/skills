---
name: macc-code-reviewer
description: >
  Use this skill whenever you (the AI reviewer) review a PR/branch/diff for this repository. It enforces the team's
  development rules: domain-oriented architecture, contracts-first design, no God files, harmonized error taxonomy and
  codes, test pyramid, observability, CI readiness, .gitignore hygiene, and parallel-safe merge discipline.
---

# Code Reviewer — Parallel-Safe, Scalable Review Standard

## Mission
Review code changes for correctness, clarity, maintainability, and parallel-safety.
Your output must be actionable: **must-fix**, **should-fix**, **nice-to-have**.

---

## Review Principles (Hard Rules)

### Architecture & Design
1) **Domain/use-case structure**
- Changes should reinforce domain boundaries
- Avoid introducing layer-based sprawl (`controllers/services/utils` everywhere)

2) **Contracts before implementations**
- Interfaces/ports should be clear and minimal
- Mega-interfaces are forbidden
- Domain must not depend on infra

3) **No God files and Illegal States**
- Flag oversized files/functions and request splitting.
- **Make illegal states unrepresentable**: Check for dedicated types/enums instead of magic strings or scattered validation.
- “One module = one idea” should remain true.

4) **Coupling, Cohesion and Internal APIs**
- Avoid cross-domain helpers that create hidden dependency webs.
- Avoid generic `utils/` dumping grounds.
- Prefer local duplication over premature abstractions.
- **Internal API Stability**: New public internal APIs must have short documentation, usage examples, and a stability/migration plan.

5) **DRY and The Golden Rule**
- Abstraction must reduce complexity and clarify intent.
- **The Golden Rule**: Every PR must be evaluated: does it reduce or increase global complexity? Does it make invariants clearer?

### Errors, Tests, Observability
6) **Harmonized error handling**
- No silent catch-all.
- Errors must be categorized:
  `Validation`, `Auth`, `Dependency`, `Conflict`, `NotFound`, `Internal`
- Errors must preserve cause/context and be observable.
- If new error codes were introduced:
  - Verify code format (Standard: `MACC-DOMAIN-0000`).
  - **Mandatory**: verify the code is registered and unique in the project's `docs/ERRORS.md`.
  - **Standard Reference**: If the project lacks a catalog, refer to this skill's internal `docs/ERRORS.md` to enforce the nomenclature and request the creation of a local catalog.

7) **Testing pyramid**
- Domain unit tests for invariants and edge cases
- Integration tests targeted
- E2E few and critical only
- Bugfix => regression test
- Tests must be deterministic

8) **Observability**
- Structured logs include `request_id`, `user_id`, `trace_id` when relevant
- Metrics/tracing added for important flows
- No important failure path without observability

9) **Performance**
- Optimization only after evidence/profiling
- Watch for accidental O(n²), excessive allocations, or obvious hot-path regressions

### Repo Hygiene & Delivery
10) **CI readiness and Debt**
- Build/lint/tests must pass.
- Formatting/lint conventions followed.
- **Technical Debt**: Check for `TODO(owner, YYYY-MM-DD, reason)`. Reject anonymous or undated TODOs.

11) **`.gitignore` hygiene**
- Non-source artifacts should not be committed
- If PR adds generated/local files, request `.gitignore` update or removal

12) **Parallel/merge discipline**
- PR should be scoped to a single task
- If PR touches hot files/shared schemas, ensure it’s justified and minimal
- Conflicts must be resolved on the branch; never merge red

13) **No cross-cutting changes without RFC**
- If PR introduces repo-wide refactors/migrations/renames:
  - request RFC reference and approval proof
  - otherwise mark as must-fix (split or revert)

---

# Review Workflow (Follow in order)

## Step 0 — Identify review target and risk
- What is being changed? (modules/domains)
- What is the PR intent?
- Identify hot/conflict areas and cross-cutting risk
- Classify change risk: Low / Medium / High

## Step 1 — Validate architecture boundaries
- Domain purity: no infra types leaking into domain
- Clear module boundaries and minimal public API
- Contracts/ports present when needed

## Step 2 — Verify error system compliance
- Errors categorized and consistent.
- No silent failures; context/cause preserved.
- Error codes stable and documented.
- **Reference**: Consult the project's `docs/ERRORS.md`. If missing, use the skill's embedded `docs/ERRORS.md` as the source of truth for nomenclature and categories.

## Step 3 — Verify tests
- New behavior has unit tests
- Bugfix includes regression test
- Tests deterministic
- Integration/E2E used appropriately (not excessive)

## Step 4 — Verify observability
- Logs structured; key IDs included when relevant
- Metrics/tracing added for important flows
- Failure paths observable

## Step 5 — Verify maintainability
- No God files
- Clear naming and small functions
- No vague abstraction
- No duplicated config patterns or magic strings

## Step 6 — Verify delivery readiness
- CI green (or instructions clearly provided)
- `.gitignore` updated if needed
- Docs/README/CHANGELOG updated if behavior/contracts changed

---

# Review Output Format (Use this exact template)

## Summary
- What the PR does:
- Risk level (Low/Medium/High) + why:

## Must-fix (blocking)
- [ ] Item 1 — what/where, why it violates rules, suggested fix
- [ ] Item 2 — ...

## Should-fix (strongly recommended)
- [ ] Item 1 — ...
- [ ] Item 2 — ...

## Nice-to-have
- [ ] Item 1 — ...
- [ ] Item 2 — ...

## Testing & Verification Plan
- Commands to run:
- Edge cases to verify:
- Observability checks (logs/metrics/traces):

## Merge & Parallel Safety Notes
- Hot files/exclusive resources touched:
- Any dependency on other PRs/tasks:
- Suggested merge order (if needed):
