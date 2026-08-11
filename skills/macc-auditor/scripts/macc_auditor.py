#!/usr/bin/env python3
"""Deterministic helpers for MACC final compliance audits."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", ".venv", "vendor"}
SKIP_AUDIT_PATHS = {"skills/macc-auditor", ".codex/skills/macc-auditor"}
DECISIONS = {"approved", "changes_requested", "blocked"}
SEVERITIES = {"blocking", "major", "minor", "advisory"}
TRACE_RESULTS = {"passed", "failed", "partial", "unverified"}
DIAGNOSTICS = {
    "MACC-AUDIT-1001": ("Invalid JSON", "Repair JSON syntax.", True),
    "MACC-AUDIT-1002": ("Audit report shape mismatch", "Use the audit-report schema/template.", True),
    "MACC-AUDIT-2001": ("Invalid decision", "Use approved, changes_requested, or blocked.", True),
    "MACC-AUDIT-2002": ("Approved report contains blocking or major findings", "Use changes_requested until blocking/major findings are resolved.", True),
    "MACC-AUDIT-3001": ("Finding is missing required evidence", "Add concrete evidence or move the item to unverified_items.", True),
    "MACC-AUDIT-3002": ("Finding is missing suggested fix", "Add the smallest actionable correction or follow-up.", True),
    "MACC-AUDIT-4001": ("Traceability row is incomplete", "Map each requirement to source, expected result, evidence, and result.", True),
}


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def diagnostic(code: str, detail: str | None = None) -> dict[str, Any]:
    message, correction, blocking = DIAGNOSTICS[code]
    item = {"code": code, "message": message, "blocking": blocking, "recommended_correction": correction}
    if detail:
        item["detail"] = detail
    return item


def files(root: Path) -> Iterable[Path]:
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            yield Path(current) / name


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def is_audit_helper_path(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in SKIP_AUDIT_PATHS)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_json_or_none(path: Path | None) -> Any:
    if not path or not path.exists():
        return None
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError):
        return None


def run_git(root: Path, args: list[str]) -> list[str]:
    try:
        result = subprocess.run(["git", *args], cwd=root, check=False, text=True, capture_output=True)
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def grep_suspicious(root: Path) -> list[dict[str, str]]:
    pattern = re.compile(r"\b(TODO|FIXME|HACK|TEMP|temporary|workaround|skip|flaky|hardcoded)\b", re.I)
    hits: list[dict[str, str]] = []
    for path in files(root):
        relative = rel(root, path)
        if is_audit_helper_path(relative):
            continue
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".kt", ".css", ".scss", ".md", ".json", ".yaml", ".yml"}:
            continue
        try:
            for number, line in enumerate(read_text(path).splitlines(), start=1):
                if pattern.search(line):
                    hits.append({"path": relative, "line": str(number), "text": line.strip()[:240]})
                    if len(hits) >= 200:
                        return hits
        except OSError:
            continue
    return hits


def classify_files(paths: list[str]) -> dict[str, list[str]]:
    buckets = {
        "implementation": [],
        "tests": [],
        "docs": [],
        "ui": [],
        "design_system": [],
        "macc": [],
        "architecture": [],
    }
    for path in paths:
        lower = path.lower()
        if re.search(r"(test|spec)\.[^.]+$", lower) or "/test" in lower or "/__tests__/" in lower:
            buckets["tests"].append(path)
        elif lower.endswith((".md", ".mdx", ".rst")) or "/docs/" in lower:
            buckets["docs"].append(path)
        elif lower.endswith((".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss", ".html")):
            buckets["ui"].append(path)
        else:
            buckets["implementation"].append(path)
        if "design-system" in lower or "tokens" in lower or "theme" in lower:
            buckets["design_system"].append(path)
        if lower.startswith(".macc/") or "worktree.prd.json" in lower or lower.endswith("prd.json"):
            buckets["macc"].append(path)
        if "adr" in lower or "architecture" in lower or "decision" in lower:
            buckets["architecture"].append(path)
    return buckets


def prd_summary(root: Path, prd: str | None) -> dict[str, Any]:
    if not prd:
        return {"path": None, "present": False}
    path = root / prd
    data = load_json_or_none(path)
    if not isinstance(data, dict):
        return {"path": prd, "present": path.exists(), "valid_json": False}
    scope = data.get("prd_scope") if isinstance(data.get("prd_scope"), dict) else data.get("lot") if isinstance(data.get("lot"), dict) else {}
    tasks = data.get("tasks", [])
    criteria = []
    for task in tasks if isinstance(tasks, list) else []:
        if isinstance(task, dict):
            for item in task.get("acceptance_criteria", []) if isinstance(task.get("acceptance_criteria"), list) else []:
                criteria.append({"task_id": task.get("id"), "criterion": item})
    return {
        "path": prd,
        "present": True,
        "valid_json": True,
        "scope": {
            "kind": scope.get("kind"),
            "id": scope.get("id") or scope.get("feature_id") or scope.get("foundation_id"),
            "name": scope.get("name") or scope.get("title"),
        },
        "task_count": len(tasks) if isinstance(tasks, list) else None,
        "acceptance_criteria": criteria,
    }


def inspect(root: Path, prd: str | None, base: str | None) -> dict[str, Any]:
    changed = run_git(root, ["diff", "--name-only", f"{base}...HEAD"] if base else ["diff", "--name-only"])
    staged = run_git(root, ["diff", "--cached", "--name-only"])
    status = run_git(root, ["status", "--short"])
    paths = sorted(set(changed + staged + [line[3:] for line in status if len(line) > 3]))
    operational = [p for p in ("worktree.prd.json", ".macc/tool.json", ".macc/worktree.json", ".macc/log") if (root / p).exists()]
    result = {
        "root": str(root),
        "prd": prd_summary(root, prd),
        "git": {"status": status, "changed_paths": paths, "buckets": classify_files(paths)},
        "operational_paths": operational,
        "candidate_evidence": {
            "tests": [rel(root, p) for p in files(root) if re.search(r"(test|spec)\.[^.]+$", p.name, re.I)][:200],
            "docs": [rel(root, p) for p in files(root) if p.suffix.lower() in {".md", ".mdx", ".rst"}][:200],
            "screenshots": [rel(root, p) for p in files(root) if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and any(token in rel(root, p).lower() for token in ("screenshot", "evidence", "review", "audit"))][:200],
            "architecture": [rel(root, p) for p in files(root) if any(token in rel(root, p).lower() for token in ("adr", "architecture", "decision"))][:100],
        },
        "suspicious_debt_markers": grep_suspicious(root),
        "warnings": [],
    }
    if not result["prd"]["present"]:
        result["warnings"].append("PRD/spec file was not found or not provided; compliance audit may need another source of requirements.")
    if not paths:
        result["warnings"].append("No changed files detected from git; inspect the delivered artifact or specify a base revision if needed.")
    return result


def skeleton(root: Path, prd: str | None) -> dict[str, Any]:
    info = inspect(root, prd, None)
    scope = info["prd"].get("scope") if isinstance(info.get("prd"), dict) else None
    if not isinstance(scope, dict) or not scope.get("id"):
        scope = {"kind": "unknown", "id": "unknown", "name": "Unknown audit scope"}
    traceability = []
    for index, item in enumerate(info["prd"].get("acceptance_criteria", []), start=1) if isinstance(info.get("prd"), dict) else []:
        traceability.append({
            "id": f"AC-{index:03d}",
            "source": f"{prd}:{item.get('task_id')}",
            "requirement": str(item.get("criterion")),
            "expected": str(item.get("criterion")),
            "implementation_evidence": [],
            "verification_evidence": [],
            "result": "unverified",
        })
    return {
        "decision": "blocked" if traceability else "blocked",
        "scope": scope,
        "summary": "Audit skeleton generated; fill evidence before final decision.",
        "traceability": traceability,
        "findings": [],
        "evidence_reviewed": [prd] if prd else [],
        "unverified_items": [row["id"] for row in traceability],
        "recommended_next_steps": ["Map each requirement to implementation and verification evidence, then rerun validate."],
    }


def markdown_report(root: Path, prd: str | None) -> str:
    report = skeleton(root, prd)
    scope = report["scope"]
    rows = []
    for row in report["traceability"]:
        rows.append(
            "| {id} | {source} | {requirement} | {expected} | {implementation} | {verification} | {result} |".format(
                id=escape_md(str(row["id"])),
                source=escape_md(str(row["source"])),
                requirement=escape_md(str(row["requirement"])),
                expected=escape_md(str(row["expected"])),
                implementation=escape_md(", ".join(row["implementation_evidence"]) or ""),
                verification=escape_md(", ".join(row["verification_evidence"]) or ""),
                result=escape_md(str(row["result"])),
            )
        )
    traceability = "\n".join(rows) if rows else "| AC-001 |  |  |  |  |  | unverified |"
    return f"""# Implementation Audit

Decision: `{report["decision"]}`

Scope:

- Kind: {scope.get("kind", "unknown")}
- ID: {scope.get("id", "unknown")}
- Name: {scope.get("name", "Unknown audit scope")}

Auditor independence:

- Fixes implemented by auditor: `none`
- Rule: Do not implement fixes. Audit, collect evidence, classify findings, and produce the canonical report only.

## Inputs reviewed

| Input group | Evidence reviewed | Status |
|---|---|---|
| Original requirements/specifications |  | missing |
| Original PRD | {escape_md(prd or "")} | {"present" if prd else "missing"} |
| Final integrated implementation |  | missing |
| Tests/results |  | missing |
| Relevant architecture/design constraints |  | missing |

## Summary

Audit skeleton generated; fill evidence before final decision.

## Traceability matrix

| ID | Source | Requirement / criterion | Expected | Implementation evidence | Verification evidence | Result |
|---|---|---|---|---|---|---|
{traceability}

## Findings

### Blocking

None recorded.

### Major

None recorded.

### Minor

None recorded.

### Advisory

None recorded.

## Unverified items

{format_unverified(report["unverified_items"])}

## Regression and integration risk

- Not assessed yet.

## Recommended next steps

- Map each requirement to implementation and verification evidence.
- Classify findings without implementing fixes.
- Rerun the audit after the next performer/fix pass.
"""


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def format_unverified(items: list[str]) -> str:
    if not items:
        return "- None recorded."
    return "\n".join(f"- {escape_md(str(item))}" for item in items)


def validate_report(path: Path) -> dict[str, Any]:
    diagnostics: list[dict[str, Any]] = []
    try:
        data = load_json(path)
    except FileNotFoundError:
        return output([diagnostic("MACC-AUDIT-1002", f"Report not found: {path}")])
    except json.JSONDecodeError as exc:
        return output([diagnostic("MACC-AUDIT-1001", f"line {exc.lineno}, column {exc.colno}: {exc.msg}")])
    required = ["decision", "scope", "summary", "traceability", "findings", "evidence_reviewed", "unverified_items", "recommended_next_steps"]
    if not isinstance(data, dict) or any(key not in data for key in required):
        return output([diagnostic("MACC-AUDIT-1002", "Missing required top-level report fields.")])
    if data.get("decision") not in DECISIONS:
        diagnostics.append(diagnostic("MACC-AUDIT-2001"))
    findings = data.get("findings")
    if not isinstance(findings, list):
        diagnostics.append(diagnostic("MACC-AUDIT-1002", "findings must be an array."))
        findings = []
    has_blocking_or_major = False
    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            diagnostics.append(diagnostic("MACC-AUDIT-1002", f"finding {index} is not an object."))
            continue
        severity = finding.get("severity")
        if severity in {"blocking", "major"}:
            has_blocking_or_major = True
        required_finding = ["id", "severity", "dimension", "requirement", "location", "expected", "observed", "evidence", "impact", "suggested_fix"]
        missing = [key for key in required_finding if key not in finding or finding.get(key) in ("", [], None)]
        if missing:
            code = "MACC-AUDIT-3001" if "evidence" in missing else "MACC-AUDIT-3002" if "suggested_fix" in missing else "MACC-AUDIT-1002"
            diagnostics.append(diagnostic(code, f"finding {finding.get('id', index)} missing: {', '.join(missing)}"))
        if severity not in SEVERITIES:
            diagnostics.append(diagnostic("MACC-AUDIT-1002", f"finding {finding.get('id', index)} has invalid severity."))
    if data.get("decision") == "approved" and has_blocking_or_major:
        diagnostics.append(diagnostic("MACC-AUDIT-2002"))
    traceability = data.get("traceability")
    if not isinstance(traceability, list):
        diagnostics.append(diagnostic("MACC-AUDIT-1002", "traceability must be an array."))
        traceability = []
    for index, row in enumerate(traceability, start=1):
        required_row = ["id", "source", "requirement", "expected", "implementation_evidence", "verification_evidence", "result"]
        if not isinstance(row, dict) or any(key not in row for key in required_row) or row.get("result") not in TRACE_RESULTS:
            diagnostics.append(diagnostic("MACC-AUDIT-4001", f"traceability row {index} is incomplete or invalid."))
    return output(diagnostics)


def output(diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "valid": not any(item["blocking"] for item in diagnostics),
        "diagnostics": diagnostics,
        "summary": {
            "blocking": sum(1 for item in diagnostics if item["blocking"]),
            "warnings": sum(1 for item in diagnostics if not item["blocking"]),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    child = sub.add_parser("inspect")
    child.add_argument("--root", default=".")
    child.add_argument("--prd")
    child.add_argument("--base")
    child = sub.add_parser("skeleton")
    child.add_argument("--root", default=".")
    child.add_argument("--prd")
    child.add_argument("--output")
    child = sub.add_parser("markdown")
    child.add_argument("--root", default=".")
    child.add_argument("--prd")
    child.add_argument("--output", default=".macc/reports/implementation-audit.md")
    child = sub.add_parser("validate")
    child.add_argument("--file", required=True)
    child = sub.add_parser("explain")
    child.add_argument("--diagnostic", required=True)
    args = parser.parse_args()
    if args.command == "explain":
        if args.diagnostic not in DIAGNOSTICS:
            emit({"code": args.diagnostic, "message": "Unknown diagnostic", "blocking": True})
            return 2
        emit(diagnostic(args.diagnostic))
        return 0
    if args.command == "inspect":
        emit(inspect(Path(args.root).resolve(), args.prd, args.base))
        return 0
    if args.command == "skeleton":
        report = skeleton(Path(args.root).resolve(), args.prd)
        if args.output:
            output_path = Path(args.root).resolve() / args.output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            emit({"output": str(output_path), "report": report})
        else:
            emit(report)
        return 0
    if args.command == "markdown":
        root = Path(args.root).resolve()
        body = markdown_report(root, args.prd)
        output_path = root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(body, encoding="utf-8")
        emit({"output": str(output_path), "canonical_report": ".macc/reports/implementation-audit.md"})
        return 0
    result = validate_report(Path(args.file))
    emit(result)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
