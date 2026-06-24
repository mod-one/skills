# Task profile guide

Use `planning_profile` independently from `routing_hints.execution_mode`.

| Profile | Use for | Do not use for |
|---|---|---|
| `general` | Backend, data, infrastructure, docs, tests, CLI, refactors | A task requiring a visual contract |
| `frontend-logic` | Client data, stores, guards, caching, streams, build setup | A material visual or interaction implementation |
| `ui-fidelity` | Implementing approved UI from mandatory sources | New visual direction explicitly open to exploration |
| `ui-exploration` | Explicitly requested visual alternatives or concepts | Existing/approved screens or imposed design systems |
| `design-system-change` | System extension, migration, replacement, tokenization | A screen consuming an unchanged system |
| `ux-review` | Review-only fidelity, usability, accessibility, consistency | Primary production implementation |

Profile minimums:

- `general` and `frontend-logic`: normal task contract and proportional validation.
- `ui-fidelity`: exact/adaptive/exploratory fidelity mode, typed sources, scope, applicable states/viewports, evidence, observable criteria.
- `ui-exploration`: sources and constraints still matter, but use `exploratory` only with explicit authorization.
- `design-system-change`: role `extension` or `migration`; include compatibility, rollout impact, documentation, and downstream tasks.
- `ux-review`: sources, states, viewports, evidence, acceptance criteria, and structured review output.

Use `micro`, `standard`, and `structural` for breadth/risk. A `ui-fidelity` component can be `micro`; a design-system migration is usually `structural`.
