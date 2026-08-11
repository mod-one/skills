# Evidence guide

Build a requirement-to-evidence trace. Each row should identify:

- requirement source: user request, PRD task, acceptance criterion, design source, ADR, or existing behavior;
- requirement text;
- expected outcome;
- implementation evidence: file, function, route, component, migration, config, screenshot, or log;
- verification evidence: test, command output, screenshot, manual run, review artifact, or explicit absence;
- audit result: `passed`, `failed`, `partial`, or `unverified`.

Evidence standards:

- Prefer concrete artifacts over claims in task summaries.
- Use exact paths, task IDs, criterion IDs, command names, and screenshot/log paths where available.
- Treat missing evidence as `unverified`, not passed.
- Label inference explicitly, for example: `inference: route behavior appears covered by controller test`.
- Do not require irrelevant evidence for out-of-scope work.

Useful local sources:

- `prd.json`, `worktree.prd.json`, PRD examples, issue text, acceptance criteria;
- `.macc/tool.json`, `.macc/worktree.json`, `.macc/log/`;
- phase result files, UX review result files, screenshots, test output;
- `git diff`, `git status`, touched files, test files, docs, ADRs;
- design references, HTML references, design-system directories, component stories.

Required input groups for the canonical audit:

- Original requirements/specifications.
- Original PRD.
- Final integrated implementation.
- Tests/results.
- Relevant architecture/design constraints.

Independence rule:

- Do not edit files to create missing evidence.
- Do not add tests to make a requirement verifiable.
- Do not update the PRD/spec/design docs to align them with the implementation.
- Do not repair defects discovered during the audit.
- Record missing or weak evidence in `.macc/reports/implementation-audit.md`.
