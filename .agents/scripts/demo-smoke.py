from __future__ import annotations

"""
demo-smoke.py - Run a disposable end-to-end demo of the agent-system workflow.

The demo creates a temporary project, refreshes prompt hashes, scaffolds a
feature, dry-runs the update envelope merge, and validates artifacts.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(command: list[str], *, cwd: Path) -> None:
    display = " ".join(command)
    print(f"\n$ {display}")
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def latest_update(project: Path) -> Path:
    updates = sorted((project / ".agents" / "updates").glob("*.json"))
    if not updates:
        raise SystemExit("demo failed: no update envelope was created")
    return updates[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the beginner smoke demo.")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the temporary demo directory and print its path",
    )
    args = parser.parse_args()

    root = repo_root()
    python = sys.executable

    temp_dir = tempfile.TemporaryDirectory(prefix="agent-system-demo-")
    tmp = temp_dir.name
    if args.keep:
        temp_dir.cleanup = lambda: None  # type: ignore[method-assign]

    with temp_dir:
        project = Path(tmp) / "solo-demo"

        print("Agent System smoke demo")
        print(f"Template: {root}")
        print(f"Demo project: {project}")

        run(
            [
                python,
                str(root / ".agents" / "scripts" / "new-project.py"),
                "--name",
                "Solo Demo",
                "--description",
                "A disposable project used to prove the agent-system workflow.",
                "--type",
                "CLI",
                "--frontend",
                "None",
                "--backend",
                "Python stdlib",
                "--output-dir",
                str(project),
            ],
            cwd=root,
        )

        run(
            [
                python,
                ".agents/scripts/prompt-hash.py",
                "--write-state",
                "--expected-revision",
                "1",
            ],
            cwd=project,
        )

        run(
            [
                python,
                ".agents/scripts/new-feature.py",
                "--name",
                "first-feature",
                "--issue",
                "1",
                "--quiet",
            ],
            cwd=project,
        )

        update_path = latest_update(project)
        run(
            [
                python,
                ".agents/scripts/merge-updates.py",
                "--expected-revision",
                "2",
                "--dry-run",
                str(update_path.relative_to(project)),
            ],
            cwd=project,
        )

        run([python, ".agents/scripts/validate-agent-artifacts.py"], cwd=project)

        print("\nSmoke demo passed.")
        if args.keep:
            print(f"Kept demo project at: {project}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
