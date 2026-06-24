# UI fidelity policy

Before planning UI-sensitive work, inspect required HTML and design-system sources. Inventory regions, classes, CSS variables, styles, fonts, colors, spacing, radii, shadows, icons, assets, visible states, scripts, media queries, and literal copy. Inspect design-system entry points, tokens, themes, global styles, components, variants, stories, assets, fonts, icons, breakpoints, tests, and accessibility conventions.

Classify sources as `required`, `supporting`, or `inspiration`. Use the following default precedence:

1. Explicit task constraints
2. Task-specific screen or component specification
3. Imposed design system
4. Existing project patterns
5. Project-wide standards
6. Generic preferences

For `exact` work, preserve information architecture, hierarchy, composition, supplied tokens, icon family, product copy, and interaction semantics. Do not redesign or simplify. For `adaptive` work, list each allowed adaptation. For `exploratory` work, record the permitted exploration boundary.

Every design-system task has one role: `consumer`, `extension`, `migration`, or `none`. A consumer cannot change the system. Missing material information or conflicting required sources require resolution, not creative interpretation.

Keep each screen/component task as a coherent unit including structure, styling, variants, local interactions, responsive behavior, applicable states, local accessibility, tests, and evidence. Split complex screens by independently coherent regions only after a stable contract and shared primitives exist.
