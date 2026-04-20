from __future__ import annotations

"""
new-project.py - Scriptable project template stamper.

Non-interactive version of bootstrap.py for use in CI/CD, team templates,
or automated project generation. Takes all values as flags.

Usage:
    python .agents/scripts/new-project.py \\
        --name "TaskFlow" \\
        --description "Task management for small teams" \\
        --type "Web App" \\
        --frontend "React, Tailwind, Vite" \\
        --backend "Node.js, Express, PostgreSQL" \\
        [--git-remote "https://github.com/org/repo"] \\
        [--license MIT] \\
        [--output-dir /path/to/new/project]

If --output-dir is provided, the repo template is copied there and then
stamped. If omitted, stamps are applied in place (current repo).
"""

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts_dir))

try:
    from agent_helpers import AgentSystemError, slugify, write_json
    from bootstrap import (
        build_initial_state,
        compute_prompt_hashes,
        find_repo_root,
        stamp_file,
        update_env_example,
        write_setup_log,
    )
except ImportError as exc:
    print(f"error: could not import dependencies: {exc}", file=sys.stderr)
    raise SystemExit(1)


def copy_template_to_output(template_root: Path, output_dir: Path) -> None:
    """Copy the template repo structure to output_dir."""
    if output_dir.exists():
        print(f"error: output directory already exists: {output_dir}", file=sys.stderr)
        raise SystemExit(1)

    # Copy everything except .git and node_modules
    ignore = shutil.ignore_patterns(".git", "node_modules", "__pycache__", "*.pyc", ".DS_Store")
    shutil.copytree(str(template_root), str(output_dir), ignore=ignore)
    print(f"  Copied template to: {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scriptable project template stamper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name",        required=True, help="Project name (e.g. 'TaskFlow')")
    parser.add_argument("--description", required=True, help="One-line description")
    parser.add_argument(
        "--type",
        default="Web App",
        choices=["Web App", "Mobile App", "API / Backend", "CLI", "Library", "Other"],
        help="Project type (default: Web App)",
    )
    parser.add_argument("--frontend",   default="TBD", help="Frontend stack description")
    parser.add_argument("--backend",    default="TBD", help="Backend stack description")
    parser.add_argument("--git-remote", default="",    help="Git remote URL")
    parser.add_argument("--license",    default="MIT", help="License (default: MIT)")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="If provided, copy template here before stamping",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="Override path to STATE.json",
    )
    args = parser.parse_args()

    template_root = find_repo_root()

    if args.output_dir:
        output_root = Path(args.output_dir).resolve()
        copy_template_to_output(template_root, output_root)
    else:
        output_root = template_root

    today = date.today().isoformat()
    project_slug = slugify(args.name)

    values: dict[str, str] = {
        "project_name":    args.name,
        "project_slug":    project_slug,
        "description":     args.description,
        "project_type":    args.type,
        "frontend_stack":  args.frontend,
        "backend_stack":   args.backend,
        "git_remote":      args.git_remote or "[URL or local path]",
        "license":         args.license,
        "status_label":    "Pre-Alpha",
        "today":           today,
        "version":         "0.1.0",
    }

    # Stamp template files
    stamp_targets = [
        output_root / "PROJECT_CONTEXT.md",
        output_root / "AGENTS.md",
        output_root / "QUICK_REFERENCE.md",
        output_root / "GETTING_STARTED.md",
        output_root / ".env.example",
    ]

    stamped: list[str] = []
    for path in stamp_targets:
        if path.exists():
            changed = stamp_file(path, values)
            if changed:
                print(f"  stamped: {path.relative_to(output_root)}")
                stamped.append(str(path.relative_to(output_root)))

    # Initialize STATE.json
    state_path = (
        Path(args.state) if args.state
        else output_root / ".agents" / "STATE.json"
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)

    initial_state = build_initial_state(values, output_root)
    write_json(state_path, initial_state)
    print(f"  initialized: {state_path.relative_to(output_root)}")

    update_env_example(output_root, values)
    write_setup_log(output_root, values, stamped)

    # Ensure required directories exist
    for d in [".agents/sessions", ".agents/gates", ".agents/updates"]:
        (output_root / d).mkdir(parents=True, exist_ok=True)

    print(f"\n  Project '{args.name}' initialized at: {output_root}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
