from __future__ import annotations

"""
bootstrap.py - Interactive project setup wizard for the agent system.

Run this once when you first clone the repo. It stamps all template
placeholders with real values, initializes STATE.json, and computes
prompt hashes so the system is ready for a first agent session.

Usage:
    python .agents/scripts/bootstrap.py [--quiet] [--state PATH]

Flags:
    --quiet     Skip PM teaching explanations (for experienced teams)
    --state     Override path to STATE.json (default: .agents/STATE.json)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Attempt to import agent_helpers from the same scripts directory.
# Works whether the user runs from repo root or from .agents/scripts/.
# ---------------------------------------------------------------------------
_scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts_dir))

try:
    from agent_helpers import (
        AgentSystemError,
        normalize_text,
        prompt_hash,
        read_state,
        slugify,
        write_json,
        write_state,
    )
except ImportError as exc:
    print(
        f"error: could not import agent_helpers from {_scripts_dir}\n"
        f"  Make sure you are running from inside the agent-system repo.\n"
        f"  Details: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# Terminal helpers (no external deps)
# ---------------------------------------------------------------------------

_IS_TTY = sys.stdout.isatty()

BOLD   = "\033[1m"   if _IS_TTY else ""
DIM    = "\033[2m"   if _IS_TTY else ""
GREEN  = "\033[32m"  if _IS_TTY else ""
CYAN   = "\033[36m"  if _IS_TTY else ""
YELLOW = "\033[33m"  if _IS_TTY else ""
RESET  = "\033[0m"   if _IS_TTY else ""


def h1(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{text}{RESET}")


def h2(text: str) -> None:
    print(f"\n{BOLD}{text}{RESET}")


def ok(text: str) -> None:
    print(f"  {GREEN}OK{RESET} {text}")


def note(text: str) -> None:
    print(f"  {DIM}{text}{RESET}")


def warn(text: str) -> None:
    print(f"  {YELLOW}!{RESET} {text}")


def teach(text: str, quiet: bool) -> None:
    """Print a PM teaching moment unless --quiet was passed."""
    if quiet:
        return
    lines = text.strip().splitlines()
    print(f"\n  {DIM}+- PM note")
    for line in lines:
        print(f"  | {line}")
    print(f"  +-{RESET}")


def ask(prompt: str, default: str = "", required: bool = True) -> str:
    """Prompt the user for input, with an optional default value."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    while True:
        value = input(f"  {display}").strip()
        if not value:
            if default:
                return default
            if not required:
                return ""
            print(f"  {YELLOW}This field is required.{RESET}")
        else:
            return value


def ask_choice(prompt: str, choices: list[str], default: str = "") -> str:
    """Ask the user to pick from a numbered list."""
    print(f"\n  {prompt}")
    for i, choice in enumerate(choices, 1):
        marker = f"{GREEN}>{RESET}" if choice == default else " "
        print(f"    {marker} {i}. {choice}")
    while True:
        raw = input(f"  Choice [{default or '1'}]: ").strip()
        if not raw and default:
            return default
        if not raw:
            raw = "1"
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        # allow typing the value directly
        if raw in choices:
            return raw
        print(f"  {YELLOW}Please enter a number between 1 and {len(choices)}.{RESET}")


def confirm(prompt: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    raw = input(f"  {prompt} {hint}: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")


# ---------------------------------------------------------------------------
# Template stamping
# ---------------------------------------------------------------------------

PLACEHOLDER_MAP = {
    # Exact strings used in the template files
    "[PROJECT NAME]":               "project_name",
    "[project-name]":               "project_slug",
    "[One-line product type description]": "description",
    "[one-line product type description]": "description",
    "[One sentence - what it does and for who]": "description",
    "[URL or local path]":          "git_remote",
    "[YYYY-MM-DD]":                 "today",
    "[framework, UI lib, state, build tool]": "frontend_stack",
    "[language, framework, database]":        "backend_stack",
    "[Web App / Mobile App / API / CLI / etc.]": "project_type",
    "[MIT / Apache / Proprietary / etc.]":    "license",
    "[Pre-Alpha / Alpha / Beta / Production]": "status_label",
    "[NAME]":                       "project_name",
    "[X.X.X]":                      "version",
}


def stamp(text: str, values: dict[str, str]) -> str:
    """Replace all known placeholders with real values."""
    for placeholder, key in PLACEHOLDER_MAP.items():
        value = values.get(key, "")
        if value:
            text = text.replace(placeholder, value)
    return text


def stamp_file(path: Path, values: dict[str, str]) -> bool:
    """Stamp a file in place. Returns True if any changes were made."""
    try:
        original = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    updated = stamp(original, values)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


# ---------------------------------------------------------------------------
# Repo root detection
# ---------------------------------------------------------------------------

def find_repo_root() -> Path:
    """Walk up from the script location to find the repo root (.git dir)."""
    candidate = Path(__file__).resolve().parent
    for _ in range(8):
        if (candidate / ".git").exists():
            return candidate
        if (candidate / "AGENTS.md").exists():
            return candidate
        candidate = candidate.parent
    # fallback: current working directory
    return Path.cwd()


# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------

def check_prerequisites(root: Path) -> list[str]:
    warnings: list[str] = []
    if sys.version_info < (3, 9):
        warnings.append(
            f"Python 3.9+ is recommended (you have {sys.version_info.major}.{sys.version_info.minor})"
        )
    if not (root / ".git").exists():
        warnings.append(
            "No .git directory found at repo root. "
            "Initialize git first: git init && git add . && git commit -m 'init'"
        )
    state_path = root / ".agents" / "STATE.json"
    if not state_path.exists():
        warnings.append(
            "STATE.json not found - will be created from defaults during setup."
        )
    return warnings


# ---------------------------------------------------------------------------
# STATE.json initialization
# ---------------------------------------------------------------------------

DEFAULT_STATE_PATH = Path(".agents") / "STATE.json"

PROMPT_FILES = {
    "ORCHESTRATOR.md":          Path(".agents/ORCHESTRATOR.md"),
    "FEATURE_AGENT.md":         Path(".agents/FEATURE_AGENT.md"),
    "VERIFIER_AGENT.md":        Path(".agents/VERIFIER_AGENT.md"),
    "INFRA_AND_DESIGN_AGENTS.md": Path(".agents/INFRA_AND_DESIGN_AGENTS.md"),
}


def compute_prompt_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name, rel_path in PROMPT_FILES.items():
        full = root / rel_path
        if full.exists():
            hashes[name] = prompt_hash(full)
        else:
            hashes[name] = "000000000000"
            warn(f"Prompt file not found, hash set to placeholder: {rel_path}")
    return hashes


def build_initial_state(values: dict[str, str], root: Path) -> dict:
    today = values["today"]
    name = values["project_name"]
    hashes = compute_prompt_hashes(root)

    return {
        "_readme": (
            "Live machine-readable snapshot for the agent team. "
            "The Orchestrator is the default sole writer. "
            "Other agents submit update envelopes in .agents/updates/ "
            "and append-only artifacts in .agents/sessions/ and .agents/gates/."
        ),
        "_updated": today,
        "_updated_by": "bootstrap",
        "_state_revision": 1,
        "_state_write_policy": (
            "Normal path: non-orchestrator agents emit update envelopes; "
            "the Orchestrator merges them into STATE.json. "
            "Direct writes are reserved for the Orchestrator or an explicit "
            "compare-and-swap emergency path."
        ),
        "_id_formats": {
            "blocker":      "BLOCKER-001",
            "known_issue":  "ISSUE-001",
            "design_request": "DESIGN-REQ-001",
            "task_node":    "TASK-ROOT or TASK-001",
            "session":      "SES-YYYYMMDD-HHMMSS-role[-feature]",
            "gate_attempt": "GATE-YYYYMMDD-HHMMSS-feature-gate",
            "update":       "UPD-YYYYMMDD-HHMMSS-role[-feature]-NN",
            "resource_claim": "RC-YYYYMMDD-HHMMSS-feature-shortid",
        },
        "prompt_versions": {
            "_note": (
                "Short SHA-256 hash (first 12 hex chars) of the normalized prompt "
                "file contents. Run prompt-hash.py --write-state to refresh."
            ),
            **hashes,
        },
        "project": {
            "name":    name,
            "version": "0.1.0",
            "phase":   1,
            "status":  "pre-alpha",
        },
        "sprint": {
            "name":        "Sprint 1.0",
            "goal":        "Set up project and define first features",
            "target_date": today,
            "phase":       1,
        },
        "task_tree": {
            "_note": "Optional nested planning structure. Node IDs follow _id_formats.task_node.",
            "version": 1,
            "nodes": [],
        },
        "core_stability": {
            "_note": "STABLE = safe to build against. IN_PROGRESS = feature agents should block.",
            "User":         "STABLE",
            "Session":      "STABLE",
            "FeatureFlags": "STABLE",
        },
        "features": {
            "_note": "Each feature entry tracks lifecycle, ownership, and runtime bundle.",
            "_statuses": {
                "BUILDING":    "In active development. Flag required if merged before ship-ready.",
                "FUNCTIONAL":  "Ready for verifier FUNCTIONAL gate.",
                "VERIFIED":    "Passed FUNCTIONAL and any required verification.",
                "SHIP_READY":  "Polished, verified, and ready for release queue.",
                "BLOCKED":     "Cannot proceed - see blockers array.",
            },
        },
        "flags": {
            "_note": "All active feature flags. Remove entry when flag is fully removed from code.",
        },
        "gates": {
            "_note": "Append-only summary index. Full evidence in per-attempt artifacts under .agents/gates/.",
        },
        "blockers": {
            "_note": "Cross-agent dependencies. File here instead of editing another role's owned files.",
        },
        "design_requests": {
            "_note": "Lightweight non-blocking signals for shared design work.",
            "items": [],
        },
        "do_not_break": {
            "_note": "Features or interfaces confirmed working. Regression against these is a hard stop.",
        },
        "known_issues": [],
        "stale_flags_to_remove": {
            "_note": "Flags whose features have shipped but have not been cleaned up yet.",
        },
        "environment_flag_matrix": {
            "_note": "Current flag state per environment. Infra owns this.",
        },
    }


# ---------------------------------------------------------------------------
# Setup log
# ---------------------------------------------------------------------------

def write_setup_log(root: Path, values: dict[str, str], stamped: list[str]) -> None:
    log_path = root / ".agents" / "SETUP_LOG.md"
    lines = [
        "# Setup Log\n",
        f"Bootstrap run: {values['today']}\n",
        "\n## Project values recorded\n",
    ]
    for key, val in values.items():
        if val:
            lines.append(f"- `{key}`: {val}\n")
    lines.append("\n## Files stamped\n")
    for f in stamped:
        lines.append(f"- {f}\n")
    lines.append(
        "\n## Next steps\n"
        "1. Run `python .agents/scripts/new-feature.py` to scaffold your first feature\n"
        "2. Read `GETTING_STARTED.md` for the full day-0 walkthrough\n"
        "3. Read `MODELS.md` to confirm your model meets the minimum requirements\n"
    )
    log_path.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# .env.example update
# ---------------------------------------------------------------------------

def update_env_example(root: Path, values: dict[str, str]) -> None:
    env_path = root / ".env.example"
    if not env_path.exists():
        return
    text = env_path.read_text(encoding="utf-8")
    slug_upper = values["project_slug"].upper().replace("-", "_")
    text = text.replace("APP_BASE_URL", f"{slug_upper}_BASE_URL")
    env_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main wizard
# ---------------------------------------------------------------------------

def run_wizard(quiet: bool, state_path_override: str | None, root: Path) -> None:
    h1("Agent System - Project Setup Wizard")
    print(
        f"\n  {DIM}This wizard stamps all template placeholders with your project's\n"
        f"  real values, initializes STATE.json, and computes prompt hashes\n"
        f"  so the system is ready for a first agent session.{RESET}\n"
    )

    teach(
        "What is this system?\n"
        "\n"
        "  This is a coordination layer for AI agents working on your codebase.\n"
        "  Instead of one AI doing everything in one conversation, a team of\n"
        "  specialized agents each owns a slice of the work - and a single\n"
        "  STATE.json file keeps them coordinated without stepping on each other.\n"
        "\n"
        "  Think of it less like 'asking an AI to write code' and more like\n"
        "  managing a small engineering team where you are the tech lead.",
        quiet,
    )

    # -- Prerequisite checks --
    h2("Checking prerequisites...")
    warnings = check_prerequisites(root)
    if warnings:
        for w in warnings:
            warn(w)
        if not confirm("Continue anyway?", default=False):
            raise SystemExit(0)
    else:
        ok("All prerequisites met")

    # -- Gather project values --
    h2("Project identity")

    project_name = ask("Project name (e.g. 'TaskFlow' or 'my-api')")
    project_slug = slugify(project_name)
    note(f"Slug will be: {project_slug}")

    description = ask("One-line description (what does it do, for who?)")

    project_type = ask_choice(
        "Project type:",
        ["Web App", "Mobile App", "API / Backend", "CLI", "Library", "Other"],
        default="Web App",
    )

    h2("Technology stack")
    teach(
        "You don't have to have this figured out perfectly yet. These values\n"
        "go into PROJECT_CONTEXT.md as reference - they don't affect how the\n"
        "agent system itself works. Fill in what you know.",
        quiet,
    )

    frontend_stack = ask(
        "Frontend stack (e.g. 'React, Tailwind, Vite')",
        required=False,
        default="TBD",
    )
    backend_stack = ask(
        "Backend stack (e.g. 'Node.js, Express, PostgreSQL')",
        required=False,
        default="TBD",
    )

    h2("Model configuration")
    teach(
        "The agent system is model-agnostic - it works with local models (Ollama,\n"
        "LM Studio, etc.) and cloud providers (Anthropic, OpenAI, Gemini).\n"
        "\n"
        "  The Orchestrator role requires at least a 70B model or a frontier\n"
        "  cloud model. Smaller models can run Feature Agent and Verifier roles.\n"
        "  See MODELS.md for the full capability matrix.",
        quiet,
    )

    model_provider = ask_choice(
        "Primary model provider:",
        ["Anthropic (cloud)", "OpenAI (cloud)", "Local (Ollama / LM Studio)", "Multiple / mixed"],
        default="Anthropic (cloud)",
    )

    if "Local" in model_provider:
        warn(
            "Local models require a 128k context window minimum.\n"
            "  Models below 32B may struggle with the Orchestrator and Verifier roles.\n"
            "  See MODELS.md after setup for guidance."
        )

    h2("Team configuration")
    team_size = ask_choice(
        "Team size:",
        ["Solo (just me)", "Small team (2-5 people)", "Larger team (5+)"],
        default="Solo (just me)",
    )

    h2("Optional")
    git_remote = ask(
        "Git remote URL (leave blank to fill in later)",
        required=False,
    )
    license_str = ask(
        "License",
        default="MIT",
        required=False,
    )

    # -- Build values dict --
    today = date.today().isoformat()
    values: dict[str, str] = {
        "project_name":    project_name,
        "project_slug":    project_slug,
        "description":     description,
        "project_type":    project_type,
        "frontend_stack":  frontend_stack,
        "backend_stack":   backend_stack,
        "git_remote":      git_remote or "[URL or local path]",
        "license":         license_str or "MIT",
        "status_label":    "Pre-Alpha",
        "today":           today,
        "version":         "0.1.0",
    }

    # -- Stamp template files --
    h2("Stamping template files...")

    stamp_targets = [
        root / "PROJECT_CONTEXT.md",
        root / "AGENTS.md",
        root / "QUICK_REFERENCE.md",
        root / "GETTING_STARTED.md",
        root / ".env.example",
    ]

    stamped: list[str] = []
    for path in stamp_targets:
        if path.exists():
            changed = stamp_file(path, values)
            if changed:
                ok(str(path.relative_to(root)))
                stamped.append(str(path.relative_to(root)))
            else:
                note(f"No placeholders found in {path.relative_to(root)}")
        else:
            note(f"Skipped (not found): {path.relative_to(root)}")

    # -- Initialize STATE.json --
    h2("Initializing STATE.json...")

    state_path = Path(state_path_override) if state_path_override else root / ".agents" / "STATE.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    initial_state = build_initial_state(values, root)

    if state_path.exists():
        if confirm(f"STATE.json already exists at {state_path}. Overwrite?", default=False):
            write_json(state_path, initial_state)
            ok("STATE.json overwritten")
        else:
            note("Keeping existing STATE.json")
    else:
        write_json(state_path, initial_state)
        ok("STATE.json created")

    # -- Update .env.example --
    update_env_example(root, values)

    # -- Write setup log --
    write_setup_log(root, values, stamped)
    ok(".agents/SETUP_LOG.md written")

    # -- Confirm directories exist --
    for d in [".agents/sessions", ".agents/gates", ".agents/updates"]:
        (root / d).mkdir(parents=True, exist_ok=True)

    # -- Summary --
    h1("Setup complete")
    print(
        f"\n  Project:   {BOLD}{project_name}{RESET}\n"
        f"  Slug:      {project_slug}\n"
        f"  State rev: 1\n"
    )

    teach(
        "What just happened?\n"
        "\n"
        "  STATE.json is now initialized. It is the single source of truth for\n"
        "  every agent working on this project. Think of it as your project's\n"
        "  live status board - it tracks what's being built, what's done, what's\n"
        "  blocked, and who is responsible for what.\n"
        "\n"
        "  Unlike a chat thread, STATE.json persists across sessions, survives\n"
        "  context resets, and can be read by any agent without them needing to\n"
        "  catch up on the conversation history. This is the key insight behind\n"
        "  the whole system: explicit shared state beats implicit shared memory.",
        quiet,
    )

    print(f"\n  {BOLD}Next steps:{RESET}")
    print(f"  1. Read {CYAN}GETTING_STARTED.md{RESET} for the full day-0 walkthrough")
    print(f"  2. Read {CYAN}MODELS.md{RESET} to confirm your model meets requirements")
    print(
        f"  3. Run {CYAN}python .agents/scripts/new-feature.py "
        f"--name your-feature --issue 1{RESET} to scaffold your first feature"
    )
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive setup wizard for the agent system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run from the repo root. Requires Python 3.9+.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Skip PM teaching explanations",
    )
    parser.add_argument(
        "--state",
        help="Override path to STATE.json",
    )
    parser.add_argument(
        "--root",
        help="Override repo root path (default: auto-detected)",
    )
    args = parser.parse_args()

    root = Path(args.root) if args.root else find_repo_root()

    try:
        run_wizard(quiet=args.quiet, state_path_override=args.state, root=root)
        return 0
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Setup cancelled.{RESET}\n")
        return 1
    except AgentSystemError as exc:
        print(f"\n  {YELLOW}Error: {exc}{RESET}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
