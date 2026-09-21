# Human approval gate policy

A human approval gate is a task with `gate.kind: human_approval`. It carries no work: the MACC coordinator never sends it to a performer, never retries it, and never gives it a worker. It waits in `waiting_approval` until people record the quorum with `macc coordinator approve`, then satisfies its dependants like a merged task. Schema: [human-approval-gate.schema.json](../schemas/human-approval-gate.schema.json). Template: [human-approval-gate-task.json](../templates/human-approval-gate-task.json).

## When to create one

Create a gate only when one of these triggers applies, and set it in `gate.approval_trigger`:

| Trigger | Use when the subject task… |
|---|---|
| `normative-change` | changes a normative specification, contract, or policy text |
| `adr` | proposes an architecture decision record |
| `open-product-decision` | resolves a product decision the specification leaves open |
| `sensitive-architecture` | fixes an architecture choice that is costly to reverse |
| `sensitive-data-model` | fixes a sensitive or shared data model |
| `security`, `identity`, `payment`, `privacy` | decides behaviour in that domain |
| `irreversible-migration` | defines a migration that cannot be rolled back |
| `production-activation`, `gate-crossing` | activates production behaviour or crosses a release gate |

Do not add a gate for routine implementation, refactors, tests, documentation, or a decision the specification already settles. Ordinary review belongs to the reviewer phase; a verdict an agent can evaluate belongs to a `gate` without `kind` (verdict gate).

## Derive the approvers; never invent them

Take the roles from the repository's specification governance, never from habit. `macc_prd.py inspect` lists `governance_sources` (CODEOWNERS, governance/RACI documents, roles-and-permissions, decision logs, ADRs) with `role_candidates`. Choose the source that assigns decision rights for the subject's domain, cite it in `gate.governance_ref`, and copy role names exactly as it writes them. Validation fails (`MACC-PRD-8003`) when a role does not appear in the cited source.

Prefer an `approval-matrix` source: its `approval_rules` map each decision domain to its approvers (for example `sécurité/identité → Responsable sécurité + Lead technique`), so pick the row matching the subject's `approval_trigger`. Application RBAC roles that grant end-user permissions in the product are not decision approvers unless the source says they approve this kind of decision.

Do not default to "Product Owner + architect". If no governance source defines who approves this kind of decision, stop and report it: that is a missing specification, not a gap to fill with assumptions.

## Graph shape

Split proposal, approval, and implementation:

```text
SEC-CR-001     contractual proposal
     ↓
SEC-ADR-003    the agent drafts the model and the ADR     (executable)
     ↓
SEC-APP-003    human gate, never sent to a performer       (gate.subject_task = SEC-ADR-003)
     ↓
SEC-DB-004     migration                                   (depends on SEC-APP-003)
     ↓
SEC-API-003    implementation
```

- The subject is a real executable task that produces the artefact to approve. List it in the gate's `dependencies` and name it in `subject_task`.
- Everything that must wait for the decision depends on the gate, not on the subject.
- The gate has no `change_scope.allowed_paths` and no implementation steps (`MACC-PRD-8002`).
- Use `bind_to: commit_sha` and keep `invalidate_on_subject_change: true`: a new revision of the subject withdraws the approval automatically.
- Set `evidence_type` to where the human proof lives (`pull_request_review`, `merge_request_approval`, `adr`, `changelog`); use `manual` only when the governance source accepts an unrecorded decision.
- List concrete `risks` the approvers must weigh.

## What a gate is not

`precondition_unmet` means a task cannot be executed. Waiting for a normal approval is neither a failure nor a technical block: model it as a gate so the coordinator waits without spending a worker. A performer must never produce or simulate the approval itself.
