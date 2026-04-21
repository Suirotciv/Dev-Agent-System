from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "scripts"
PYTHON = sys.executable


def load_spec_interview_module():
    path = ROOT / ".agents" / "scripts" / "spec-interview.py"
    spec = importlib.util.spec_from_file_location("spec_interview_mod", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(
    args: list[str],
    cwd: Path,
    expect: int = 0,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if completed.returncode != expect:
        raise AssertionError(
            f"command failed with {completed.returncode}, expected {expect}\n"
            f"cmd: {' '.join(args)}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


class ScriptWorkflowTests(unittest.TestCase):
    def make_project(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        project = Path(temp.name) / "project"
        run_script(
            [
                PYTHON,
                str(SCRIPTS / "new-project.py"),
                "--name",
                "Test Project",
                "--description",
                "Disposable test project",
                "--output-dir",
                str(project),
            ],
            cwd=ROOT,
        )
        return temp, project

    def test_prompt_hash_check_and_write(self) -> None:
        temp, project = self.make_project()
        with temp:
            result = run_script([PYTHON, ".agents/scripts/prompt-hash.py", "--check"], cwd=project)
            self.assertIn('"status": "ok"', result.stdout)

            prompt = project / ".agents" / "FEATURE_AGENT.md"
            prompt.write_text(prompt.read_text(encoding="utf-8") + "\nTest drift.\n", encoding="utf-8")
            run_script([PYTHON, ".agents/scripts/prompt-hash.py", "--check"], cwd=project, expect=1)
            run_script(
                [
                    PYTHON,
                    ".agents/scripts/prompt-hash.py",
                    "--write-state",
                    "--expected-revision",
                    "1",
                ],
                cwd=project,
            )
            run_script([PYTHON, ".agents/scripts/prompt-hash.py", "--check"], cwd=project)

    def test_new_feature_merge_dry_run_and_validation(self) -> None:
        temp, project = self.make_project()
        with temp:
            run_script(
                [
                    PYTHON,
                    ".agents/scripts/new-feature.py",
                    "--name",
                    "User Auth",
                    "--issue",
                    "7",
                    "--quiet",
                ],
                cwd=project,
            )
            state = json.loads((project / ".agents" / "STATE.json").read_text(encoding="utf-8"))
            self.assertNotIn("user-auth", state["features"])

            update = sorted((project / ".agents" / "updates").glob("*.json"))[-1]
            run_script(
                [
                    PYTHON,
                    ".agents/scripts/merge-updates.py",
                    "--expected-revision",
                    "1",
                    "--dry-run",
                    str(update.relative_to(project)),
                ],
                cwd=project,
            )
            run_script([PYTHON, ".agents/scripts/validate-agent-artifacts.py"], cwd=project)

    def test_merge_rejects_invalid_status(self) -> None:
        temp, project = self.make_project()
        with temp:
            update = project / ".agents" / "updates" / "2026-04-20-1200-bad.json"
            update.write_text(
                json.dumps(
                    {
                        "update_id": "UPD-20260420-120000-bad-01",
                        "submitted_at": "2026-04-20T12:00:00+00:00",
                        "submitted_by": "test",
                        "role": "orchestrator",
                        "_prompt_version": "abcdef123456",
                        "_state_revision_at_start": 1,
                        "target_feature": "bad",
                        "resource_claim_id": None,
                        "summary": "bad status",
                        "changes": [
                            {
                                "op": "set",
                                "path": "features.bad",
                                "value": {
                                    "status": "NOPE",
                                    "spec_status": "INTERVIEW_NEEDED",
                                },
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            run_script(
                [
                    PYTHON,
                    ".agents/scripts/merge-updates.py",
                    "--expected-revision",
                    "1",
                    "--dry-run",
                    str(update.relative_to(project)),
                ],
                cwd=project,
                expect=1,
            )

    def test_merge_known_issue_gate_append_and_revision_mismatch(self) -> None:
        temp, project = self.make_project()
        with temp:
            update = project / ".agents" / "updates" / "2026-04-20-1200-gate.json"
            update.write_text(
                json.dumps(
                    {
                        "update_id": "UPD-20260420-120000-gate-01",
                        "submitted_at": "2026-04-20T12:00:00+00:00",
                        "submitted_by": "test",
                        "role": "orchestrator",
                        "_prompt_version": "abcdef123456",
                        "_state_revision_at_start": 1,
                        "target_feature": "demo",
                        "resource_claim_id": None,
                        "summary": "record known issue and gate summary",
                        "changes": [
                            {
                                "op": "append",
                                "path": "known_issues",
                                "value": {
                                    "id": "ISSUE-999",
                                    "description": "Example issue",
                                    "owner": "orchestrator",
                                    "priority": "LOW",
                                    "opened": "2026-04-20",
                                },
                            },
                            {
                                "op": "append",
                                "path": "gates.demo",
                                "value": {
                                    "gate_attempt_id": "GATE-20260420-120000-demo-functional",
                                    "artifact": ".agents/gates/2026-04-20-1200-demo-functional.json",
                                    "gate": "FUNCTIONAL",
                                    "date": "2026-04-20",
                                    "result": "PASS",
                                },
                            },
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            run_script(
                [
                    PYTHON,
                    ".agents/scripts/merge-updates.py",
                    "--expected-revision",
                    "999",
                    str(update.relative_to(project)),
                ],
                cwd=project,
                expect=1,
            )
            run_script(
                [
                    PYTHON,
                    ".agents/scripts/merge-updates.py",
                    "--expected-revision",
                    "1",
                    str(update.relative_to(project)),
                ],
                cwd=project,
            )
            state = json.loads((project / ".agents" / "STATE.json").read_text(encoding="utf-8"))
            self.assertEqual(state["_state_revision"], 2)
            self.assertEqual(state["known_issues"][-1]["id"], "ISSUE-999")
            self.assertEqual(state["gates"]["demo"][-1]["result"], "PASS")

    def test_allocate_runtime_claim_release(self) -> None:
        temp, project = self.make_project()
        with temp:
            state_path = project / ".agents" / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["features"]["demo"] = {
                "status": "BUILDING",
                "spec_status": "SPEC_APPROVED",
                "flag": "FLAGS.DEMO",
                "agent": None,
                "started": "2026-04-20",
                "spec": "src/features/demo/SPEC.md",
                "blockers": [],
                "notes": "",
                "runtime_port": None,
                "test_db": None,
                "worktree_path": None,
                "resource_claim_id": None,
                "compose_project_name": None,
                "cache_namespace": None,
            }
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            run_script(
                [
                    PYTHON,
                    ".agents/scripts/allocate-runtime.py",
                    "claim",
                    "demo",
                    "--expected-revision",
                    "1",
                    "--port",
                    "3105",
                ],
                cwd=project,
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["features"]["demo"]["runtime_port"], 3105)
            self.assertEqual(state["_state_revision"], 2)

            run_script(
                [
                    PYTHON,
                    ".agents/scripts/allocate-runtime.py",
                    "release",
                    "demo",
                    "--expected-revision",
                    "2",
                ],
                cwd=project,
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIsNone(state["features"]["demo"]["runtime_port"])

    def test_malformed_artifact_fails_validation(self) -> None:
        temp, project = self.make_project()
        with temp:
            bad_gate = project / ".agents" / "gates" / "2026-04-20-1200-demo-functional.json"
            bad_gate.write_text("{}", encoding="utf-8")
            run_script([PYTHON, ".agents/scripts/validate-agent-artifacts.py"], cwd=project, expect=1)


class SpecInterviewTests(unittest.TestCase):
    def test_replace_interview_section(self) -> None:
        mod = load_spec_interview_module()
        src = (
            "# X\n\n## Interview notes\n\n(old)\n\n---\n\n"
            "## User Story\n\nAs a user,\n"
        )
        out = mod.replace_interview_section(src, "NEW BODY")
        self.assertIn("NEW BODY", out)
        self.assertNotIn("(old)", out)
        self.assertIn("## User Story", out)
        self.assertIn("As a user,", out)


class AcceptanceCommandTests(unittest.TestCase):
    def test_help_commands_exit_zero(self) -> None:
        commands = [
            [PYTHON, ".agents/scripts/bootstrap.py", "--help"],
            [PYTHON, ".agents/scripts/new-project.py", "--help"],
            [PYTHON, ".agents/scripts/new-feature.py", "--help"],
            [PYTHON, ".agents/scripts/merge-updates.py", "--help"],
            [PYTHON, ".agents/scripts/allocate-runtime.py", "--help"],
            [PYTHON, ".agents/scripts/spec-interview.py", "--help"],
        ]
        for command in commands:
            with self.subTest(command=command):
                run_script(command, cwd=ROOT)

    def test_demo_smoke_passes(self) -> None:
        run_script([PYTHON, ".agents/scripts/demo-smoke.py"], cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
