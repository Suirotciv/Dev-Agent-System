from __future__ import annotations

"""
prompt-hash.py - Check or refresh prompt hashes in .agents/STATE.json.

Usage:
    python .agents/scripts/prompt-hash.py --check
    python .agents/scripts/prompt-hash.py --write-state --expected-revision N
"""

import argparse
import json
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts_dir))

from agent_helpers import (  # noqa: E402
    AgentSystemError,
    PROMPT_FILES,
    is_hex12,
    prompt_hash,
    read_state,
    repo_root,
    write_state,
)


def compute_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name, rel_path in PROMPT_FILES.items():
        path = root / rel_path
        if not path.exists():
            raise AgentSystemError(f"prompt file not found: {rel_path}")
        hashes[name] = prompt_hash(path)
    return hashes


def check_hashes(root: Path, state_path: str | None) -> tuple[bool, dict[str, dict[str, str]]]:
    state = read_state(state_path)
    actual = compute_hashes(root)
    recorded = state.get("prompt_versions", {})
    details: dict[str, dict[str, str]] = {}
    ok = True

    for name, actual_hash in actual.items():
        state_hash = str(recorded.get(name, ""))
        match = is_hex12(state_hash) and state_hash == actual_hash
        ok = ok and match
        details[name] = {
            "state": state_hash,
            "current": actual_hash,
            "status": "ok" if match else "drift",
        }

    return ok, details


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or refresh .agents prompt hashes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Check STATE.json hashes")
    mode.add_argument("--write-state", action="store_true", help="Write current hashes to STATE.json")
    parser.add_argument("--expected-revision", type=int, help="Required with --write-state")
    parser.add_argument("--root", help="Optional repo root path")
    parser.add_argument("--state", help="Optional path to STATE.json")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root()

    try:
        if args.check:
            ok, details = check_hashes(root, args.state)
            print(json.dumps({"prompt_hashes": details}, indent=2))
            return 0 if ok else 1

        if args.expected_revision is None:
            raise AgentSystemError("--expected-revision is required with --write-state")

        state = read_state(args.state)
        note = state.get("prompt_versions", {}).get("_note")
        state["prompt_versions"] = compute_hashes(root)
        if note:
            state["prompt_versions"]["_note"] = note
        updated = write_state(
            state,
            expected_revision=args.expected_revision,
            actor="prompt-hash",
            state_path=args.state,
        )
        print(
            json.dumps(
                {
                    "updated": "prompt_versions",
                    "state_revision": updated["_state_revision"],
                    "prompt_versions": updated["prompt_versions"],
                },
                indent=2,
            )
        )
        return 0
    except AgentSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
