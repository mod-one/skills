---
name: macc-prd-planner
description: >
  Use this skill whenever you (the AI planner) must generate or update a `prd.json` file for MACC.
  It decomposes a lot into small, unambiguous, parallel-safe tasks that stay compatible with
  worktree-scoped execution, coordinator scheduling, PRD reconciliation, existing error conventions,
  and token-efficient model routing by phase. Do NOT use for implementation or code review.
---

# MACC PRD Planner Skill - `prd.json` Generator and Updater

## Mission

Produce or update a `prd.json` that helps MACC execute work with:
- very small, clear tasks;
- minimal coupling and minimal collision risk;
- stable task IDs;
- compatibility with MACC worktree context files and PRD reconciliation flows;
- proportional validation expectations;
- routing hints that help the coordinator or runner choose the lightest viable model.

The planner classifies tasks.
The planner does **not** choose concrete provider/model names.
Model selection remains a coordinator or runner responsibility.

## Use This Skill When

- a new development lot must be decomposed into `prd.json` tasks;
- an existing `prd.json` must be updated without breaking task identity;
- the repository already follows MACC conventions or is being planned for MACC execution;
- parallel execution and resource contention matter.

## Do Not Use This Skill For

- implementing code;
- reviewing code changes;
- forcing provider-specific model names into tasks;
- inventing a new repository-wide error taxonomy when one already exists.

## MACC Planning Context

Treat these constraints as mandatory whenever they are relevant in the repository:

- `prd.json.example` is the schema source of truth.
- `worktree.prd.json` is the worktree-scoped task context used by performers.
- `.macc/tool.json` describes tool-specific execution context.
- `.macc/worktree.json` describes worktree identity and local scope.
- `.macc/log/` and adjacent MACC runtime artifacts are hot/shared operational areas.
- The coordinator schedules READY tasks using fields such as `priority`, `dependencies`, `exclusive_resources`, `category`, and `id`.
- `sync-prd` and `audit-prd` rely on task identity stability and accurate task state descriptions.

Do not produce a plan that would make these flows ambiguous or fragile.

## Core Planning Principles

### 1. Plan for execution, not for theory
A good task should be directly executable by a performer with little interpretation.

Each task must clearly answer:
- what problem it solves;
- what will be changed;
- what stays out of scope;
- what concrete result must exist when the task is complete.

### 2. Keep tasks small
Default target: one task should fit comfortably within one focused performer run.

If a task feels broad, split it.
Prefer more small tasks over fewer broad tasks.

### 3. Parallel safety is first-class
Every task must explicitly consider:
- `dependencies`;
- `exclusive_resources`;
- hot files or hot folders;
- shared schemas, shared contracts, shared operational files, and shared docs.

If two tasks would likely collide, either:
- add the right dependency,
- assign the same `exclusive_resources`,
- or split the work differently.

### 4. Plan by responsibility boundaries
Prefer task boundaries that align with:
- domain contracts and invariants,
- adapters and integrations,
- validation or mapping seams,
- UI/API surface changes,
- docs or observability work only when separately useful.

Avoid planning around vague dumping grounds such as generic `utils`, broad “cleanup”, or “misc fixes”.

### 5. Reuse the repository's existing error model
Do not force a new global error taxonomy into the plan.

Plan tasks to reuse the repository's existing error conventions first.
When relevant:
- coordinator and runner work should stay compatible with canonical classes and existing `E***` semantics;
- web-facing API work should stay compatible with the structured envelope and `MACC-WEB-XXXX` conventions;
- other modules should follow their local subsystem conventions.

Only create explicit error-model work when the lot truly changes error handling behavior, mappings, or observability.

### 6. Proportionality over uniform heaviness
Do not give every task the same delivery burden.
Use the lightest planning mode that still protects quality.

### 7. Stable identity matters
When updating an existing `prd.json`:
- preserve task IDs whenever the task is still conceptually the same;
- do not rename IDs casually;
- do not delete or rewrite completed-task meaning lightly;
- prefer updating `description`, `notes`, `result`, or `steps` over changing identity.

The plan must remain compatible with later `sync-prd` and `audit-prd` operations.

## Task Planning Modes

Each task should be classified with the lightest planning mode that fits.

### Micro
Use when the task is local, low-risk, and narrow.
Examples:
- focused bugfix in one module;
- small validation update;
- narrow test addition;
- tiny adapter correction;
- local docs clarification.

Expected shape:
- one small scope;
- few touched files;
- minimal dependencies;
- light validation profile;
- no architecture note unless explicitly required.

### Standard
Use when the task changes behavior across a small boundary or introduces a new internal seam.
Examples:
- new contract plus one implementation task;
- targeted API endpoint change;
- coordinator rule update in one subsystem;
- moderate refactor inside one domain.

Expected shape:
- module-level context;
- targeted tests;
- proportional observability expectations;
- stronger dependency and exclusive-resource mapping.

### Structural
Use only when the task changes shared contracts, orchestration rules, cross-module architecture, or a major hotspot.
Examples:
- shared schema changes;
- deep refactor of a hotspot or god file;
- coordinator dispatch logic changes;
- migration of a shared interface used by multiple performers.

Expected shape:
- cross-cutting context is explicit;
- migration or compatibility thinking is visible;
- stronger validation profile;
- architecture note or decision task when needed.

## Anti-God-File and Hotspot Planning Policy

The planner must reduce collisions before implementation begins.

A file or area is considered risky when one or more of these signals appear:
- it mixes unrelated responsibilities;
- it changes for unrelated tasks;
- it is difficult to test in isolation;
- it is a recurring conflict hotspot;
- it grows faster than neighboring files or modules;
- multiple upcoming tasks would need to touch it.

Soft thresholds for attention:
- over 300 lines: check whether responsibilities are already mixed;
- over 500 lines: avoid adding more unrelated logic without an extraction plan;
- over 800 lines: prefer a split or extraction task before feature growth unless clearly justified.

Planner actions for risky files or hotspots:
- create an extraction or split task before feature growth when possible;
- mark the area in `exclusive_resources` if parallel collision risk is real;
- avoid generating several simultaneous tasks that all require the same dense file;
- prefer nearby module extraction over continued expansion of a central file.

Forbidden planning patterns:
- tasks that tell performers to append more unrelated helpers to a shared file;
- several parallel tasks that all depend on the same dense file without exclusivity;
- vague “cleanup” tasks that hide structural refactors inside feature work.

## Routing Hints for Token-Efficient Model Selection

The planner should provide **routing hints**, not concrete models.

Why:
- token efficiency depends on phase, risk, and scope;
- the same task may need light reasoning for triage and deeper reasoning for architecture review;
- the coordinator or runner knows the current tool inventory and can map abstract hints to actual models.

### Required rule
Every task should include a `routing_hints` object unless the repository schema forbids custom fields.

Recommended fields:
- `execution_mode`: `micro | standard | structural`
- `reasoning_depth`: `light | standard | deep`
- `context_scope`: `local | module | cross-cutting`
- `risk_level`: `low | medium | high`
- `validation_profile`: `light | standard | heavy`

Recommended default interpretation:
- exploration, triage, light review, summary -> `reasoning_depth: light`
- normal implementation planning -> `reasoning_depth: standard`
- hard planning, deep refactor, architecture, recovery analysis -> `reasoning_depth: deep`

Escalate one level when one or more of these are true:
- `execution_mode` is `structural`;
- `context_scope` is `cross-cutting`;
- `risk_level` is `high`;
- the task affects shared contracts or operational hotspots.

Do not encode provider names, vendor SKUs, or tool-specific model identifiers into the PRD.

## Schema Alignment Rules

### Repository schema is the source of truth
Before writing output:
- locate and read the repository's `prd.json.example` when available;
- match its top-level structure and required fields exactly;
- preserve ordering and formatting conventions used by the repository;
- ensure `generated_at` matches the current date;
- use the repository's timezone and priority mapping conventions.

### Embedded schema is only a memory aid
If this skill includes an example schema later in the document, treat it only as a reminder.
Do not prefer it over the repository's actual `prd.json.example`.

### Input tolerance when updating
When reading an existing `prd.json`:
- preserve fields that already exist and are still meaningful;
- do not fail because optional fields are absent;
- add new optional fields only when they improve execution clarity and stay compatible with the repo schema.

## Required Task Fields

At minimum, each task should include the fields required by the repository schema.
Common fields usually include:
- `id`
- `title`
- `category`
- `description`
- `objective`
- `result`
- `steps`
- `exclusive_resources`
- `dependencies`
- `priority`

Recommended optional fields when supported:
- `notes`
- `labels`
- `routing_hints`

## Task Authoring Rules

### IDs and naming
- IDs must be stable, unique, and searchable.
- Use a consistent prefix by lot and area.
- Titles must be action-oriented and concrete.
- Preserve IDs for conceptually unchanged tasks during updates.

### Description quality
Each task description should include:
- Problem or Goal
- Key Actions
- Out of Scope
- Success Criteria

Avoid vague phrasing such as:
- “improve system”
- “cleanup code”
- “make it better”
- “fix issues”

### Steps quality
Steps should be short, concrete, and sequenced.
Do not turn `steps` into a huge implementation SOP.
Use steps to clarify execution order, not to micromanage the performer.

### Result quality
`result` must describe the expected tangible state:
- files, modules, endpoints, schemas, task metadata, docs, or observable behavior.

## Planning Workflow

### Step 0 - Frame the lot
Produce a short planning frame:
- lot goal;
- assumptions;
- constraints;
- existing PRD or new PRD;
- hot zones;
- shared operational files or directories;
- likely cross-cutting seams.

### Step 1 - Read the MACC context
When present, inspect the planning context that affects execution safety:
- `prd.json.example`
- existing `prd.json`
- `worktree.prd.json`
- `.macc/tool.json`
- `.macc/worktree.json`
- `.macc/log/` and nearby operational paths

Do not plan tasks that casually rewrite MACC operational files unless the lot explicitly requires it.

### Step 2 - Decide task boundaries
Break the lot by responsibility boundaries.
Prefer separating:
- contracts, types, invariants;
- implementation behind a contract;
- adapter/integration changes;
- docs or observability when they deserve separate tracking;
- structural extraction work from feature work when hotspots are involved.

### Step 3 - Add contracts-first tasks when useful
When parallel work or shared contracts are likely:
- create an early task for the contract, schema, type, invariant, or interface boundary;
- make downstream implementation tasks depend on it.

Do this only when it genuinely reduces collisions or ambiguity.
Do not create ceremonial contract tasks for trivial micro work.

### Step 4 - Set dependencies and exclusive resources
For each task:
- keep `dependencies` minimal and explicit;
- add `exclusive_resources` for true hotspots, dense files, shared schemas, shared docs, shared operational files, or high-conflict paths;
- avoid fake exclusivity on areas that can safely proceed in parallel.

If two tasks touch the same real hotspot, they should not be parallel-ready at the same time.

### Step 5 - Classify routing hints
For each task, classify:
- `execution_mode`
- `reasoning_depth`
- `context_scope`
- `risk_level`
- `validation_profile`

The planner classifies.
The runtime maps those hints to the lightest viable model.

### Step 6 - Apply proportional delivery expectations
Plan the minimum necessary validation.
Do not blindly attach the same checklist to every task.

Typical guidance:
- micro -> focused validation, targeted test update if behavior changes;
- standard -> targeted tests and proportional observability updates when relevant;
- structural -> stronger validation and explicit compatibility thinking.

Do not assign post-integration operational monitoring ownership to performers inside task text.
That belongs to runtime operations, coordinator supervision, or the human/operator layer.

### Step 7 - Validate clarity and execution safety
Split or rewrite any task that:
- touches too many domains at once;
- hides a hotspot refactor inside a feature task;
- has vague success criteria;
- depends on an unresolved architecture decision;
- would break ID stability during PRD updates;
- would force several performers into the same dense file without exclusivity.

### Step 8 - Validate PRD update safety
When updating an existing PRD:
- keep completed tasks stable unless they are genuinely wrong;
- do not repurpose an old ID for a different meaning;
- prefer adding new tasks for newly discovered work;
- adjust notes, descriptions, results, and steps of remaining tasks to reflect the latest known reality;
- preserve compatibility with later `audit-prd` refinement.

## Output Checklist

Before delivering `prd.json`, verify:
- it matches the repository's `prd.json.example` schema;
- task IDs are stable, unique, and update-safe;
- every task has clear problem, actions, out-of-scope, and success criteria;
- dependencies are explicit and minimal;
- exclusive resources are used for true collision areas;
- hotspots and god-file risks were planned around, not ignored;
- error handling expectations reuse the existing repository conventions;
- delivery expectations are proportional to task type;
- routing hints are present when allowed by the schema;
- the JSON is valid and consistently formatted.

## Minimal Reference Shape

Use this only as a reminder if the repository example is unavailable.

```json
{
  "lot": "Lot Name",
  "version": "1.0",
  "generated_at": "YYYY-MM-DD",
  "timezone": "Europe/Paris",
  "priority_mapping": {
    "0": "P0 / This task should not be done in parallel with another!",
    "1": "P1 / Must-have",
    "2": "P2 / Should-have",
    "3": "P3 / Nice-to-have or preparatory",
    "4": "P4 / Lowest priority"
  },
  "routing_hints_mapping": {
    "execution_mode": "micro | standard | structural",
    "reasoning_depth": "light | standard | deep",
    "context_scope": "local | module | cross-cutting",
    "risk_level": "low | medium | high",
    "validation_profile": "light | standard | heavy"
  },
  "assumptions": [],
  "tasks": [
    {
      "id": "LOT-AREA-001",
      "title": "Action-oriented title",
      "category": "category-name",
      "description": "Problem/Goal: ...\nKey actions: ...\nOut of scope: ...\nSuccess criteria: ...",
      "objective": "High-level goal",
      "result": "Expected result",
      "steps": [
        "Step 1",
        "Step 2"
      ],
      "notes": "Contextual notes",
      "exclusive_resources": [
        "path-or-module"
      ],
      "dependencies": [],
      "priority": "1",
      "routing_hints": {
        "execution_mode": "standard",
        "reasoning_depth": "standard",
        "context_scope": "module",
        "risk_level": "medium",
        "validation_profile": "standard"
      }
    }
  ]
}
```

## Refusal or Escalation Conditions

Stop and report instead of improvising when:
- the repository schema and the requested output conflict in a way that cannot be reconciled safely;
- the lot would require repurposing existing task IDs in a misleading way;
- the only apparent plan would hide a major architecture decision inside ordinary feature tasks;
- the user asks for provider-specific model binding directly inside the PRD even though runtime selection should stay abstract.
