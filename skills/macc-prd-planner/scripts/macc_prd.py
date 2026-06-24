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
}


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
