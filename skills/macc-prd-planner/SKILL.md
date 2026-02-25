---
name: macc-prd-planner
description: >
  Use this skill whenever you (the AI planner) must generate or update a `prd.json` file that decomposes a development lot
  into very small, unambiguous tasks executable by AI agents (often in parallel). It enforces low coupling, explicit
  dependencies and exclusive resources, harmonized error-system planning, clear success criteria, and a consistent
  schema aligned with the repository's `prd.json.example`. Do NOT use for implementing code or doing code review.
---

# MACC PRD Planner `prd.json` Task Decomposition (Parallel-Aware)

## Mission
Produce a `prd.json` that breaks a development lot into **tiny, unambiguous, parallel-friendly tasks** that can be executed by AI agents in < 1 day each.

You must:
- minimize coupling and conflicts
- specify dependencies/exclusive resources
- define success criteria precisely
- enforce consistent error-system planning
- align with the repository’s **existing example schema** (`prd.json.example`)

---

## Hard Rules (Non-Negotiable)

1) **Tasks must be small**
- If a task can’t be done in < 1 day, split it
- Prefer more smaller tasks over fewer large tasks

2) **Every task must be unambiguous**
For each task, explicitly answer:
- Problem/Objective: what does it solve?
- Main actions: what will be done?
- Boundaries: what must NOT be done?
- Success criteria: how do we know it’s complete?

3) **Parallel safety is first-class**
Every task must include:
- `dependencies`: tasks that must be done first
- `exclusive_resources`: hot files/modules/paths that should not be modified in parallel
- guidance that avoids multi-agent collisions

4) **Architecture rules influence planning**
- Prefer domain/use-case splits
- Prefer contracts-first tasks (define interfaces/types before implementation)
- **Make illegal states unrepresentable**: Plan tasks to use dedicated types/enums instead of magic strings
- Avoid tasks that require global “utils” creation or cross-cutting refactors without an RFC task first

5) **Plan for a harmonized error system**
- Include tasks to define and document:
  - error taxonomy and stable nomenclature (e.g., `AAAA-XXXX-0000`)
  - error catalog documentation
  - tests for error mapping/propagation
- Ensure tasks specify where errors must be categorized and observed (logs/metrics)

6) **Definition of “Done” and Ownership**
A task is considered done only if:
- build OK, lint/format OK, tests OK
- docs/README/CHANGELOG updated
- observability added for critical flows
- no orphan TODOs (must include `TODO(owner, YYYY-MM-DD, reason)`)
- **Ownership**: The implementing agent is responsible for monitoring metrics/logs after merge.

---

# `prd.json` Output Requirements

## 1) Schema alignment (mandatory)
Before writing output:
- Locate and read the repo’s `prd.json.example`
- Match its top-level structure exactly (including `priority_mapping`, `assumptions`, `timezone`, `generated_at`)
- Ensure `generated_at` matches the current date.

Your output must be:
- valid JSON
- stable ordering and consistent formatting
- consistent ID naming

## 2) Task object requirements
Each task entry must include at least:
- `id`
- `title`
- `category`
- `description` (must include Problem/Actions/Out-of-scope/Success criteria)
- `objective`
- `result` (expected result)
- `steps` (explicit, checklist-like)
- `notes` (optional but recommended)
- `exclusive_resources` (list)
- `dependencies` (list)
- `priority` (use project mapping)

## 3) IDs and naming conventions
- IDs must be stable, unique, and searchable
- Use a consistent prefix by lot and area (follow repo patterns)
- Titles must be action-oriented (imperative verb)

---

# Planning Workflow (Follow in order)

## Step 0 — Understand the lot
- Define the lot goal in 2–5 bullet points
- List assumptions and constraints
- Identify “hot zones” (areas with high conflict risk)

## Step 1 — Decompose by domain/use-case
- Create a task map by domain boundaries
- Prefer separating:
  - contracts/types/invariants
  - infra adapters
  - integrations
  - docs/tests/observability

## Step 2 — Create “contracts-first” tasks
When parallel work is likely:
- create an early task that:
  - introduces interfaces/traits/ports
  - defines domain types (illegal states unrepresentable)
  - defines error contracts
  - adds minimal tests for invariants

Then create follow-up implementation tasks that depend on it.

## Step 3 — Explicit dependencies & exclusive resources
For each task:
- list `dependencies` (IDs)
- list `exclusive_resources`:
  - specific hot files
  - folders/modules
  - shared schemas/configs
  - global docs

Rule:
- if two tasks touch the same exclusive resource, they should not be scheduled in parallel

## Step 4 — Bake in quality gates
Ensure tasks include explicit sub-steps for:
- harmonized errors (taxonomy, code, docs)
- tests (unit/integration/E2E as needed)
- observability (logs/metrics/tracing)
- docs updates
- `.gitignore` updates if the task introduces generated/local artifacts

## Step 5 — Validate task size and clarity
Reject or split tasks that:
- require repo-wide refactors without RFC
- touch many domains at once
- have vague success criteria (“should work”, “improve”)
- depend on unknown decisions (create a separate “decision/RFC” task first)

---

# Output Checklist (Before delivering `prd.json`)
- [ ] Matches `prd.json.example` schema
- [ ] Every task includes unambiguous Problem/Actions/Out-of-scope/Success criteria
- [ ] Dependencies are explicit and minimal
- [ ] Exclusive resources listed for conflict-heavy areas
- [ ] Error-system tasks exist and are prioritized appropriately
- [ ] Tasks are small (< 1 day), split if needed
- [ ] DoD is implicitly satisfiable (build/lint/tests/docs/observability)
- [ ] JSON is valid and consistent

---

## Reference Schema (from `prd.json.example`)

Use this structure as the foundation for every `prd.json` generated:

```json
{
	"lot": "Lot Name",
	"version": "1.0",
	"generated_at": "YYYY-MM-DD",
	"timezone": "Europe/Paris",
	"priority_mapping": {
		"0": "P0 / This task should not be done in parallel with another.",
		"1": "P1 / Must-have for MVP",
		"2": "P2 / Should-have for MVP",
		"4": "P3 / Nice-to-have (MVP+) or preparatory",
		"5": "P4 / Lowest priority / can defer"
	},
	"assumptions": [
		"Assumption 1",
		"Assumption 2"
	],
	"tasks": [
		{
			"id": "LOT-AREA-001",
			"title": "Action-oriented title",
			"category": "category-name",
			"description": "Problem/Goal: ...\nKey actions: ...\nOut of scope: ...\nSuccess criteria: ...",
			"objective": "High-level goal",
			"result": "Expected physical result (files, state)",
			"steps": [
				"Step 1",
				"Step 2"
			],
			"notes": "Contextual notes",
			"exclusive_resources": ["file-or-module-path"],
			"dependencies": ["PREVIOUS-ID"],
			"priority": "1"
		}
	]
}
```