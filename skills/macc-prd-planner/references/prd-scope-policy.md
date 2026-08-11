# PRD scope policy

One PRD file has one file-level scope.

Use `feature` when the PRD delivers one coherent user-visible, API-visible, operational, or business capability. Supporting docs, tests, migrations, and local refactors belong in the same PRD only when they are necessary to deliver that single capability.

Use `shared-foundation` when the PRD delivers reusable substrate for multiple future features: shared contracts, auth/session base, design-system primitives, routing shell, build/test scaffolding, cross-feature data model, or migration groundwork. It may name downstream consumers in `consumer_feature_ids`, but it must not implement any downstream feature's specific UI, workflow, copy, or business behavior.

Split into separate PRDs when:

- two tasks can ship independent user/business capabilities;
- a task has a different `scope_ref`, `feature_id`, `scope_refs`, or `feature_ids`;
- a shared-foundation PRD starts delivering one consuming feature;
- a feature PRD contains foundation work that is not required by that feature.

Keep cross-cutting work inside a feature PRD only when it is inseparable from that feature and explicitly marked out of scope for other feature behavior.
