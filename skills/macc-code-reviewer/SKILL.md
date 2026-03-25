---
name: macc-reviewer
description: >
  Use this skill when an AI reviewer audits one MACC task implementation inside one worktree.
  It enforces MACC-native review: task-scoped analysis, worktree/context awareness,
  anti-god-file discipline, existing error-model alignment, deterministic tests,
  proportional documentation, observability, and parallel-safe delivery.
  Do not use for planning-only work or for implementing code.
---

# MACC Reviewer Skill - Task-Scoped Change Review

## Mission

Review exactly one task implementation in one worktree.
Your job is to determine whether the delivered change set is:
- correct,
- scoped to the selected task,
- maintainable,
- compatible with MACC orchestration,
- safe for parallel execution and later integration.

Your output must be actionable and evidence-based:
- `must-fix` = blocking issue or contract violation;
- `should-fix` = strong recommendation with meaningful risk;
- `nice-to-have` = non-blocking improvement.

## Use This Skill When

- a MACC review phase is running for one selected task;
- you must review a concrete change set, not invent new scope;
- the repository uses MACC worktree/task conventions.

## Do Not Use This Skill For

- implementing code;
- generating or restructuring `prd.json`;
- architecture planning without a concrete reviewed change set;
- repo-wide audits with no selected task.

## MACC Review Context

Treat these constraints as mandatory:

- One review run = one selected task = one worktree context.
- Review against the selected task first, not against personal preferences.
- Preserve compatibility with:
  - `worktree.prd.json`
  - `.macc/tool.json`
  - `.macc/worktree.json` when present
  - `.macc/log/`
  - coordinator phase transitions
  - `sync-prd` and reconciliation expectations
- Focus on the current task change set. Do not require unrelated cleanup.
- If a finding depends on another task, shared hot file, or exclusive resource, state it explicitly.

## Review Proportionality

Judge the implementation with the lightest review mode that fits the task.

### Micro review
Use when the change is local, low-risk, and does not alter shared contracts.

Expect:
- local correctness;
- targeted tests;
- no architecture ceremony;
- minimal documentation changes only if behavior changed.

### Standard review
Use when the change crosses a small module boundary or adds/refines an internal contract.

Expect:
- clear contract boundaries;
- targeted tests;
- proportional observability;
- nearby documentation or contract notes when behavior changed.

### Structural review
Use only when the task changes shared contracts, orchestration behavior, or cross-module architecture.

Expect:
- migration thinking;
- stronger compatibility checks;
- short architecture note or ADR when the repository already uses that practice.

Do not demand structural-process artifacts for a micro task.

## Non-Negotiable Review Rules

### 1. Review the selected task, not imagined scope
- The reviewed change must stay aligned with one task objective.
- Do not ask for opportunistic expansion outside the selected task.
- If adjacent issues are real, place them in `should-fix` or `nice-to-have` unless they block this task directly.

### 2. Stay MACC-native
- Review the change in its worktree/task context.
- Check that local MACC files and orchestration expectations were not broken accidentally.
- Do not require a workflow that conflicts with MACC coordinator behavior.

### 3. Architecture by responsibility
- Prefer domain or use-case boundaries over vague technical dumping grounds.
- One module should have one clear reason to change.
- Flag hidden dependency webs and mixed-responsibility modules.
- Prefer clear nearby code over clever cross-cutting abstractions.

### 4. Contracts before expanded behavior
- Interfaces, DTOs, domain types, invariants, and boundaries should remain explicit.
- Mega-interfaces and broad helper surfaces are review concerns.
- Domain logic should not silently depend on infrastructure details when separation matters.

### 5. Anti-god-file policy
A file is at risk when one or more of these signals appear:
- it mixes unrelated responsibilities;
- it changes for unrelated tasks;
- it is difficult to test in isolation;
- it is a recurring conflict hotspot;
- it keeps growing faster than neighboring files in the same module.

Soft thresholds:
- over 300 lines: re-evaluate responsibility boundaries;
- over 500 lines: adding new logic requires an explicit split or extraction evaluation;
- over 800 lines: adding new logic is normally unacceptable unless the file is a justified exception.

Justified exceptions:
- generated code;
- declarative schemas or configuration;
- thin composition roots;
- index or re-export files.

When reviewing a dense file, check whether the implementer chose an acceptable path:
1. split first;
2. extract the new logic into a nearby module;
3. apply a minimal urgent patch and clearly report follow-up refactor need.

Flag these patterns:
- unrelated helpers appended to a shared file;
- new business logic added to an already mixed-responsibility file;
- generic `utils` or `helpers` dumping grounds created to avoid proper modularization.

### 6. Reuse the repository's existing error model
- Never demand a new global error taxonomy if the repository already has one.
- Review alignment with the existing module or subsystem conventions first.
- For coordinator and runner code, verify alignment with canonical classes and `E***` semantics when relevant.
- For web-facing API code, verify alignment with the structured envelope and `MACC-WEB-XXXX` semantics when relevant.
- Preserve context, retryability semantics, and useful raw causes.
- No silent catch-all and no swallowed failures.

### 7. Tests are part of correctness
- Changed behavior must be tested proportionally.
- Every bugfix should include a regression test when practical.
- Favor domain or unit tests first, then targeted integration tests.
- Tests must be deterministic.
- Time, randomness, and network dependencies should be controlled when relevant.

### 8. Observability must not regress
- Important failures must remain diagnosable.
- Structured logs, metrics, or tracing should be preserved or improved where relevant.
- MACC log inspection expectations must not be broken.

### 9. Documentation must be proportional
- Nearby docs, contract notes, examples, or module notes should be updated when behavior or interfaces changed.
- Do not require architecture noise for a micro task.
- A short architecture note or ADR is only expected for structural changes when the repository already uses that practice.

### 10. No broad transversal changes by default
- Repo-wide renames, formatting sweeps, library swaps, or mass refactors are out of scope unless the selected task clearly requires them.
- If such a change appears, verify that it is isolated, justified, and documented proportionally.

### 11. Global complexity must go down, not up
Before approving, verify that:
- coupling did not increase unnecessarily;
- invariants are clearer, not more implicit;
- testing is easier or at least not worse;
- no new god file or hot-file hotspot was created without explicit justification.

## Evidence Rules for Findings

Every finding must state all of the following:
- `where`: file, module, function, flow, or interface;
- `impact`: what can break, confuse, or become costly;
- `proof`: concrete observation, failing scenario, violated invariant, or missing protection;
- `suggested fix`: the smallest correction that would resolve the issue.

Do not label a stylistic preference as `must-fix`.

Use this severity logic:
- `must-fix` for incorrectness, broken invariants, unsafe behavior, contract mismatch, missing required test coverage for changed behavior, broken MACC compatibility, or unjustified structural risk;
- `should-fix` for maintainability risk, weak boundaries, growing hotspot risk, or missing but non-blocking observability/documentation;
- `nice-to-have` for polish, readability, or optional refinement.

If you are uncertain, say so explicitly.
Do not invent certainty.

## Strict Review Workflow

### Step 0 - Frame the review target
Build this working summary before judging the change:

- Task ID:
- Objective:
- Review mode: `micro | standard | structural`
- In scope:
- Out of scope:
- Available task fields:
- Dependencies:
- Exclusive resources:
- Touched modules:
- Touched hot/conflict areas:
- Dense file risk:
- Assumptions:

Rules:
- Restate the task objective in one sentence.
- Use the selected PRD entry as the source of truth.
- Identify whether the review depends on local MACC context files.
- Do not escalate scope before proving why.

### Step 1 - Verify MACC worktree context
When present, review against:
- `worktree.prd.json`
- `.macc/tool.json`
- `.macc/worktree.json`
- relevant local task/config files
- relevant `.macc/log/` expectations when the change touches orchestration or observability

Check that the implementation did not accidentally break task metadata, worktree-scoped assumptions, or review-phase expectations.

### Step 2 - Verify task scope and architecture boundaries
Check that:
- the delivered change matches one task objective;
- boundaries remain clear;
- new behavior appears at the right seam;
- shared hot files were touched only when justified;
- dense files were split, extracted, or minimally patched with explicit reasoning.

### Step 3 - Verify contracts and invariants
Check that:
- interfaces and types are coherent;
- invalid states are not made easier to represent;
- domain rules stay explicit;
- new abstraction really reduces complexity;
- public internal behavior, if changed, is understandable and proportionally documented.

### Step 4 - Verify existing error-model alignment
Check that:
- new failure paths map to the existing subsystem conventions;
- context and raw causes are preserved where useful;
- retryability or operator-action semantics were not damaged;
- web/API surfaces remain aligned with the structured error envelope when relevant;
- coordinator and runner flows remain aligned with canonical classes and `E***` semantics when relevant.

### Step 5 - Verify tests and determinism
Check that:
- changed behavior has proportional coverage;
- bugfixes include regression protection when practical;
- tests are deterministic;
- expensive end-to-end coverage was not used where smaller tests would suffice.

### Step 6 - Verify observability and diagnosability
Check that:
- important flows still emit useful diagnostics;
- structured logs, metrics, or tracing were preserved or improved where relevant;
- failure analysis remains practical for operators.

### Step 7 - Verify delivery readiness
Check that:
- changed docs and contract notes stay synchronized;
- local/generated artifacts are handled by the repository's ignore rules when relevant;
- the change set remains focused and reviewable;
- no accidental transversal repo-wide change slipped in.

### Step 8 - Produce an evidence-based review result
Return only findings that are grounded in the reviewed change.
Distinguish blockers from preferences.
State uncertainty explicitly when needed.

## Review Output Template

Use this exact structure:

## Summary
- Task reviewed:
- What the change does:
- Review mode: `micro | standard | structural`
- Risk level: `low | medium | high`
- Decision: `approve | changes_requested | blocked`
- Why:

## Must-fix
- [ ] Item 1 — where / impact / proof / suggested fix
- [ ] Item 2 — ...

## Should-fix
- [ ] Item 1 — where / impact / proof / suggested fix
- [ ] Item 2 — ...

## Nice-to-have
- [ ] Item 1 — where / impact / proof / suggested fix
- [ ] Item 2 — ...

## Verification Notes
- Tests to run or re-run:
- Edge cases to verify:
- Observability checks:
- Context files checked:

## Parallel-Safety Notes
- Hot/conflict areas touched:
- Exclusive resources involved:
- Dependencies on other tasks or phases:
- Suggested integration order if relevant:

## MACC Compatibility Notes
- Worktree context preserved: `yes | no | unclear`
- Existing error model aligned: `yes | no | unclear`
- Dense file policy respected: `yes | no | unclear`
- Proportional docs respected: `yes | no | unclear`
- Follow-up task needed: `yes | no`

## Reviewer Guardrails

Reject your own review and rewrite it if:
- you are requesting work that is outside the selected task without proving necessity;
- you are imposing a new repository-wide standard not already justified by MACC or the existing subsystem;
- you are calling a preference a blocker;
- you are flagging a god file without explaining the responsibility problem or the acceptable extraction path;
- you are criticizing missing artifacts that are disproportionate to a micro task;
- you are making claims without a concrete `where` and `proof`.
