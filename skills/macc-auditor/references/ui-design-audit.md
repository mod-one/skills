# UI and design audit

Use this reference when the final result has UI, visual, interaction, or design-system impact.

Check required design sources first:

- screenshot, mockup, HTML reference, Figma export, graphic charter, design-system docs, component stories, existing reference screen;
- source authority: required, supporting, inspiration;
- fidelity mode: exact, adaptive, exploratory;
- design-system role: consumer, extension, migration, none.

Audit these dimensions:

- information architecture and hierarchy;
- layout, alignment, density, spacing, radii, shadows;
- typography, color, icon family, imagery, copy;
- component choice and allowed variants;
- required states: loading, empty, error, disabled, focused, hover, selected, populated;
- responsiveness and viewport-specific behavior;
- keyboard and screen-reader accessibility;
- interaction semantics and transitions;
- protected design-system paths and token usage.

Finding examples:

- `blocking`: exact approved design required but final screen changes layout, copy, or component hierarchy.
- `blocking`: consumer task modifies design-system tokens without authorization.
- `major`: required empty/error state absent.
- `major`: functional UI uses ad hoc styling instead of imposed components.
- `minor`: small spacing mismatch with no user-flow impact when exact fidelity was not required.

Do not accept “UI works” as design compliance. Functional correctness and fidelity are separate checks.
