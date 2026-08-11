# Diagnostic guide

| Code | Meaning | Blocking |
|---|---|---|
| `MACC-PRD-1001` | Invalid JSON | Yes |
| `MACC-PRD-1002` | PRD shape/schema mismatch | Yes |
| `MACC-PRD-2001` | Duplicate task ID | Yes |
| `MACC-PRD-2002` | Unknown dependency | Yes |
| `MACC-PRD-2003` | Dependency cycle | Yes |
| `MACC-PRD-3001` | Parallel tasks share an unprotected hotspot | Usually |
| `MACC-PRD-4001` | Invalid profile/routing value | Yes |
| `MACC-PRD-5001` | Required design source is absent | Yes |
| `MACC-PRD-5002` | Required design sources conflict | Yes |
| `MACC-PRD-5003` | Design-system consumer can write system paths | Yes |
| `MACC-PRD-6001` | Missing UI fidelity mode/contract | Yes |
| `MACC-PRD-6002` | Vague UI acceptance criterion | Warning |
| `MACC-PRD-6003` | Required UI evidence missing | Yes |
| `MACC-PRD-6004` | UI task fragmented below a coherent unit | Warning |
| `MACC-PRD-7001` | PRD scope contract is missing or invalid | Yes |
| `MACC-PRD-7002` | Task scope does not match the file-level PRD scope | Yes |

Fix the diagnosed cause; do not weaken an intended contract merely to clear a diagnostic.
