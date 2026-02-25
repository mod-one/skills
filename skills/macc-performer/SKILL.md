---
name: macc-performer
description: >
  Use this skill when an AI developer must implement exactly one development task from a PRD task list
  (for example prd.json) in this repository, especially when several agents work in parallel. It enforces
  domain-responsibility architecture, contracts-first implementation, strict and harmonized error handling,
  deterministic testing, observability, CI discipline, and conflict-safe delivery. Do not use for PRD generation
  or review-only tasks.
---

# Performer Skill - PRD Task Implementer (Parallel Safe)

Mission: implement one PRD task with minimal blast radius, stable contracts, and deployable quality.

## Input Contract

Before writing code, identify all task fields from the selected PRD entry:
- `id`
- `title`
- `objective`
- `description`
- `result`
- `steps`
- `dependencies`
- `exclusive_resources`
- `priority`

If the task is `priority: "0"` or declares exclusive resources, do not run it in parallel with conflicting tasks.

## Non-Negotiable Engineering Rules

1. Architecture by responsibility, not by technology.
- Split by domain/use-case (`billing`, `auth`, `catalog`, etc.), not repo-wide technical layers.
- Each module exposes a minimal public API and hides internals.
- Document module invariants explicitly.
- Domain core must not depend on infra; infra depends on domain.

2. Contracts before implementations.
- Define ports/interfaces/types first.
- Keep interfaces small, stable, and testable.
- Forbid mega-interfaces.

3. No God files.
- Split files by responsibility before they become large.

4. Coupling and cohesion.
- One module = one clear idea.
- Avoid generic cross-cutting `utils` dumping grounds.
- Prefer local duplication over unclear global abstraction.

5. DRY with judgment.
- DRY applies to business knowledge and invariants first.
- Factor only after repeated patterns and only if abstraction reduces complexity.

6. Illegal states must be unrepresentable.
- Use typed IDs/value objects/enums/validated constructors.
- Avoid magic strings and ad-hoc nullable flows.

7. Strict and harmonized error model.
- No silent catch-all.
- Every error is categorized, contextualized, preserved, and observable.
- Required categories: `Validation`, `Auth`, `Dependency`, `Conflict`, `NotFound`, `Internal`.
- Required fields: `code`, `category`, `message`, `context`, `cause`.
- Error codes must follow the `MACC-DOMAIN-0000` nomenclature defined in the project's `docs/ERRORS.md`.
- **Mandatory**: If the project lacks a catalog, refer to this skill's internal `docs/ERRORS.md` to initialize the project's catalog or follow its standard. Update the catalog whenever introducing new codes.

8. Performance policy.
- Clarity first, then measure, then optimize locally.
- Optimize only with evidence (profiling or measured bottleneck).

9. Test policy.
- Unit tests on domain invariants and edge cases first.
- Targeted integration tests second.
- Few critical E2E tests only.
- Every bugfix adds a regression test.
- Tests must be deterministic (mock time/network/randomness).

10. Readability and consistency.
- Enforce formatter and linter in CI.
- Prefer domain naming over technical naming.
- Keep functions focused and names explicit.
- Large files/classes indicate architecture drift.

11. Internal API stability.
- Any public internal API gets short contract docs and example usage.
- Breaking changes require migration path and progressive deprecation when possible.
- Keep API docs updated with each behavior or signature change.

12. Observability from start.
- Structured logs with correlation fields when available (`request_id`, `user_id`, `trace_id`).
- Track latency and error metrics for critical flows.
- Add tracing for distributed paths when relevant.

13. CI/CD reliability.
- PR must pass build, lint/format, tests, and baseline dependency security checks.
- Default branch must remain deployable.

14. Debt management.
- Use `TODO(owner, YYYY-MM-DD, reason): ...` only.
- Track debt items explicitly and prefer small frequent refactors.

15. Living minimal documentation.
- Keep lightweight architecture notes, run/test instructions, conventions, and short ADRs close to code.
- Update docs in the same PR when contracts/behavior change.

16. Golden rule for each PR.
- Validate the change reduces global complexity.
- Validate coupling is controlled.
- Validate invariants are clearer.
- Validate testing is easier.

17. No transversal repo-wide changes without explicit approval.
- Global renaming/style migrations/library swaps require a lightweight RFC and approval first.

18. Code standards are mandatory.
- No magic strings for business rules.
- No duplicated config constants without reason.
- New modules must include minimal tests, structured errors, and short contract docs.
- Any new abstraction must be justified by reduced complexity.

19. Git hygiene.
- Add non-committable artifacts to `.gitignore` (generated files, caches, local env files, temp outputs).

## Execution Workflow (Strict Order)

### Step 0 - Task framing from PRD
- Restate objective in one sentence.
- Define in-scope and out-of-scope from task `description`.
- List touched domains/modules.
- Identify conflict-prone files and resources.
- Check task `dependencies` and `exclusive_resources` before coding.

Output template:
- Objective:
- In scope:
- Out of scope:
- Dependencies:
- Exclusive resources:
- Touched modules:
- Hot/conflict areas:

### Step 1 - Parallel-safe plan
- Keep the change local to one domain.
- If hot files are unavoidable, split into small contracts-first increments.
- Use a feature flag when partial delivery is needed.

### Step 2 - Define contracts
- Define/update interfaces, DTOs, domain types, invariants, and error contract.
- Write minimal contract-focused tests when relevant.

### Step 3 - Implement
- Keep domain independent from infra.
- Implement infra adapters behind contracts.
- Avoid broad utility abstractions.

### Step 4 - Error integration
- Ensure each failure path maps to the standard error model.
- Ensure code/category/message/context/cause are preserved.
- **Reference**: Consult the project's `docs/ERRORS.md`. If missing, use the skill's embedded `docs/ERRORS.md` as the master standard for categories and nomenclature.
- Update the project's error catalog/docs and add tests for new mappings.

### Step 5 - Testing
- Add domain unit tests first.
- Add targeted integration tests for DB/HTTP boundaries when needed.
- Add regression tests for fixes.
- Ensure determinism.

### Step 6 - Observability
- Add structured logs and key metrics for important flows.
- Add tracing hooks for distributed or hard-to-debug paths.

### Step 7 - Hygiene and CI
- Run formatter, linter, and tests.
- Check `.gitignore` updates.
- Ensure changed docs/contracts are synchronized.

### Step 8 - Pre-PR gate
- Scope is minimal and aligned with one PRD task.
- No God file introduced.
- Contracts precede implementation.
- Error model is harmonized and documented.
- Tests are deterministic and sufficient.
- CI-equivalent local checks pass.
- Docs and ADR notes are updated if needed.

## Branch, Commit, PR

Branching:
- One PRD task = one branch.
- Never commit directly to `main`.
- Keep branch short-lived.

Commit style:
- Use Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`).
- One commit should keep one clear intent.

PR checklist block:
- PRD task ID:
- What/Why:
- Included scope:
- Excluded scope:
- How to test:
- Risks:
- Observability:
- Error codes added/changed:
- Docs/ADR updated:
