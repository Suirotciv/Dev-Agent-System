from __future__ import annotations

"""
spec-interview.py — Interactive spec interview that writes Interview notes into SPEC.md.

Use this when you want a form-like flow in the terminal instead of staring at
empty placeholders. It does not replace an Orchestrator agent for judgment
calls; it captures your answers in the right place for the feature agent.

Usage:
    python .agents/scripts/spec-interview.py --feature pixel-editor
    python .agents/scripts/spec-interview.py --feature pixel-editor --root C:\\path\\to\\Pixel_App
    python .agents/scripts/spec-interview.py --feature pixel-editor --dry-run

Duplicate .agents/updates/*.json files:
    If you ran new-feature.py twice, you get two envelopes. Keep the newest,
    delete the older one(s), then merge once. Only one merge should add the feature.
"""

import argparse
import sys
from datetime import date
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts_dir))

from agent_helpers import AgentSystemError, normalize_text, slugify  # noqa: E402


def replace_interview_section(content: str, interview_body: str) -> str:
    """Replace everything from '## Interview notes' up to (but not including) '## User Story'."""
    start_marker = "## Interview notes"
    end_marker = "\n## User Story"
    text = normalize_text(content)
    start = text.find(start_marker)
    if start == -1:
        raise AgentSystemError("SPEC.md is missing '## Interview notes' section")
    end = text.find(end_marker, start)
    if end == -1:
        raise AgentSystemError("SPEC.md is missing '## User Story' after Interview notes")
    # Keep "## User Story" and everything after it (drop the leading newline).
    tail = text[end + 1 :].lstrip("\n")
    new_block = f"{start_marker}\n\n{interview_body.strip()}\n\n---\n\n{tail}"
    return text[:start] + new_block


def prompt_multiline(label: str) -> str:
    print(f"\n{label}")
    print("(Finish with an empty line.)")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "" and lines:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def prompt_line(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        raw = input(f"{label}{suffix}: ").strip()
    except EOFError:
        return default
    return raw if raw else default


def run_wizard(feature: str, root: Path, dry_run: bool) -> None:
    slug = slugify(feature)
    spec_path = root / "src" / "features" / slug / "SPEC.md"
    if not spec_path.exists():
        raise AgentSystemError(
            f"SPEC.md not found: {spec_path}\n"
            f"Run new-feature.py --name {slug} first."
        )

    today = date.today().isoformat()
    print(
        f"\nSpec interview wizard → {spec_path.relative_to(root)}\n"
        "Answer in your own words. Short bullets are fine.\n"
    )

    user_goal = prompt_multiline("1) Who is the user, and what are they trying to accomplish?")
    success = prompt_multiline("2) What does success look like from the user's perspective?")
    print("\n3) Three ways this could fail or disappoint (one line each is OK).")
    fail1 = prompt_line("   Failure 1")
    fail2 = prompt_line("   Failure 2")
    fail3 = prompt_line("   Failure 3")
    out_scope = prompt_multiline("4) What is explicitly OUT of scope for this version?")
    patterns = prompt_multiline(
        "5) Any patterns, files, or constraints to follow? (or leave blank)"
    )
    extras = prompt_multiline(
        "6) Anything else the builder must know? (e.g. eyedropper, export size — or leave blank)"
    )

    interview_body = f"""_Completed {today} via spec-interview wizard (human answers)._

**User and goal:**
{user_goal or "(not provided)"}

**Success looks like:**
{success or "(not provided)"}

**Most likely failure modes:**
1. {fail1 or "(not provided)"}
2. {fail2 or "(not provided)"}
3. {fail3 or "(not provided)"}

**Explicit out of scope:**
{out_scope or "(not provided)"}

**Existing patterns to follow:**
{patterns or "(none noted)"}

**Extra requirements / interview catch-alls:**
{extras or "(none)"}
"""

    original = spec_path.read_text(encoding="utf-8")
    updated = replace_interview_section(original, interview_body)

    if dry_run:
        print("\n--- dry run: would write ---\n")
        print(interview_body)
        return

    spec_path.write_text(updated, encoding="utf-8")
    print(f"\nOK — Interview notes updated in {spec_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fill SPEC.md Interview notes via interactive prompts.",
    )
    parser.add_argument("--feature", required=True, help="Feature slug (e.g. pixel-editor)")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print interview body only; do not write SPEC.md",
    )
    args = parser.parse_args()

    try:
        run_wizard(args.feature, args.root.resolve(), args.dry_run)
        return 0
    except AgentSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
