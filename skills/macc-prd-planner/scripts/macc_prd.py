#!/usr/bin/env python3
"""Portable deterministic inspection and validation for MACC PRD planning.

This compatibility CLI intentionally uses only the Python standard library. Its JSON
contracts and diagnostic namespace are suitable for replacement by the MACC PRD core.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", ".venv", "vendor"}
PROFILES = {"general", "frontend-logic", "ui-fidelity", "ui-exploration", "design-system-change", "ux-review"}
UI_PROFILES = {"ui-fidelity", "ui-exploration", "design-system-change", "ux-review"}
ROUTING = {
    "execution_mode": {"micro", "standard", "structural"},
    "reasoning_depth": {"light", "standard", "deep"},
    "context_scope": {"local", "module", "cross-cutting"},
    "risk_level": {"low", "medium", "high"},
    "validation_profile": {"light", "standard", "heavy"},
}
DIAGNOSTICS = {
    "MACC-PRD-1001": ("Invalid JSON", "Repair the JSON syntax before planning can continue.", True),
    "MACC-PRD-1002": ("PRD schema mismatch", "Supply a JSON object with a task array and repository-compatible fields.", True),
    "MACC-PRD-2001": ("Duplicate task ID", "Give every task a unique, stable ID.", True),
    "MACC-PRD-2002": ("Unknown dependency", "Reference an existing task ID or remove the dependency.", True),
    "MACC-PRD-2003": ("Dependency cycle", "Break the cycle with a contracts-first or sequential dependency design.", True),
    "MACC-PRD-2004": ("Completed task identity removed", "Keep completed task IDs when validating an update, or explicitly reconcile the historical PRD.", True),
    "MACC-PRD-3001": ("Parallel tasks share an unprotected hotspot", "Add a dependency, share an exclusive resource, or split the scopes.", True),
    "MACC-PRD-4001": ("Invalid routing or planning profile", "Use a supported profile and routing-hint value.", True),
    "MACC-PRD-4002": ("Documentation task absent", "Add a dedicated documentation task or record a lot-level justification.", True),
    "MACC-PRD-4003": ("Verification task absent", "Add a dedicated tests/verification task or record a lot-level justification.", True),
    "MACC-PRD-5001": ("Required design source does not exist", "Correct the path or resolve the missing authoritative source.", True),
    "MACC-PRD-5002": ("Required design sources conflict", "Add a contract-resolution task and block dependent implementation.", True),
    "MACC-PRD-5003": ("Design-system consumer can modify the design system", "Protect the system and remove it from the consumer write scope.", True),
    "MACC-PRD-6001": ("Missing UI fidelity contract", "Set fidelity mode, design-system role, and required source contract.", True),
    "MACC-PRD-6002": ("Vague UI acceptance criterion", "Use source-specific, observable acceptance criteria.", False),
    "MACC-PRD-6003": ("Required UI evidence missing", "Add proportional screenshot, interaction, accessibility, token, or protected-path evidence.", True),
    "MACC-PRD-6004": ("UI task fragmented below a coherent unit", "Combine layers of the same visual unit or establish a stable shared contract first.", False),
    "MACC-PRD-7001": ("PRD scope contract missing or invalid", "Declare exactly one file-level prd_scope with kind feature or shared-foundation, stable id, name, and definition.", True),
    "MACC-PRD-7002": ("Task scope does not match PRD scope", "Move unrelated feature work to another PRD, or change the task scope_ref/feature_id to the file-level prd_scope id.", True),
    "MACC-PRD-8001": ("Invalid human approval gate", "Set gate.kind human_approval with subject_task (also listed in dependencies), at least one required_approvers role with count >= 1, quorum all|any|1..N, and bind_to commit_sha.", True),
    "MACC-PRD-8002": ("Human approval gate carries executable work", "Remove change_scope.allowed_paths and implementation steps from the gate; put the work in the subject task. A gate is never executed by a performer.", True),
    "MACC-PRD-8003": ("Approver role not traceable to the governance source", "Use the role names the cited governance source defines, or cite the source that defines them. Never invent approver roles.", True),
    "MACC-PRD-8004": ("Human approval gate lacks a governance source", "Cite the specification governance source that defines the approver roles in gate.governance_ref, or escalate: roles must be derived, not assumed.", True),
    "MACC-PRD-8005": ("Human approval gate lacks a valid trigger", "Set gate.approval_trigger to one of the allowed triggers, or remove the gate: approval is added only when a trigger applies.", True),
    "MACC-PRD-8006": ("Approval-sensitive task is not behind a human gate", "If this task implements a decision that needs human approval, add a human_approval gate on the decision and make this task depend on it; otherwise record why none is needed in notes.", False),
}

# A human approval gate is justified only by one of these triggers.
APPROVAL_TRIGGERS = {
    "normative-change",
    "adr",
    "open-product-decision",
    "sensitive-architecture",
    "sensitive-data-model",
    "security",
    "identity",
    "payment",
    "privacy",
    "irreversible-migration",
    "production-activation",
    "gate-crossing",
}
GOVERNANCE_NAME = re.compile(r"(codeowners|governance|gouvernance|raci|roles?[-_]?permissions|decisions?|adr|approv|ownership|responsab)", re.I)
ROLE_TOKEN = re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b")
ROLE_HINT = re.compile(r"(OWNER|LEAD|ARCHITECT|OFFICER|MANAGER|REVIEWER|APPROVER|ADMIN|DPO|CISO|CTO|SPONSOR|STEWARD|RESPONSIBLE)")


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def diagnostic(code: str, task_id: str | None = None, detail: str | None = None) -> dict[str, Any]:
    title, correction, blocking = DIAGNOSTICS[code]
    item = {"code": code, "message": title, "blocking": blocking, "recommended_correction": correction}
    if task_id:
        item["task_id"] = task_id
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


def find_named(root: Path, name: str) -> Path | None:
    direct = root / name
    if direct.exists():
        return direct
    for path in files(root):
        if path.name == name:
            return path
    return None


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


def detect_technology(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"frontend": None, "styling": None, "component_library": None, "languages": []}
    package = load_json_or_none(root / "package.json") or {}
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    if "react" in deps:
        result["frontend"] = "react-vite" if "vite" in deps else "react"
    elif "vue" in deps:
        result["frontend"] = "vue"
    elif "@angular/core" in deps:
        result["frontend"] = "angular"
    if "tailwindcss" in deps:
        result["styling"] = "tailwind"
    elif any((root / x).exists() for x in ("src/styles", "src/styles.css", "src/app.css")):
        result["styling"] = "project-css"
    for library in ("@radix-ui/react-dialog", "@mui/material", "antd", "@chakra-ui/react"):
        if library in deps:
            result["component_library"] = library
            break
    suffixes = {path.suffix.lower() for path in files(root)}
    result["languages"] = sorted({
        {".rs": "rust", ".py": "python", ".ts": "typescript", ".tsx": "typescript-react", ".js": "javascript", ".go": "go", ".java": "java", ".kt": "kotlin"}.get(s)
        for s in suffixes
    } - {None})
    return result


def possible_design_sources(root: Path) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for path in files(root):
        lower = rel(root, path).lower()
        if path.suffix.lower() in {".html", ".htm"} and any(token in lower for token in ("design", "reference", "prototype", "mockup")):
            sources.append({"path": rel(root, path), "kind": "html-reference", "authority": "supporting", "exists": True})
    for candidate in ("design-system", "design", "src/design-system", "web/src/design-system", "ui"):
        path = root / candidate
        if path.is_dir():
            sources.append({"path": candidate, "kind": "design-system", "authority": "supporting", "exists": True})
    return sources


def hotspot_paths(root: Path) -> list[str]:
    hotspots: list[str] = []
    for path in files(root):
        try:
            if path.stat().st_size > 30_000 or sum(1 for _ in path.open(encoding="utf-8", errors="ignore")) > 500:
                hotspots.append(rel(root, path))
        except OSError:
            continue
    return hotspots[:100]


APPROVAL_HEADING = re.compile(r"^#{1,6}\s.*(approb|approv|raci|decision rights|droits de d[ée]cision|who decides|qui d[ée]cide|signataires?)", re.I)


def fold(value: str) -> str:
    """Lower-case and strip accents so 'Responsable sécurité' matches
    RESPONSABLE_SECURITE."""
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).lower()


def approval_rules(content: str) -> list[dict[str, str]]:
    """Rows of approval matrices: markdown tables under a heading about
    approval, RACI, or decision rights. Each row maps a domain to the approvers
    the governance source requires for it."""
    rules: list[dict[str, str]] = []
    in_section = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            in_section = bool(APPROVAL_HEADING.match(stripped))
            continue
        if not in_section or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            # Separator row: the row just before it was the table header.
            if rules:
                rules.pop()
            continue
        if len(cells) < 2:
            continue
        rules.append({"domain": cells[0], "approvers": cells[1]})
    return rules[:40]


def governance_sources(root: Path) -> list[dict[str, Any]]:
    """Files that define who decides: CODEOWNERS, governance/RACI docs, decision
    logs and ADR records. For each: role-like UPPER_SNAKE tokens or CODEOWNERS
    owners (`role_candidates`) and approval-matrix rows (`approval_rules`).
    The planner derives approver roles from these, never from assumptions.

    Application RBAC roles (end-user permissions) may appear here too; they are
    not approval roles unless the source says they approve decisions."""
    found: list[dict[str, Any]] = []
    for path in files(root):
        name = path.name
        relative = rel(root, path)
        # MACC's own state, logs, and worktree copies are not governance.
        if relative.split("/", 1)[0] == ".macc":
            continue
        is_codeowners = name == "CODEOWNERS"
        if not is_codeowners and not (path.suffix.lower() in {".md", ".mdx", ".txt", ".yaml", ".yml", ".json"} and GOVERNANCE_NAME.search(relative)):
            continue
        try:
            content = text(path)
        except OSError:
            continue
        if is_codeowners:
            owners = sorted({token for token in re.findall(r"@[\w./-]+", content)})
            found.append({"path": relative, "kind": "codeowners", "role_candidates": owners[:50]})
            continue
        roles = sorted({token for token in ROLE_TOKEN.findall(content) if ROLE_HINT.search(token)})
        rules = approval_rules(content)
        kind = "approval-matrix" if rules else ("adr" if re.search(r"(^|/)(adr|decisions?)(/|[-_.])", relative, re.I) else "governance")
        if roles or rules or kind == "governance":
            entry: dict[str, Any] = {"path": relative, "kind": kind, "role_candidates": roles[:50]}
            if rules:
                entry["approval_rules"] = rules
            found.append(entry)
    order = {"approval-matrix": 0, "codeowners": 1, "governance": 2, "adr": 3}
    return sorted(found, key=lambda item: (order.get(item["kind"], 9), item["path"]))[:60]


def role_is_traceable(role: str, governance_text: str) -> bool:
    """A role is traceable when the governance source names it, verbatim or in
    its prose form, ignoring case and accents
    (PRODUCT_OWNER ~ "Product Owner"; RESPONSABLE_SECURITE ~ "Responsable sécurité")."""
    folded = fold(governance_text)
    role_folded = fold(role)
    if role.startswith("@"):
        return role_folded in folded
    candidates = {role_folded, role_folded.replace("_", " "), role_folded.replace("_", "-")}
    return any(candidate in folded for candidate in candidates)


def inspect(root: Path) -> dict[str, Any]:
    schema = find_named(root, "prd.json.example")
    existing = find_named(root, "prd.json")
    docs = [rel(root, p) for p in files(root) if p.name.lower().startswith(("readme", "changelog", "contributing")) or "docs" in p.parts][:100]
    tests = [rel(root, p) for p in files(root) if re.search(r"(test|spec)\.[^.]+$", p.name, re.I)][:100]
    operational = [p for p in ("worktree.prd.json", ".macc/tool.json", ".macc/worktree.json", ".macc/log") if (root / p).exists()]
    return {
        "schema_version": "1",
        "repository": {"root": str(root), "prd_schema": rel(root, schema) if schema else None, "existing_prd": rel(root, existing) if existing else None},
        "technology": detect_technology(root),
        "design_sources": possible_design_sources(root),
        "design_inventory": {"tokens": [], "components": [], "assets": [], "fonts": [], "icons": [], "breakpoints": [], "screen_regions": []},
        "hot_zones": hotspot_paths(root),
        "documentation_paths": docs,
        "test_paths": tests,
        "operational_paths": operational,
        "governance_sources": governance_sources(root),
        "protected_paths": [],
        "warnings": [] if schema else ["prd.json.example was not found; use the repository schema when available."],
        "blocking_issues": [],
    }


def build_context(root: Path) -> dict[str, Any]:
    context = inspect(root)
    inventory = context["design_inventory"]
    for source in context["design_sources"]:
        if source["kind"] == "design-system":
            result = inspect_design(root, source["path"])
            for kind, names in result.get("tokens", {}).items():
                inventory["tokens"].extend({"kind": kind, "name": name, "source": source["path"]} for name in names)
            inventory["components"].extend(result.get("components", []))
            inventory["assets"].extend(result.get("assets", []))
            inventory["fonts"].extend(result.get("fonts", []))
            inventory["icons"].extend(result.get("icons", []))
            inventory["breakpoints"].extend(result.get("breakpoints", []))
        elif source["kind"] == "html-reference":
            result = inspect_html(root, source["path"])
            inventory["screen_regions"].extend({"name": region, "source": source["path"]} for region in result.get("regions", []))
    context["reference_coverage"] = {}
    return context


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def inspect_design(root: Path, source: str) -> dict[str, Any]:
    path = (root / source).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return {"path": source, "warnings": ["Path is outside the repository root."]}
    if not path.is_dir():
        return {"path": source, "warnings": ["Design-system directory does not exist."]}
    entries = list(files(path))
    names = [p.name.lower() for p in entries]
    tokens: dict[str, list[str]] = defaultdict(list)
    components: list[dict[str, Any]] = []
    assets: list[str] = []
    fonts: list[str] = []
    icons: list[str] = []
    breakpoints: list[str] = []
    for item in entries:
        content = text(item) if item.suffix.lower() in {".css", ".scss", ".sass", ".ts", ".tsx", ".js", ".json"} else ""
        for variable in re.findall(r"--([A-Za-z0-9_-]+)", content):
            bucket = "colors" if any(x in variable.lower() for x in ("color", "surface", "text", "status")) else "spacing" if "space" in variable.lower() else "other"
            if variable not in tokens[bucket]:
                tokens[bucket].append(variable)
        breakpoints.extend(x for x in re.findall(r"(?:min|max)-width\s*:\s*[^ )]+", content) if x not in breakpoints)
        if item.suffix.lower() in {".tsx", ".jsx", ".vue", ".svelte"}:
            components.append({"name": item.stem, "path": rel(root, item), "variants": sorted(set(re.findall(r"variant[s]?\s*[:=]\s*[\"']?([A-Za-z0-9_-]+)", content)))})
        if item.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".webp"}:
            assets.append(rel(root, item))
        if item.suffix.lower() in {".woff", ".woff2", ".ttf", ".otf"}:
            fonts.append(rel(root, item))
        if "icon" in item.name.lower():
            icons.append(rel(root, item))
    return {
        "path": source,
        "role_recommendation": "consumer",
        "entry_points": [rel(root, p) for p in entries if p.name.lower() in {"index.ts", "index.tsx", "index.js", "readme.md"}],
        "tokens": dict(tokens), "components": components, "assets": assets, "fonts": fonts, "icons": icons,
        "breakpoints": breakpoints, "stories": [rel(root, p) for p in entries if ".stories." in p.name],
        "tests": [rel(root, p) for p in entries if re.search(r"(test|spec)\.[^.]+$", p.name, re.I)],
        "warnings": [] if entries else ["Design-system directory is empty."],
    }


def inspect_html(root: Path, source: str) -> dict[str, Any]:
    path = root / source
    if not path.is_file():
        return {"path": source, "warnings": ["HTML reference does not exist."]}
    content = text(path)
    classes = re.findall(r"\bclass=[\"']([^\"']+)[\"']", content, re.I)
    regions = []
    for tag, attrs in re.findall(r"<(header|main|aside|nav|section|footer|article|div)\b([^>]*)", content, re.I):
        marker = re.search(r"(?:id|data-region)=[\"']([^\"']+)", attrs, re.I)
        if marker:
            regions.append(marker.group(1))
        elif tag != "div":
            regions.append(tag.lower())
    exact_copy = [re.sub(r"\s+", " ", x).strip() for x in re.findall(r">\s*([^<>]{3,})\s*<", content) if x.strip()]
    return {
        "path": source,
        "regions": sorted(set(regions)),
        "classes": sorted({c for group in classes for c in group.split()}),
        "css_variables": sorted(set(re.findall(r"--[A-Za-z0-9_-]+", content))),
        "font_families": sorted(set(re.findall(r"font-family\s*:\s*([^;}{]+)", content, re.I))),
        "assets": sorted(set(re.findall(r"(?:src|href)=[\"']([^\"'#?]+)", content, re.I))),
        "interactive_elements": sorted(set(re.findall(r"<(button|input|select|textarea|a)\b", content, re.I))),
        "media_queries": sorted(set(re.findall(r"@media\s*\(([^)]+)\)", content, re.I))),
        "exact_copy": exact_copy,
        "external_dependencies": sorted(set(re.findall(r"https?://[^\"'\s>]+", content))),
        "warnings": [],
    }


def path_exists(root: Path, pattern: str) -> bool:
    candidate = pattern.rstrip("/")
    candidate = re.sub(r"/\*\*.*$", "", candidate).rstrip("/")
    return bool(candidate) and (root / candidate).exists()


def overlaps(first: str, second: str) -> bool:
    def base(value: str) -> str:
        return re.sub(r"/\*\*.*$", "", value).rstrip("/")
    a, b = base(first), base(second)
    return bool(a and b and (a == b or a.startswith(b + "/") or b.startswith(a + "/")))


def is_dependent(start: str, target: str, graph: dict[str, list[str]]) -> bool:
    stack, visited = list(graph.get(start, [])), set()
    while stack:
        current = stack.pop()
        if current == target:
            return True
        if current not in visited:
            visited.add(current)
            stack.extend(graph.get(current, []))
    return False


def prd_scope(data: dict[str, Any]) -> dict[str, Any] | None:
    scope = data.get("prd_scope")
    if not isinstance(scope, dict):
        scope = data.get("lot") if isinstance(data.get("lot"), dict) else None
    if not isinstance(scope, dict):
        return None
    kind = scope.get("kind") or scope.get("scope_kind") or scope.get("type")
    identifier = scope.get("id") or scope.get("scope_id") or scope.get("feature_id") or scope.get("foundation_id")
    name = scope.get("name") or scope.get("title") or scope.get("feature_name") or scope.get("foundation_name")
    definition = scope.get("definition") or scope.get("scope") or scope.get("summary") or scope.get("objective")
    normalized = {"kind": kind, "id": identifier, "name": name, "definition": definition}
    if kind not in {"feature", "shared-foundation"}:
        return None
    if not all(isinstance(normalized[key], str) and normalized[key].strip() for key in ("id", "name", "definition")):
        return None
    return normalized


def task_scope_refs(task: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("scope_ref", "feature_id", "foundation_id"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
    for key in ("scope_refs", "feature_ids"):
        values = task.get(key)
        if isinstance(values, list):
            refs.extend(item.strip() for item in values if isinstance(item, str) and item.strip())
    return refs


def validate(root: Path, file_name: str, profile: str | None, previous_name: str | None) -> dict[str, Any]:
    path = root / file_name
    diagnostics: list[dict[str, Any]] = []
    try:
        data = load_json(path)
    except FileNotFoundError:
        diagnostics.append(diagnostic("MACC-PRD-1002", detail=f"PRD file not found: {file_name}"))
        return validation_output(diagnostics)
    except json.JSONDecodeError as exc:
        diagnostics.append(diagnostic("MACC-PRD-1001", detail=f"line {exc.lineno}, column {exc.colno}: {exc.msg}"))
        return validation_output(diagnostics)
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        diagnostics.append(diagnostic("MACC-PRD-1002", detail="Top-level object must contain a tasks array."))
        return validation_output(diagnostics)
    tasks = data["tasks"]
    scope = prd_scope(data)
    if scope is None:
        diagnostics.append(diagnostic("MACC-PRD-7001"))
    elif scope["kind"] == "feature":
        raw_scope = data.get("prd_scope") if isinstance(data.get("prd_scope"), dict) else data.get("lot", {})
        if isinstance(raw_scope, dict) and raw_scope.get("consumer_feature_ids"):
            diagnostics.append(diagnostic("MACC-PRD-7001", detail="consumer_feature_ids is only valid for shared-foundation PRDs."))
    ids: list[str] = []
    graph: dict[str, list[str]] = {}
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str) or not task["id"]:
            diagnostics.append(diagnostic("MACC-PRD-1002", detail="Every task requires a non-empty string id."))
            continue
        ids.append(task["id"])
        graph[task["id"]] = task.get("dependencies", []) if isinstance(task.get("dependencies", []), list) else []
    id_set = set(ids)
    for task_id in sorted({task_id for task_id in ids if ids.count(task_id) > 1}):
        diagnostics.append(diagnostic("MACC-PRD-2001", task_id))
    for task_id, dependencies in graph.items():
        for dependency in dependencies:
            if dependency not in id_set:
                diagnostics.append(diagnostic("MACC-PRD-2002", task_id, f"Unknown dependency: {dependency}"))
        if is_dependent(task_id, task_id, graph):
            diagnostics.append(diagnostic("MACC-PRD-2003", task_id))
    priority_mapping = data.get("priority_mapping", {})
    for task in tasks:
        task_id = task.get("id") if isinstance(task, dict) else None
        if not isinstance(task, dict):
            continue
        if scope is not None:
            for ref in task_scope_refs(task):
                if ref != scope["id"]:
                    diagnostics.append(diagnostic("MACC-PRD-7002", task_id, f"Task scope reference {ref!r} does not match PRD scope {scope['id']!r}."))
        selected_profile = task.get("planning_profile", "general")
        if selected_profile not in PROFILES:
            diagnostics.append(diagnostic("MACC-PRD-4001", task_id, f"Unsupported planning_profile: {selected_profile}"))
        hints = task.get("routing_hints")
        if hints is not None:
            if not isinstance(hints, dict) or any(hints.get(key) not in values for key, values in ROUTING.items()):
                diagnostics.append(diagnostic("MACC-PRD-4001", task_id, "routing_hints must use supported values for all five fields."))
        if "priority" in task and priority_mapping and str(task["priority"]) not in {str(k) for k in priority_mapping}:
            diagnostics.append(diagnostic("MACC-PRD-1002", task_id, "Priority is absent from priority_mapping."))
        # --profile ui-fidelity enables the additional UI validation pass; it
        # does not turn documentation and verification tasks in the same lot
        # into UI tasks.
        if selected_profile in UI_PROFILES:
            validate_ui_task(root, task, diagnostics)
    validate_collisions(tasks, graph, diagnostics)
    validate_lot_responsibilities(data, tasks, diagnostics)
    validate_approval_gates(root, tasks, graph, diagnostics)
    if previous_name:
        previous = load_json_or_none(root / previous_name)
        if isinstance(previous, dict):
            old_done = {t.get("id") for t in previous.get("tasks", []) if isinstance(t, dict) and str(t.get("status", "")).lower() in {"done", "completed"}}
            for task_id in sorted(old_done - id_set):
                diagnostics.append(diagnostic("MACC-PRD-2004", task_id))
    return validation_output(diagnostics)


def validate_ui_task(root: Path, task: dict[str, Any], diagnostics: list[dict[str, Any]]) -> None:
    task_id = task.get("id")
    contract = task.get("design_contract")
    if not isinstance(contract, dict) or contract.get("fidelity_mode") not in {"exact", "adaptive", "exploratory"} or contract.get("design_system_role") not in {"consumer", "extension", "migration", "none"} or not isinstance(contract.get("sources"), list):
        diagnostics.append(diagnostic("MACC-PRD-6001", task_id))
        return
    sources = contract["sources"]
    required_sources = [source for source in sources if isinstance(source, dict) and source.get("authority") == "required"]
    if task.get("planning_profile") in {"ui-fidelity", "ui-exploration"} and not required_sources:
        diagnostics.append(diagnostic("MACC-PRD-6001", task_id, "UI fidelity/exploration task requires at least one required source."))
    for source in required_sources:
        if not isinstance(source.get("path"), str) or source.get("type") is None or source.get("mutable") is not False:
            diagnostics.append(diagnostic("MACC-PRD-6001", task_id, "Every required source needs path, type, authority, and mutable: false."))
        elif not path_exists(root, source["path"]):
            diagnostics.append(diagnostic("MACC-PRD-5001", task_id, str(source.get("path"))))
    if contract.get("conflicts"):
        diagnostics.append(diagnostic("MACC-PRD-5002", task_id))
    scope = task.get("change_scope") if isinstance(task.get("change_scope"), dict) else {}
    readonly = scope.get("read_only_paths", []) if isinstance(scope.get("read_only_paths", []), list) else []
    allowed = scope.get("allowed_paths", []) if isinstance(scope.get("allowed_paths", []), list) else []
    if contract.get("design_system_role") == "consumer":
        for source in required_sources:
            if source.get("type") == "design-system":
                source_path = str(source.get("path", ""))
                if not any(overlaps(source_path, item) for item in readonly) or any(overlaps(source_path, item) for item in allowed):
                    diagnostics.append(diagnostic("MACC-PRD-5003", task_id, source_path))
    if task.get("planning_profile") == "ui-fidelity":
        if not scope or not isinstance(task.get("fidelity_contract"), dict) or not isinstance(task.get("adaptation_policy"), dict):
            diagnostics.append(diagnostic("MACC-PRD-6001", task_id, "UI fidelity requires change_scope, fidelity_contract, and adaptation_policy."))
        if not isinstance(task.get("ui_states"), list) or not task["ui_states"]:
            diagnostics.append(diagnostic("MACC-PRD-6001", task_id, "UI fidelity requires applicable ui_states."))
    evidence = task.get("evidence_requirements")
    if not isinstance(evidence, list) or not evidence:
        diagnostics.append(diagnostic("MACC-PRD-6003", task_id))
    elif any(isinstance(item, dict) and item.get("type") == "screenshot" and item.get("viewport") for item in evidence):
        if not isinstance(task.get("viewports"), list) or not task["viewports"]:
            diagnostics.append(diagnostic("MACC-PRD-6003", task_id, "Screenshot evidence references a viewport but viewports are undefined."))
    criteria = task.get("acceptance_criteria", [])
    vague = re.compile(r"\b(looks polished|feels intuitive|modern design|improves? the ux|matches the design)\b", re.I)
    if not isinstance(criteria, list) or not criteria:
        diagnostics.append(diagnostic("MACC-PRD-6002", task_id, "UI acceptance criteria are absent."))
    elif any(isinstance(item, str) and vague.search(item) for item in criteria):
        diagnostics.append(diagnostic("MACC-PRD-6002", task_id))


def validate_collisions(tasks: list[Any], graph: dict[str, list[str]], diagnostics: list[dict[str, Any]]) -> None:
    valid = [task for task in tasks if isinstance(task, dict) and isinstance(task.get("id"), str)]
    for index, first in enumerate(valid):
        first_allowed = first.get("change_scope", {}).get("allowed_paths", []) if isinstance(first.get("change_scope"), dict) else []
        for second in valid[index + 1:]:
            second_allowed = second.get("change_scope", {}).get("allowed_paths", []) if isinstance(second.get("change_scope"), dict) else []
            if not first_allowed or not second_allowed or is_dependent(first["id"], second["id"], graph) or is_dependent(second["id"], first["id"], graph):
                continue
            overlap = next((a for a in first_allowed for b in second_allowed if overlaps(str(a), str(b))), None)
            common_resource = set(first.get("exclusive_resources", [])) & set(second.get("exclusive_resources", []))
            if overlap and not common_resource:
                diagnostics.append(diagnostic("MACC-PRD-3001", first["id"], f"Overlaps {second['id']} at {overlap}."))


def validate_lot_responsibilities(data: dict[str, Any], tasks: list[Any], diagnostics: list[dict[str, Any]]) -> None:
    assumptions = data.get("lot", {}).get("assumptions", []) if isinstance(data.get("lot"), dict) else []
    assumption_text = " ".join(str(item).lower() for item in assumptions)
    text_values = [" ".join(str(task.get(key, "")) for key in ("title", "category", "description", "objective")) .lower() for task in tasks if isinstance(task, dict)]
    if not any(re.search(r"\b(doc|readme|changelog|documentation)\b", value) for value in text_values) and "documentation" not in assumption_text:
        diagnostics.append(diagnostic("MACC-PRD-4002"))
    if not any(re.search(r"\b(test|verification|validate|regression|qa)\b", value) for value in text_values) and not any(word in assumption_text for word in ("test", "verification")):
        diagnostics.append(diagnostic("MACC-PRD-4003"))


def is_human_gate(task: Any) -> bool:
    return isinstance(task, dict) and isinstance(task.get("gate"), dict) and task["gate"].get("kind") == "human_approval"


SENSITIVE_TEXT = re.compile(
    r"\b(adr|migration|migrate|production|go[- ]live|rollout|payment|billing|privacy|gdpr|rgpd|personal data|identity|mfa|authentication|authorization|encryption|secret|security)\b",
    re.I,
)


def validate_approval_gates(root: Path, tasks: list[Any], graph: dict[str, list[str]], diagnostics: list[dict[str, Any]]) -> None:
    gates = {task["id"] for task in tasks if is_human_gate(task) and isinstance(task.get("id"), str)}
    for task in tasks:
        if not is_human_gate(task):
            continue
        task_id = task.get("id")
        gate = task["gate"]
        deps = task.get("dependencies", []) if isinstance(task.get("dependencies"), list) else []
        problems = []
        subject = gate.get("subject_task")
        if not isinstance(subject, str) or not subject.strip():
            problems.append("gate.subject_task is required")
        elif subject not in deps:
            problems.append(f"gate.subject_task {subject!r} must also be listed in dependencies")
        approvers = gate.get("required_approvers")
        if not isinstance(approvers, list) or not approvers:
            problems.append("gate.required_approvers must name at least one role")
            approvers = []
        total = 0
        for approver in approvers:
            role = approver.get("role") if isinstance(approver, dict) else None
            count = approver.get("count", 1) if isinstance(approver, dict) else 0
            if not isinstance(role, str) or not role.strip():
                problems.append("a required approver has no role")
            if not isinstance(count, int) or count < 1:
                problems.append(f"required approver {role!r} needs count >= 1")
            else:
                total += count
        quorum = gate.get("quorum", "all")
        if not (quorum in ("all", "any") or (isinstance(quorum, int) and not isinstance(quorum, bool) and 1 <= quorum <= max(total, 1))):
            problems.append(f"gate.quorum {quorum!r} must be 'all', 'any' or 1..{max(total, 1)}")
        if gate.get("bind_to", "commit_sha") != "commit_sha":
            problems.append("gate.bind_to must be commit_sha")
        if gate.get("required_verdict") not in (None, "accepted"):
            problems.append("human_approval gates do not use required_verdict")
        for problem in problems:
            diagnostics.append(diagnostic("MACC-PRD-8001", task_id, problem))

        scope = task.get("change_scope") if isinstance(task.get("change_scope"), dict) else {}
        if scope.get("allowed_paths"):
            diagnostics.append(diagnostic("MACC-PRD-8002", task_id, "change_scope.allowed_paths must be empty for a human approval gate."))

        trigger = gate.get("approval_trigger")
        if trigger not in APPROVAL_TRIGGERS:
            diagnostics.append(diagnostic("MACC-PRD-8005", task_id, f"approval_trigger {trigger!r} is not one of: {', '.join(sorted(APPROVAL_TRIGGERS))}."))

        governance = gate.get("governance_ref")
        if not isinstance(governance, str) or not governance.strip():
            diagnostics.append(diagnostic("MACC-PRD-8004", task_id))
            continue
        governance_path = root / governance.split("#", 1)[0]
        if not governance_path.is_file():
            diagnostics.append(diagnostic("MACC-PRD-8004", task_id, f"governance_ref {governance!r} does not exist."))
            continue
        governance_text = text(governance_path)
        for approver in approvers:
            role = approver.get("role") if isinstance(approver, dict) else None
            if isinstance(role, str) and role.strip() and not role_is_traceable(role, governance_text):
                diagnostics.append(diagnostic("MACC-PRD-8003", task_id, f"Role {role!r} does not appear in {governance!r}."))

    # Advisory: high-risk, approval-sensitive work that no human gate precedes.
    for task in tasks:
        if not isinstance(task, dict) or is_human_gate(task) or not isinstance(task.get("id"), str):
            continue
        hints = task.get("routing_hints") if isinstance(task.get("routing_hints"), dict) else {}
        if hints.get("risk_level") != "high":
            continue
        blob = " ".join(str(task.get(key, "")) for key in ("title", "category", "description", "objective"))
        if not SENSITIVE_TEXT.search(blob):
            continue
        if any(is_dependent(task["id"], gate_id, graph) for gate_id in gates):
            continue
        if "no approval" in str(task.get("notes", "")).lower():
            continue
        diagnostics.append(diagnostic("MACC-PRD-8006", task["id"]))


def validation_output(diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    return {"valid": not any(item["blocking"] for item in diagnostics), "diagnostics": diagnostics, "summary": {"blocking": sum(item["blocking"] for item in diagnostics), "warnings": sum(not item["blocking"] for item in diagnostics)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "build-context"):
        child = sub.add_parser(command)
        child.add_argument("--root", default=".")
        if command == "build-context":
            child.add_argument("--output", default=".macc/state/prd-planning-context.json")
    for command in ("inspect-design", "inspect-html"):
        child = sub.add_parser(command)
        child.add_argument("--root", default=".")
        child.add_argument("--path", required=True)
    child = sub.add_parser("validate")
    child.add_argument("--root", default=".")
    child.add_argument("--file", required=True)
    child.add_argument("--profile", choices=["ui-fidelity"])
    child.add_argument("--previous")
    child = sub.add_parser("explain")
    child.add_argument("--diagnostic", required=True)
    args = parser.parse_args()
    if args.command == "explain":
        if args.diagnostic not in DIAGNOSTICS:
            emit({"code": args.diagnostic, "message": "Unknown diagnostic", "blocking": True})
            return 2
        emit(diagnostic(args.diagnostic))
        return 0
    root = Path(args.root).resolve()
    if args.command == "inspect":
        emit(inspect(root))
        return 0
    if args.command == "build-context":
        context = build_context(root)
        output = root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        emit({"output": rel(root, output), "context": context})
        return 0
    if args.command == "inspect-design":
        emit(inspect_design(root, args.path))
        return 0
    if args.command == "inspect-html":
        emit(inspect_html(root, args.path))
        return 0
    result = validate(root, args.file, args.profile, args.previous)
    emit(result)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
