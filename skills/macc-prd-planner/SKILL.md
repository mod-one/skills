---
name: macc-prd-planner
description: >
  Generate or safely update a MACC `prd.json` execution plan, including dependency-safe task
  decomposition, repository inspection, schema-aware validation, and strict UX/UI fidelity contracts.
  Use for MACC lots involving backend, infrastructure, frontend logic, approved UI implementation,
  design-system work, or UX review. Do not use to implement code or review a code diff.
---

# MACC PRD Planner

Produce executable, update-safe `prd.json` files. Each PRD file represents exactly one product feature or one shared foundation used by multiple features. Decide semantic task boundaries and contracts; use the bundled deterministic CLI to establish repository facts and validate objective rules.

Do not select provider-specific models. `routing_hints` remain abstract and runtime-resolved.

## Required workflow

1. Frame the PRD scope: choose exactly one `prd_scope.kind` (`feature` or `shared-foundation`), one stable scope ID, name, definition, assumptions, constraints, existing PRD status, shared hot zones, and likely cross-cutting seams.
2. Inspect the repository before planning:

   ```bash
   python3 <skill-root>/scripts/macc_prd.py inspect --root .
   python3 <skill-root>/scripts/macc_prd.py build-context --root .
   ```

   Read `prd.json.example` as the schema source of truth. Also inspect `prd.json`, `worktree.prd.json`, `.macc/tool.json`, `.macc/worktree.json`, and MACC operational paths when present.
3. Classify every task on both axes: `routing_hints.execution_mode` and `planning_profile`.
4. For UI-sensitive work, inspect every required design source before task decomposition:

   ```bash
   python3 <skill-root>/scripts/macc_prd.py inspect-design --root . --path <design-system-dir>
   python3 <skill-root>/scripts/macc_prd.py inspect-html --root . --path <reference.html>
   ```

   Create a `reference_coverage` map from each screen/component area to its authoritative sources. The generated context inventories facts; the planner supplies this semantic mapping.

5. Define coherent task boundaries, dependencies, `exclusive_resources`, and change boundaries. Every task must serve the file-level `prd_scope`; move unrelated feature work to a separate PRD.
6. Generate or update `prd.json`, preserving existing task IDs when their responsibility has not changed.
7. Validate, repair only the reported defect, and validate again. Make at most two automatic repair passes:

   ```bash
   python3 <skill-root>/scripts/macc_prd.py validate --root . --file prd.json
   python3 <skill-root>/scripts/macc_prd.py validate --root . --file prd.json --profile ui-fidelity
   ```

8. Deliver only a valid PRD, or report blocking diagnostics. Never delete requirements merely to satisfy validation.

The CLI emits JSON diagnostics. Use `explain` for a code:

```bash
python3 <skill-root>/scripts/macc_prd.py explain --diagnostic MACC-PRD-6003
```

The script is a portable, deterministic compatibility implementation. Replace it with the MACC Rust core when available; preserve command names, JSON output shape, and diagnostic codes.

## Universal planning policy

- Treat one PRD file as one planning unit: either one user-visible/business capability (`feature`) or one reusable enabling layer (`shared-foundation`). Do not mix multiple feature deliveries in the same PRD.
- Use `prd_scope.id` as the file-level identity. Add `scope_ref` to tasks when the repository schema permits custom task fields; it must match `prd_scope.id`.
- Use `shared-foundation` only for common infrastructure, contracts, design-system primitives, auth/session substrate, build/test scaffolding, data migrations, or other reusable base work that intentionally supports several future features without delivering any one of them.
- Put downstream feature names in `prd_scope.consumer_feature_ids` only for traceability. Do not implement those downstream features in the shared-foundation PRD.
- Resolve edge cases with [prd-scope-policy.md](references/prd-scope-policy.md).
- Plan for one focused performer run per task, with clear goal, actions, out-of-scope work, result, and observable success criteria.
- Keep tasks small, but do not split a UI task below its smallest coherent visual and behavioral unit.
- Treat dependencies and `exclusive_resources` as first-class scheduling constraints. They prevent collisions; they do **not** grant or restrict write access.
- Reuse the repository's existing error model. Do not invent a global taxonomy.
- Include dedicated documentation and verification tasks unless a specific lot assumption justifies omission.
- Preserve task identity in updates. Do not repurpose completed or existing IDs for unrelated responsibilities.
- Avoid adding unrelated behavior to hot files. Plan extraction before further growth where a hotspot mixes responsibilities or creates collision risk.
- Keep `worktree.prd.json`, coordinator scheduling, `sync-prd`, and `audit-prd` compatibility intact.

## Two-axis classification

`execution_mode` measures technical breadth and risk:

- `micro`: local, low-risk work with focused validation.
- `standard`: a module-level behavior change or new internal seam with targeted tests.
- `structural`: shared contracts, orchestration, cross-module architecture, migrations, or major hotspots; include compatibility thinking and heavy validation.

`planning_profile` selects the domain contract. Use the lightest applicable profile:

- `general` (default): backend, infrastructure, data, documentation, tests, CLI, and ordinary refactors.
- `frontend-logic`: non-visual client code such as API clients, stores, route guards, caching, and build configuration.
- `ui-fidelity`: faithfully implement an approved screen, component, layout, flow, or behavior from imposed sources.
- `ui-exploration`: explore a new visual direction only when creative exploration is explicitly authorized.
- `design-system-change`: extend, migrate, replace, or reorganize a design system as the task result.
- `ux-review`: assess fidelity, usability, accessibility, consistency, or interaction semantics without primary implementation work.

Do not infer `ui-exploration` from the presence of frontend code. Use `ui-fidelity` when strict compliance, an imposed design system, HTML reference, visual prototype, screenshot, graphic charter, approved UI, or explicit no-deviation instruction exists.

## UI contracts

For `ui-fidelity`, `ui-exploration`, `design-system-change`, and relevant `ux-review` tasks, use the optional fields in [ui-fidelity-contract.schema.json](schemas/ui-fidelity-contract.schema.json) when the repository schema permits custom fields. Start from the applicable template in [templates](templates/).

When custom fields are forbidden, encode the same contract in `description`, `acceptance_criteria`, `labels`, and `notes` using [acceptance-criteria-guide.md](references/acceptance-criteria-guide.md). Do not silently drop a contract because the schema is older.

### Sources, authority, and conflicts

Put typed sources in `design_contract.sources`. Set every source to one of:

- `required`: the performer must comply.
- `supporting`: resolves details absent from required sources.
- `inspiration`: permits creative reinterpretation.

Do not downgrade an imposed specification or design system to `inspiration`.

Default precedence is: explicit task constraints; task-specific screen/component specification; imposed design system; project patterns; project-wide standards; generic agent preferences. Generic preferences never override project sources.

If required sources materially conflict, create a contract-resolution task and block dependent work, or stop and report that the PRD cannot safely be finalized.

### Fidelity modes and design-system roles

Every `ui-fidelity` and `ui-exploration` task needs `fidelity_mode`:

- `exact`: default for approved references; no voluntary redesign, content simplification, invented tokens, rewritten copy, replacement components, decoration, or generic modernization.
- `adaptive`: only explicitly stated responsive, accessibility, i18n, platform, or equivalent-component adaptations.
- `exploratory`: substantial visual interpretation; use only when expressly authorized.

Missing information is not permission to redesign. Reuse the nearest compatible existing pattern for minor gaps; make material ambiguity a clarification or contract-resolution dependency.

Every task that references a design system needs `design_system_role`: `consumer`, `extension`, `migration`, or `none`.

`consumer` is the default for an imposed system. It must not change system sources, tokens, color/font/spacing/radius/shadow scales, icon family, component library, or shared primitives unless specifically authorized. `extension` tasks include rationale, API, docs, tests/stories, migration impact, and dependencies. `migration` tasks include compatibility, rollout, regression, deprecation, docs, and cross-screen impact.

### Scope, evidence, and review

Use `change_scope.allowed_paths` for intended writes, `read_only_paths` for inspect-only sources, and `forbidden_paths` for prohibited areas. Set all required immutable sources to read-only or forbidden. A reviewer or merge gate must compare the final diff to these boundaries.

For each relevant task, select only applicable `ui_states` and concrete `viewports`. Require proportional evidence: screenshots, interaction tests, accessibility checks, design-token audit, protected-path check, component story, visual regression, or manual fidelity review.

Acceptance criteria must be observable and source-specific. Reject vague criteria such as “looks polished,” “modern,” “intuitive,” or “matches the design” without a named source and dimension.

For a UX review task, require a structured decision (`approved` or `changes_requested`) and violations with criterion, severity (`blocking`, `major`, `minor`, `advisory`), location, expected/observed behavior, and evidence path. Only configured blocking/major findings gate a merge.

## Execution and integration boundaries

The resulting contract is enforced after planning:

- Performers read every required source before editing, remain in `allowed_paths`, do not modify `read_only_paths` or `forbidden_paths`, honor the fidelity mode and design-system role, produce required evidence, and escalate material ambiguity. Record evidence, adaptation decisions, protected-path violations, and unresolved ambiguities using [phase-result.schema.json](schemas/phase-result.schema.json).
- Reviewers verify sources, fidelity, design-system use, protected paths, states, viewports, evidence, accessibility, and acceptance criteria. Record the decision and violations using [ux-review-result.schema.json](schemas/ux-review-result.schema.json) and [the result template](templates/ux-review-result.json).
- Coordinators or merge gates block configured mandatory-evidence failures, unauthorized protected-path changes, unresolved blocking UX violations, missing required sources, material redesign of an `exact` task, and unauthorized consumer token/library changes.

MACC Web/TUI editors should expose profile-aware forms, discovered sources, source authority, contracts, diagnostics, evidence, and review findings. A future MCP server may expose the same repository context, inspectors, schema, validators, and diagnostics, but it must delegate to the shared MACC PRD core rather than duplicate policy. MCP is optional and must not replace this semantic planning workflow.

## Task authoring

At the file level, prefer this scope contract:

```json
{
  "prd_scope": {
    "kind": "feature",
    "id": "feature-slug",
    "name": "Feature name",
    "definition": "The single capability this PRD delivers.",
    "out_of_scope": ["Other features and unrelated foundation work"]
  }
}
```

For shared base work, set `"kind": "shared-foundation"` and describe the reusable substrate, not the downstream features that may consume it. Use [prd-scope.schema.json](schemas/prd-scope.schema.json), [feature-prd.json](templates/feature-prd.json), or [shared-foundation-prd.json](templates/shared-foundation-prd.json) as needed.

Each task uses repository-required fields and, where supported, these recommended fields:

```json
{
  "scope_ref": "feature-or-foundation-id",
  "planning_profile": "general",
  "routing_hints": {
    "execution_mode": "standard",
    "reasoning_depth": "standard",
    "context_scope": "module",
    "risk_level": "medium",
    "validation_profile": "standard"
  }
}
```

Write descriptions with: Problem/Goal, Key actions, Out of scope, and Success criteria. Use action-oriented titles; keep steps short and sequenced; describe tangible results.

If the repository schema forbids `prd_scope` or `scope_ref`, encode the same identity in `lot.kind`, `lot.id`, `lot.name`, `lot.definition`, and each task description. Do not omit the single-feature/shared-foundation contract.

For UI tasks, add explicit authoritative sources, precedence, fidelity mode, design-system role, scope boundaries, allowed adaptations, escalation conditions, states, viewports, evidence, and precise acceptance criteria.

Use contracts-first tasks only when they reduce a real collision or ambiguity. Do not dispatch parallel UI implementation tasks while their shared design contract or primitives are unstable. Do not split markup, styling, responsiveness, states, and local accessibility across unrelated tasks for the same component or screen.

## Completion checks

Before delivery, confirm:

- JSON and repository schema compatibility; unique stable IDs; valid dependencies; no cycles; valid priority and routing hints.
- The PRD has exactly one valid file-level scope: `feature` or `shared-foundation`; all task `scope_ref`, `feature_id`, `scope_refs`, or `feature_ids` values match that scope.
- Explicit, minimal dependencies and real collision protection; hot zones are planned around.
- At least one documentation task and one verification task, or an explicit lot assumption for each omission.
- For UI-sensitive tasks: sources are inspected and exist; authority/precedence, fidelity mode, design-system role, scope boundaries, states/viewports, adaptations, observable criteria, and evidence are complete.
- `consumer` tasks do not authorize design-system writes; required sources are immutable; required-source conflicts are resolved.
- Exact tasks preserve the authoritative reference rather than reinterpreting it.

## Escalate instead of improvising

Stop and report when the requested PRD mixes multiple features; a shared-foundation PRD starts delivering a downstream feature; the repository schema conflicts with the requested PRD; IDs would be misleadingly repurposed; a material architecture decision is hidden in an ordinary task; a required source is unavailable or conflicts with another required source; exact work lacks material interaction/responsive behavior; a consumer task requires a system change; no authoritative source or reusable pattern exists for strict fidelity; the schema cannot represent or compatibly encode a required contract; or blocking validation diagnostics remain after two repair passes.
