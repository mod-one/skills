"""Regression tests for human approval gates in macc-prd-planner's validator.

Run: python3 -m unittest discover -s tests -v   (from the repository root)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "macc-prd-planner" / "scripts" / "macc_prd.py"
SKILL = SCRIPT.parents[1]

GOVERNANCE = """# Décisions

**Propriétaires :** Product Owner, Lead technique, Responsable sécurité

### 5.3 Approbations minimales

| Domaine | Approbateurs |
| --- | --- |
| produit/périmètre | Product Owner + opérations |
| sécurité/identité | Responsable sécurité + Lead technique |
"""


def task(task_id, **extra):
    base = {
        "id": task_id,
        "title": f"{task_id} documentation and verification",
        "category": "docs",
        "description": "Problem/Goal: g\nKey actions: a\nOut of scope: o\nSuccess criteria: tests pass",
        "dependencies": [],
        "priority": "1",
        "scope_ref": "sec",
    }
    base.update(extra)
    return base


def gate_task(**gate_overrides):
    gate = {
        "kind": "human_approval",
        "subject_task": "SEC-ADR-003",
        "approval_trigger": "sensitive-data-model",
        "governance_ref": "docs/16-decisions.md",
        "required_approvers": [
            {"role": "RESPONSABLE_SECURITE", "count": 1},
            {"role": "LEAD_TECHNIQUE", "count": 1},
        ],
        "quorum": "all",
        "bind_to": "commit_sha",
        "evidence_type": "pull_request_review",
    }
    gate.update(gate_overrides)
    return task("SEC-APP-003", title="Approve the recovery-code model", category="approval",
                dependencies=["SEC-ADR-003"], gate=gate)


class GateValidation(unittest.TestCase):
    def run_validate(self, tasks):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "16-decisions.md").write_text(GOVERNANCE, encoding="utf-8")
            prd = {"prd_scope": {"kind": "feature", "id": "sec", "name": "Security", "definition": "MFA"},
                   "tasks": tasks}
            (root / "prd.json").write_text(json.dumps(prd), encoding="utf-8")
            out = subprocess.run([sys.executable, str(SCRIPT), "validate", "--root", str(root), "--file", "prd.json"],
                                 capture_output=True, text=True, check=False)
            return json.loads(out.stdout)

    def codes(self, result):
        return sorted({d["code"] for d in result["diagnostics"] if d["code"].startswith("MACC-PRD-8")})

    def base(self, gate=None, dependant_deps=("SEC-APP-003",)):
        return [
            task("SEC-ADR-003", title="Draft ADR-003 recovery-code model"),
            gate if gate is not None else gate_task(),
            task("SEC-DB-004", title="Migrate recovery codes", dependencies=list(dependant_deps),
                 routing_hints={"execution_mode": "structural", "reasoning_depth": "deep",
                                "context_scope": "module", "risk_level": "high", "validation_profile": "heavy"}),
        ]

    def test_valid_gate_with_accented_prose_roles_passes(self):
        result = self.run_validate(self.base())
        self.assertEqual(self.codes(result), [], result["diagnostics"])

    def test_invented_role_is_not_traceable(self):
        g = gate_task(required_approvers=[{"role": "LEAD_ARCHITECT", "count": 1}])
        result = self.run_validate(self.base(g))
        self.assertIn("MACC-PRD-8003", self.codes(result))
        self.assertFalse(result["valid"])

    def test_missing_or_absent_governance_source(self):
        self.assertIn("MACC-PRD-8004", self.codes(self.run_validate(self.base(gate_task(governance_ref=None)))))
        self.assertIn("MACC-PRD-8004", self.codes(self.run_validate(self.base(gate_task(governance_ref="docs/nope.md")))))

    def test_gate_without_a_trigger_is_refused(self):
        self.assertIn("MACC-PRD-8005", self.codes(self.run_validate(self.base(gate_task(approval_trigger=None)))))
        self.assertIn("MACC-PRD-8005", self.codes(self.run_validate(self.base(gate_task(approval_trigger="nice-to-have")))))

    def test_structural_defects(self):
        g = gate_task(subject_task="OTHER", required_approvers=[], quorum=7, bind_to="tag")
        result = self.run_validate(self.base(g))
        details = " ".join(d.get("detail", "") for d in result["diagnostics"] if d["code"] == "MACC-PRD-8001")
        for fragment in ("must also be listed in dependencies", "at least one role", "quorum", "bind_to"):
            self.assertIn(fragment, details)

    def test_gate_with_executable_scope_is_refused(self):
        g = gate_task()
        g["change_scope"] = {"allowed_paths": ["docs/adr/**"]}
        self.assertIn("MACC-PRD-8002", self.codes(self.run_validate(self.base(g))))

    def test_high_risk_sensitive_work_outside_a_gate_is_flagged_but_not_blocking(self):
        result = self.run_validate(self.base(dependant_deps=("SEC-ADR-003",)))
        advisory = [d for d in result["diagnostics"] if d["code"] == "MACC-PRD-8006"]
        self.assertEqual([d["task_id"] for d in advisory], ["SEC-DB-004"])
        self.assertFalse(advisory[0]["blocking"])

    def test_explain_knows_every_gate_code(self):
        for code in ("MACC-PRD-8001", "MACC-PRD-8002", "MACC-PRD-8003", "MACC-PRD-8004", "MACC-PRD-8005", "MACC-PRD-8006"):
            out = subprocess.run([sys.executable, str(SCRIPT), "explain", "--diagnostic", code],
                                 capture_output=True, text=True, check=False)
            self.assertEqual(out.returncode, 0, code)


class GovernanceDiscovery(unittest.TestCase):
    def test_approval_matrix_is_extracted_and_macc_state_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "16-decisions.md").write_text(GOVERNANCE, encoding="utf-8")
            noisy = root / ".macc" / "worktree" / "w1" / "docs"
            noisy.mkdir(parents=True)
            (noisy / "16-decisions.md").write_text(GOVERNANCE, encoding="utf-8")
            out = subprocess.run([sys.executable, str(SCRIPT), "inspect", "--root", str(root)],
                                 capture_output=True, text=True, check=True)
            sources = json.loads(out.stdout)["governance_sources"]
            self.assertEqual([s["path"] for s in sources], ["docs/16-decisions.md"])
            self.assertEqual(sources[0]["kind"], "approval-matrix")
            rules = {r["domain"]: r["approvers"] for r in sources[0]["approval_rules"]}
            self.assertEqual(rules["sécurité/identité"], "Responsable sécurité + Lead technique")
            self.assertNotIn("Domaine", rules, "header row must not be reported as a rule")


class BundledArtefacts(unittest.TestCase):
    def test_schema_and_template_parse_and_agree(self):
        schema = json.loads((SKILL / "schemas" / "human-approval-gate.schema.json").read_text(encoding="utf-8"))
        template = json.loads((SKILL / "templates" / "human-approval-gate-task.json").read_text(encoding="utf-8"))
        for field in schema["required"]:
            self.assertIn(field, template["gate"], field)
        self.assertEqual(template["change_scope"]["allowed_paths"], [])
        self.assertIn(template["gate"]["subject_task"], template["dependencies"])


if __name__ == "__main__":
    unittest.main()
