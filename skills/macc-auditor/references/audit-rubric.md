# Audit rubric

Use this rubric to keep final compliance audits consistent.

| Dimension | Pass | Finding |
|---|---|---|
| Spec coverage | Every requirement has implementation and verification evidence | Missing, partial, ambiguous, or only asserted |
| Acceptance criteria | Each criterion maps to concrete evidence | Criterion absent from tests/manual verification |
| Behavior | Required user paths and states work together | Happy path only, missing state, edge case, or permission path |
| UI/design | Final UI follows required source and allowed adaptations | Functional but visually divergent, wrong copy, layout, token, state, or interaction |
| Design system | Uses required tokens/components/roles without unauthorized changes | New ad hoc styles, token drift, component bypass, protected-path change |
| Architecture | Matches accepted boundaries, contracts, data flow, and error model | Local success with global inconsistency or decision drift |
| Integration | Works coherently in the full product flow | Correct in isolation but incoherent globally |
| Regression risk | Relevant old behavior remains protected | Tests are too narrow or skip affected adjacent behavior |
| Debt/workaround | No hidden temporary path affects deliverability | TODO, hack, hardcoded shortcut, brittle mock, broad cleanup debt |

Severity rules:

- `blocking`: violates a must-have requirement, acceptance criterion, imposed design source, critical user path, security/privacy constraint, data integrity rule, or explicit architecture decision.
- `major`: important required behavior is incomplete, user case missing, integration incoherent, coverage materially weak, or workaround likely to affect near-term delivery.
- `minor`: localized issue with contained impact.
- `advisory`: non-blocking improvement or follow-up risk.

Prefer the highest justified severity. If severity depends on missing evidence, classify the report as `blocked` or mark the item `unverified`.
