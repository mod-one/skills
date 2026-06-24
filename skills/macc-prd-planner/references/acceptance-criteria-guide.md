# Acceptance criteria guide

Use objective criteria. Name the source, state, viewport, behavior, or protected boundary being checked.

Good examples:

- Only typography, color, spacing, radius, and shadow tokens from `web/src/design-system/` are used.
- The `populated`, `empty`, and `error` states match their named required references at 1440×900 and 390×844.
- Keyboard focus follows the existing design-system focus treatment and every interactive control has an accessible name.
- No file in `read_only_paths` or `forbidden_paths` changes.
- Required screenshot, interaction-test, token-audit, and protected-path evidence exists.

Do not use “polished”, “modern”, “intuitive”, “improved UX”, or an unsupported “matches the design”.

When custom PRD fields are unsupported, include these labeled description sections:

```text
Authoritative references:
Source authority and precedence:
Fidelity mode:
Design-system role:
Allowed changes:
Read-only references:
Forbidden changes:
Required states:
Required viewports:
Required evidence:
Out of scope:
Success criteria:
```

Add labels such as `frontend-ui`, `ui-fidelity`, `design-system-consumer`, and `visual-review-required` where supported.
