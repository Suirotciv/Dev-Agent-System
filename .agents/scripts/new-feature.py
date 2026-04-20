from __future__ import annotations

"""
new-feature.py - Scaffold a new feature from templates.

Creates src/features/[name]/SPEC.md and AGENTS.md with all placeholders
stamped, and emits an update envelope to add the feature to STATE.json.

Usage:
    python .agents/scripts/new-feature.py \\
        --name user-auth \\
        --issue 12 \\
        [--flag FLAGS.USER_AUTH] \\
        [--phase 1] \\
        [--quiet]

The feature is NOT added directly to STATE.json. An update envelope is
written to .agents/updates/ for the Orchestrator to merge. This keeps
the single-writer guarantee intact.
"""

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts_dir))

try:
    from agent_helpers import (
        AgentSystemError,
        generate_resource_claim_id,
        prompt_hash,
        read_state,
        slugify,
        write_json,
    )
except ImportError as exc:
    print(f"error: could not import agent_helpers: {exc}", file=sys.stderr)
    raise SystemExit(1)

_IS_TTY = sys.stdout.isatty()
BOLD  = "\033[1m"  if _IS_TTY else ""
GREEN = "\033[32m" if _IS_TTY else ""
CYAN  = "\033[36m" if _IS_TTY else ""
DIM   = "\033[2m"  if _IS_TTY else ""
YELLOW = "\033[33m" if _IS_TTY else ""
RESET = "\033[0m"  if _IS_TTY else ""


def ok(text: str) -> None:
    print(f"  {GREEN}OK{RESET} {text}")


def note(text: str) -> None:
    print(f"  {DIM}{text}{RESET}")


def warn(text: str) -> None:
    print(f"  {YELLOW}!{RESET} {text}")


def teach(text: str, quiet: bool) -> None:
    if quiet:
        return
    lines = text.strip().splitlines()
    print(f"\n  {DIM}+- PM note")
    for line in lines:
        print(f"  | {line}")
    print(f"  +-{RESET}")


def find_repo_root() -> Path:
    candidate = Path(__file__).resolve().parent
    for _ in range(8):
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
        candidate = candidate.parent
    return Path.cwd()


SPEC_TEMPLATE = """\
# SPEC.md - {feature_title}
# The Orchestrator owns acceptance criteria and status metadata in this file.
# The Verifier may append to "Failure patterns learned" only.
# Do not change criteria without Orchestrator approval.

---

## Identity

**Feature:** {feature_name}
**Phase:** Phase {phase}
**Issue:** #{issue}
**Branch:** feature/{feature_name}-#{issue}
**Flag:** `{flag}` (env: `{flag_env}`)
**Started:** {today}
**Current status:** see `.agents/STATE.json` -> `features.{feature_name}.status`

---

## Interview notes

_The Orchestrator runs a spec interview before writing acceptance criteria.
Record the answers here so the feature agent has full context on user intent._

**User and goal:**
(Who is this for? What are they trying to accomplish - not the technical solution.)

**Success looks like:**
(What does the user experience when this works correctly?)

**Most likely failure modes:**
1.
2.
3.

**Explicit out of scope:**
-

**Existing patterns to follow:**
-

---

## User Story

As a [type of user],
I want to [action],
So that [outcome/value].

---

## Acceptance Criteria

These are binary. Pass means observable, testable behavior.

### Functional (FUNCTIONAL gate)

- [ ] AC-01: [User can do X] - verified by: [test name or manual step]
- [ ] AC-02: [When Y happens, Z is shown] - verified by: [test name]
- [ ] AC-03: [Error state: when API fails, user sees message M] - test: [name]
- [ ] AC-04: [Empty state: when no data, shows empty state component] - test: [name]
- [ ] AC-05: [Loading state: spinner shown while fetching] - test: [name]
- [ ] AC-06: [Works on mobile viewport 375px] - tested via: [DevTools / device]

### Polish (SHIP_READY gate - added after FUNCTIONAL passes)

- [ ] AC-07: [Matches design reference at all breakpoints]
- [ ] AC-08: [Keyboard navigable - all actions reachable without mouse]
- [ ] AC-09: [Screen reader: announces state changes correctly]
- [ ] AC-10: [Color contrast passes 4.5:1]
- [ ] AC-11: [Copy approved by project owner]

---

## Out of Scope

- [Feature X] is NOT part of this feature - tracked separately
- [Edge case Y] is deferred - see PROJECT_CONTEXT.md

---

## API Contract

Input (from API / store):

```typescript
interface {feature_pascal}Input {{
  // define here
}}
```

Output (what user sees / what events are emitted):

```typescript
interface {feature_pascal}Output {{
  // define here
}}
```

---

## Test Plan

Unit tests required:
- [List specific behaviors that need unit tests]

Integration tests required:
- [Primary user flow: describe it]
- [Error flow: describe it]

E2E tests (written by Verifier):
- [Critical user journey this feature is part of]

---

## Design Reference

Design file: [Figma link | "not yet created" | "follows existing patterns"]
Key screens: [list screen names]
Deviations approved: [none | describe any approved deviation]

---

## Gate Sign-offs

| Gate | Date | Result | Signed By |
|------|------|--------|-----------|
| FUNCTIONAL | | | |
| SHIP_READY | | | |

---

## Failure patterns learned

Append-only. The Verifier may add entries here after failed gates so future
work converts failures into tests.

---

## Change Log

Append-only. Document any acceptance-criteria changes after work started.
"""


AGENTS_TEMPLATE = """\
# AGENTS.md - {feature_title}
# Feature-specific context for agents working on {feature_name}.
# Keep this file under 80 lines.
# Only include what cannot be inferred from reading the code.

## Feature Overview

**What it does:** [One sentence - what user action this enables]
**Status:** see `.agents/STATE.json` -> `features.{feature_name}.status`
**Spec / Acceptance criteria:** `SPEC.md` in this directory
**Flag:** `{flag}` (env: `{flag_env}`)
**Issue:** #{issue}

## Ownership Notes

- `SPEC.md` is orchestrator-owned for criteria and status metadata.
- The Verifier may append to `Failure patterns learned` only.
- Feature Agents own feature-local code and tests, not shared design tokens
  or core utilities.

## Non-Obvious Constraints

[List ONLY things an agent cannot infer from the code itself]

- [Example: This feature depends on [Service] which has a N req/min rate limit]
- [Example: [Component] mounts twice in StrictMode - the current effect is intentional]

## Files in This Feature

```text
{feature_name}/
  AGENTS.md
  SPEC.md
  index.ts
  {feature_pascal}.tsx
  {feature_pascal}.test.ts
  use{feature_pascal}.ts
  use{feature_pascal}.test.ts
  types.ts
  api.ts
```

## Known Gotchas

[Document things that HAVE gone wrong or are likely to trip up an agent]

## Do Not Touch From This Directory

- `src/types/` - file a blocker if you need a change
- `src/utils/flags.ts` - request through the orchestrator flow
- `src/styles/tokens.css` - Design System Agent owns this
- `src/features/[other-feature]/` - different feature's territory
"""


def pascal_case(slug: str) -> str:
    return "".join(word.capitalize() for word in slug.replace("-", "_").split("_"))


def flag_to_env(flag: str) -> str:
    """FLAGS.USER_AUTH -> FEATURE_USER_AUTH"""
    name = flag.replace("FLAGS.", "").strip()
    return f"FEATURE_{name}"


def scaffold_feature(
    *,
    feature_name: str,
    issue: int,
    flag: str,
    phase: int,
    root: Path,
    quiet: bool,
) -> None:
    feature_title = feature_name.replace("-", " ").title()
    feature_pascal = pascal_case(feature_name)
    flag_env = flag_to_env(flag)
    today = date.today().isoformat()

    values = {
        "feature_name":   feature_name,
        "feature_title":  feature_title,
        "feature_pascal": feature_pascal,
        "flag":           flag,
        "flag_env":       flag_env,
        "issue":          str(issue),
        "phase":          str(phase),
        "today":          today,
    }

    feature_dir = root / "src" / "features" / feature_name
    feature_dir.mkdir(parents=True, exist_ok=True)

    # -- Write SPEC.md --
    spec_path = feature_dir / "SPEC.md"
    if spec_path.exists():
        warn(f"SPEC.md already exists at {spec_path.relative_to(root)}")
        overwrite = input("  Overwrite? [y/N]: ").strip().lower() == "y"
        if not overwrite:
            note("Keeping existing SPEC.md")
        else:
            spec_path.write_text(SPEC_TEMPLATE.format(**values), encoding="utf-8")
            ok(f"Wrote {spec_path.relative_to(root)}")
    else:
        spec_path.write_text(SPEC_TEMPLATE.format(**values), encoding="utf-8")
        ok(f"Wrote {spec_path.relative_to(root)}")

    # -- Write AGENTS.md --
    agents_path = feature_dir / "AGENTS.md"
    if agents_path.exists():
        note(f"AGENTS.md already exists at {agents_path.relative_to(root)} - skipping")
    else:
        agents_path.write_text(AGENTS_TEMPLATE.format(**values), encoding="utf-8")
        ok(f"Wrote {agents_path.relative_to(root)}")

    # -- Emit update envelope --
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d-%H%M")
    dt_iso = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    update_id = f"UPD-{now.strftime('%Y%m%d-%H%M%S')}-new-feature-{feature_name}-01"

    # Read current state revision for the envelope
    state_path = root / ".agents" / "STATE.json"
    current_revision = 0
    try:
        state = read_state(state_path)
        current_revision = state.get("_state_revision", 0)
        prompt_ver = state.get("prompt_versions", {}).get("FEATURE_AGENT.md", "000000000000")
    except Exception:
        warn("Could not read STATE.json - using revision 0 and placeholder prompt version")
        prompt_ver = "000000000000"

    envelope = {
        "update_id":                 update_id,
        "submitted_at":              dt_iso,
        "submitted_by":              "new-feature-script",
        "role":                      "orchestrator",
        "_prompt_version":           prompt_ver,
        "_state_revision_at_start":  current_revision,
        "target_feature":            feature_name,
        "resource_claim_id":         None,
        "summary":                   f"Scaffold new feature '{feature_name}' (issue #{issue}).",
        "changes": [
            {
                "op":    "set",
                "path":  f"features.{feature_name}",
                "value": {
                    "status":              "BUILDING",
                    "spec_status":         "INTERVIEW_NEEDED",
                    "flag":                flag,
                    "agent":               None,
                    "started":             today,
                    "spec":                f"src/features/{feature_name}/SPEC.md",
                    "blockers":            [],
                    "notes":               "",
                    "runtime_port":        None,
                    "test_db":             None,
                    "worktree_path":       None,
                    "resource_claim_id":   None,
                    "compose_project_name": None,
                    "cache_namespace":     None,
                },
            },
            {
                "op":   "set",
                "path": f"flags.{flag}",
                "value": {
                    "env_var":     flag_env,
                    "description": f"Enables the {feature_title} feature",
                    "owner":       f"feature-agent:{feature_name}",
                    "status":      "CREATED",
                    "created":     today,
                    "remove_after": "TBD",
                    "environments": {
                        "development": False,
                        "staging":     False,
                        "production":  False,
                    },
                },
            },
        ],
    }

    updates_dir = root / ".agents" / "updates"
    updates_dir.mkdir(parents=True, exist_ok=True)
    envelope_path = updates_dir / f"{timestamp}-new-feature-{feature_name}.json"
    write_json(envelope_path, envelope)
    ok(f"Update envelope written: .agents/updates/{envelope_path.name}")

    teach(
        "Why is the feature behind a flag?\n"
        "\n"
        "  Feature flags decouple deployment from release. A feature can be\n"
        "  merged into the main branch (deployed) long before it is turned on\n"
        "  for users (released). This means:\n"
        "\n"
        "    - Smaller, safer merges (no giant 'feature branch' PRs)\n"
        "    - Easy rollback (flip the flag, not the deploy)\n"
        "    - The ability to test in production without affecting all users\n"
        "\n"
        "  The flag stays off until the feature passes the SHIP_READY gate.\n"
        "  After release, the flag is removed entirely - dead flags are tech debt.",
        quiet,
    )

    teach(
        "What is INTERVIEW_NEEDED?\n"
        "\n"
        "  Before writing acceptance criteria, the Orchestrator runs a short\n"
        "  interview with you to understand the *user's* goal - not the technical\n"
        "  solution. This might feel like extra process, but it consistently\n"
        "  reduces rework because it catches misunderstood requirements before\n"
        "  a single line of code is written.\n"
        "\n"
        "  Fill in the 'Interview notes' section of SPEC.md before asking\n"
        "  the Orchestrator to assign a feature agent. Change spec_status to\n"
        "  SPEC_APPROVED when the acceptance criteria are signed off.",
        quiet,
    )

    print(f"\n  {BOLD}Next steps for '{feature_name}':{RESET}")
    print(f"  1. Fill in the Interview notes section in {CYAN}src/features/{feature_name}/SPEC.md{RESET}")
    print(f"  2. Write acceptance criteria (AC-01 through AC-06 minimum)")
    print(f"  3. Ask the Orchestrator to merge the update envelope and assign a feature agent")
    print(f"     Command: {CYAN}python .agents/scripts/merge-updates.py "
          f"--expected-revision {current_revision} .agents/updates/{envelope_path.name}{RESET}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new feature from templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name",  required=True, help="Feature name slug (e.g. user-auth)")
    parser.add_argument("--issue", required=True, type=int, help="GitHub/linear issue number")
    parser.add_argument(
        "--flag",
        default=None,
        help="Feature flag constant (e.g. FLAGS.USER_AUTH). Derived from --name if omitted.",
    )
    parser.add_argument("--phase", type=int, default=1, help="Product phase (default: 1)")
    parser.add_argument("--quiet", action="store_true", help="Skip PM teaching explanations")
    parser.add_argument("--root",  help="Override repo root path")
    args = parser.parse_args()

    root = Path(args.root) if args.root else find_repo_root()
    feature_name = slugify(args.name)
    flag = args.flag or f"FLAGS.{feature_name.upper().replace('-', '_')}"

    print(f"\n{BOLD}Scaffolding feature: {feature_name}{RESET}\n")

    try:
        scaffold_feature(
            feature_name=feature_name,
            issue=args.issue,
            flag=flag,
            phase=args.phase,
            root=root,
            quiet=args.quiet,
        )
        return 0
    except AgentSystemError as exc:
        print(f"\n  {YELLOW}Error: {exc}{RESET}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Cancelled.{RESET}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
