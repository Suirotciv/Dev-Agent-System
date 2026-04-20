from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "scripts"


def load_helpers():
    spec = importlib.util.spec_from_file_location("agent_helpers_test", SCRIPTS / "agent_helpers.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AgentHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        self.helpers = load_helpers()

    def test_slug_hash_frontmatter_and_artifacts(self) -> None:
        self.assertEqual(self.helpers.slugify("  User Auth!! "), "user-auth")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            prompt = tmp_path / "prompt.md"
            prompt.write_text("hello\r\n", encoding="utf-8")
            self.assertRegex(self.helpers.prompt_hash(prompt), r"^[0-9a-f]{12}$")

            session = tmp_path / "2026-04-20-1200-orchestrator.md"
            session.write_text(
                "---\nlegacy: false\ncount: 3\nname: demo\n---\nbody\n",
                encoding="utf-8",
            )
            meta, body = self.helpers.parse_frontmatter(session)
            self.assertEqual(meta["count"], 3)
            self.assertFalse(meta["legacy"])
            self.assertIn("body", body)

            artifacts = tmp_path / "artifacts"
            artifacts.mkdir()
            (artifacts / "README.md").write_text("skip", encoding="utf-8")
            (artifacts / "a.json").write_text("{}", encoding="utf-8")
            (artifacts / "b.md").write_text("skip", encoding="utf-8")
            self.assertEqual(
                [p.name for p in self.helpers.list_artifact_files(artifacts, ".json")],
                ["a.json"],
            )

    def test_apply_change_set_append_and_error(self) -> None:
        data: dict[str, object] = {}
        self.helpers.apply_change(
            data,
            {"op": "set", "path": "features.demo.status", "value": "BUILDING"},
        )
        self.helpers.apply_change(
            data,
            {"op": "append", "path": "known_issues", "value": {"id": "ISSUE-001"}},
        )
        self.assertEqual(data["features"]["demo"]["status"], "BUILDING")  # type: ignore[index]
        self.assertEqual(data["known_issues"][0]["id"], "ISSUE-001")  # type: ignore[index]

        with self.assertRaises(Exception):
            self.helpers.apply_change(
                data,
                {"op": "append", "path": "features.demo.status", "value": "x"},
            )


if __name__ == "__main__":
    unittest.main()
