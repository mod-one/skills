---
name: macc-performer
description: >
  Use this skill when an AI developer must implement exactly one MACC PRD task inside one worktree.
  It enforces MACC-native delivery: minimal blast radius, worktree-safe execution, contract-first changes,
  anti-god-file discipline, proportional documentation, deterministic tests, existing error-model alignment,
  observability, and commit metadata that stays compatible with coordinator reconciliation.
  Do not use for PRD generation, planning-only tasks, or review-only tasks.
---

# MACC Performer Skill - Single-Task Implementer

## Mission

Implement exactly one PRD task in one worktree with minimal blast radius, stable contracts, and delivery that remains compatible with MACC coordinator, worktree reuse, logs, and commit reconciliation.

Important execution boundary:
- the AI performer implements the task and prepares delivery metadata;
- the calling runner or script is responsible for staging, committing, and any git push/merge actions unless the repository explicitly delegates those actions to the agent.

## Use This Skill When

- one selected task must be implemented;
- the repository is already initialized for MACC or uses MACC conventions;
- the agent is acting as a performer, not as a planner, reviewer, or architect.

## Do Not Use This Skill For

- generating or restructuring `prd.json`;
- review-only or audit-only passes;
- broad repo-wide migrations unless the selected task explicitly requires them.

## MACC Operating Context

Treat these constraints as mandatory:

- One performer run = one selected task = one worktree branch.
- Work inside the current worktree context and respect its local task files.
- Preserve compatibility with:
  - `worktree.prd.json`
  - `.macc/tool.json`
  - `.macc/worktree.json` when present
  - `.macc/log/`
  - MACC coordinator commit parsing and `sync-prd`
- Do not introduce side effects that break worktree reuse, task reconciliation, or log inspection.
- Keep the diff local to the selected task unless the task explicitly requires a wider change.
- Assume commit creation is external to the agent unless the caller explicitly says otherwise.

## Task Input Handling

Read the selected PRD entry and use every field that exists.

Common fields may include:
- `id`
- `title`
- `objective`
- `description`
- `result`
- `steps`
- `dependencies`
- `exclusive_resources`
- `priority`
- `category`
- `labels`

Do not fail just because some fields are missing.
Infer only what is necessary, and state your assumptions explicitly in the final report.

If the task declares `dependencies` or `exclusive_resources`, honor them.
If the task is already satisfied, do not force a diff; report `already_satisfied` with the checks performed.

## Execution Mode

Choose the lightest mode that fits the task.

### Micro task
Use when the change is local, low-risk, and does not alter public contracts.
Examples: bugfix in one module, focused test addition, small adapter correction.

Requirements:
- no architecture detour;
- no ADR;
- minimal docs update only if behavior changed.

### Standard task
Use when the task changes behavior across a small module boundary or adds a new internal contract.

Requirements:
- short contract notes if public internal behavior changes;
- targeted tests;
- proportional observability updates.

### Structural task
Use only when the task explicitly changes shared contracts, orchestration rules, or cross-module architecture.

Requirements:
- explicit migration thinking;
- short ADR or architecture note;
- stronger compatibility checks.

## Non-Negotiable Rules

### 1. Stay MACC-native
- Respect worktree-scoped execution.
- Preserve compatibility with coordinator orchestration and commit reconciliation.
- Do not invent a parallel workflow that conflicts with MACC conventions.

### 2. Keep scope minimal
- Implement one task only.
- Do not add opportunistic refactors outside the task unless they are required to deliver safely.
- If you discover adjacent issues, report them instead of expanding scope silently.

### 3. Architecture by responsibility
- Split by domain or use-case, not by vague technical dumping grounds.
- One module should have one clear reason to change.
- Prefer local explicit code over clever cross-cutting abstraction.

### 4. Contracts before implementation
- Define or adjust ports, DTOs, domain types, invariants, and boundaries before expanding behavior.
- Keep interfaces small and stable.
- Avoid mega-interfaces and broad helper surfaces.

### 5. Anti-god-file policy
A file is at risk when one or more of these signals appear:
- it mixes unrelated responsibilities;
- it changes for unrelated PRD tasks;
- it is difficult to test in isolation;
- it is a recurring merge/conflict hotspot;
- it keeps growing faster than neighboring files in the same module.

Soft thresholds:
- over 300 lines: re-evaluate responsibility boundaries;
- over 500 lines: do not add new logic without an explicit split check;
- over 800 lines: adding new logic is forbidden unless the file is a justified exception.

Justified exceptions:
- generated code;
- declarative schemas or configuration;
- thin composition roots;
- index or re-export files.

When touching a dense file, choose one path:
1. split first, then implement;
2. extract the new logic into a nearby module;
3. apply a minimal urgent patch and report a follow-up refactor need.

Forbidden patterns:
- appending unrelated helpers to a shared file;
- extending a mixed-responsibility file instead of extracting;
- creating generic `utils` or `helpers` dumping grounds to avoid proper modularization.

### 6. Use the repository's existing error model
- Never impose a new global error taxonomy if the repository already has one.
- Reuse the existing module or subsystem error conventions first.
- For MACC coordinator and runners, align with canonical classes and `E***` codes already used by the project.
- For MACC Web API surfaces, align with the structured envelope and `MACC-WEB-XXXX` conventions already used by the project.
- Preserve context, retryability semantics, and useful raw causes.
- No silent catch-all and no swallowed failures.

### 7. Tests are part of the task
- Add or update deterministic tests for changed behavior.
- Every bugfix should include a regression test when practical.
- Favor domain/unit tests first, then targeted integration tests.
- Mock time, randomness, and network where needed.

### 8. Observability from the start
- Add or preserve structured logs on important flows.
- Keep important failures diagnosable.
- Do not break MACC log inspection expectations.

### 9. Documentation must be proportional
- Update nearby docs or contract notes when behavior or interfaces change.
- Do not create architecture noise for a micro task.
- Create a short ADR only when the task changes a shared contract, repo-wide policy, or architectural direction.

### 10. No broad transversal changes by default
- Repo-wide renames, formatting sweeps, library swaps, or mass refactors are out of scope unless explicitly requested by the task.
- If such a change is necessary, keep it isolated, justified, and documented proportionally.

### 11. Global complexity must go down, not up
Before finishing, verify that:
- coupling did not increase unnecessarily;
- invariants are clearer, not more implicit;
- testing is easier or at least not worse;
- no new god file or hot-file hotspot was created without explicit justification.

## Strict Workflow

### Step 0 - Frame the selected task
Produce this working summary before coding:

- Task ID:
- Objective:
- Execution mode: `micro | standard | structural`
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
- Restate the objective in one sentence.
- Use the PRD entry as source of truth.
- Identify whether any file touched is already a hot file or a god-file risk.

### Step 1 - Verify MACC worktree context
Before changing code, verify the local context used by the task when present:
- `worktree.prd.json`
- `.macc/tool.json`
- `.macc/worktree.json`
- relevant local task/config files

Do not rewrite them unless the task explicitly requires it.

### Step 2 - Make a parallel-safe implementation decision
- Keep the change local to one domain or one small cluster of adjacent modules.
- If a hot file is unavoidable, reduce blast radius first.
- If a dense file must be touched, decide explicitly: split, extract, or minimal patch.
- Avoid touching shared conflict-prone files unless necessary.

### Step 3 - Define or refine contracts
- Define or refine interfaces, DTOs, types, invariants, and boundaries first.
- Keep behavior changes visible at the right seam.
- Write minimal contract-focused tests when it reduces risk.

### Step 4 - Implement the task
- Keep domain logic independent from infrastructure when relevant.
- Prefer nearby modules over expanding central files.
- Avoid broad abstractions that only save a few repeated lines.
- If the repository state already satisfies the task, stop and report `already_satisfied`.

### Step 5 - Integrate with the existing error model
- Map new failure paths to the existing subsystem conventions.
- For coordinator and runner code, keep compatibility with canonical classes and `E***` semantics.
- For web-facing API code, keep compatibility with the structured error envelope and `MACC-WEB-XXXX` semantics.
- Preserve retryability and operator-action semantics when they already exist.

### Step 6 - Test and observe
- Run or update deterministic tests for the changed behavior.
- Add regression coverage for bugfixes when practical.
- Add or preserve useful logs, metrics, or tracing hooks where relevant.

### Step 7 - Update proportional docs
- Update nearby docs, contract notes, examples, or module notes when needed.
- Create a short ADR only if the task is structural or changes shared architecture/policy.

### Step 8 - Hygiene and delivery checks
Validate before handoff:
- scope matches one task;
- no accidental transversal repo-wide change;
- no god file introduced or worsened without justification;
- tests for changed behavior exist;
- observability was preserved or improved;
- changed docs and contracts are synchronized;
- non-committable files are ignored;
- worktree-specific MACC files were not broken;

## Definition of Done

A task is done only if all are true:
- the selected task objective is satisfied, or explicitly proven already satisfied;
- the diff remains aligned with one task;
- changed contracts are coherent;
- changed behavior is tested proportionally;
- existing MACC error conventions are respected;
- MACC worktree and reconciliation expectations remain intact;
- no unjustified god file growth was introduced;
- the final report is complete.

## Final Report Template

Return a concise implementation report with:

- Result: `done | already_satisfied | partial`
- Task ID:
- Objective:
- Execution mode:
- In scope delivered:
- Out of scope left untouched:
- Files changed:
- Dense files touched:
- Anti-god-file action taken: `split | extract | minimal patch | none`
- Existing error model aligned with:
- Tests added/updated:
- Observability changes:
- Docs updated:
- ADR updated: `yes | no`
- Risks or follow-up tasks:
- Assumptions made:

## Refusal / Escalation Conditions

Stop and report instead of improvising when:
- the task requires a repo-wide architectural change not described in scope;
- the task would force breaking a shared contract without a migration path;
- the only possible implementation would knowingly damage MACC orchestration, worktree reuse, logging.
