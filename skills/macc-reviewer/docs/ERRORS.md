# MACC Error Catalog & Nomenclature

This document is the single source of truth for error codes in the MACC ecosystem. All agents must refer to this file before creating or reviewing error codes.

## 1. Nomenclature Rules

Format: `[FEATURE]-[DOMAIN]-[CODE]`
- **[FEATURE]**: 4-character uppercase feature identifier.
- **[DOMAIN]**: 4-character uppercase domain identifier.
- **[CODE]**: 4-digit incremental number (starting from 0001).

Example: `MACC-AUTH-0001`

## 2. Error Categories

Every error must belong to one of these categories:
- **Validation**: Input or state is invalid.
- **Auth**: Authentication or Authorization failure.
- **Dependency**: External service or DB failure.
- **Conflict**: Resource already exists or state conflict.
- **NotFound**: Resource does not exist.
- **Internal**: Unexpected system error.

## 3. Registered Domains

| Prefix | Domain | Description |
| :--- | :--- | :--- |
| **AUTH** | Authentication | Login, JWT, Roles, Permissions. |
| **INFRA** | Infrastructure | Kubernetes, ArgoCD, Networking, Storage. |
| **DATA** | Data / DB | Persistence, Schemas, Migrations. |
| **DOMN** | Domain Logic | Core business rules and invariants. |
| **REPO** | Repository | Git, PRD, CI/CD pipelines. |
| **OBSV** | Observability | Logs, Metrics, Tracing. |

## 4. Error Registry (Active Codes)

| Code | Category | Description |
| :--- | :--- | :--- |
| **MACC-AUTH-0001** | Auth | Missing or invalid authentication token. |
| **MACC-AUTH-0002** | Auth | Insufficient permissions for this action. |
| **MACC-INFRA-0001** | Dependency | Failed to connect to Kubernetes API. |
| **MACC-DATA-0001** | Validation | Schema validation failed for the provided input. |
| **MACC-DOMN-0001** | Conflict | Business invariant violation (state transition forbidden). |
| **MACC-REPO-0001** | Internal | PRD file is corrupted or missing mandatory fields. |

---

*Note for Agents: When creating a new code, append it to this table and ensure it does not duplicate an existing number within the same domain.*
