from __future__ import annotations

"""
validate-agent-artifacts.py - Validate all agent-system control-plane artifacts.

Checks STATE.json, session logs, gate artifacts, and update envelopes for
structural and semantic correctness. Run after every change to .agents/.

Usage:
    python .agents/scripts/validate-agent-artifacts.py [--root PATH] [--state PATH]
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from agent_helpers import (
    ALLOWED_ROLES,
    AgentSystemError,
    GATE_FILE_RE,
    PROMPT_FILES,
    SESSION_FILE_RE,
    UPDATE_FILE_RE,
    is_hex12,
    is_template_key,
    list_artifact_files,
    load_json,
    parse_frontmatter,
    parse_iso_datetime,
    prompt_hash,
    read_state,
    repo_root,
)


def fail(message: str) -> None:
    raise AgentSystemError(message)


def warn(message: str) -> None:
    """Non-fatal warning - printed but does not cause exit code 1."""
    print(f"  warning: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# STATE.json validation
# ---------------------------------------------------------------------------

def validate_state(root: Path, state_path: str | None) -> list[str]:
    resolved_state = state_path if state_path else root / ".agents" / "STATE.json"
    state = read_state(resolved_state)

    # -- Required top-level keys --
    required_top_level = {
        "_updated", "_updated_by", "_state_revision", "prompt_versions",
        "project", "sprint", "task_tree", "core_stability", "features",
        "gates", "blockers", "design_requests", "do_not_break", "known_issues",
    }
    missing = sorted(required_top_level - state.keys())
    if missing:
        fail(f"STATE.json is missing keys: {', '.join(missing)}")

    if not isinstance(state["_state_revision"], int) or state["_state_revision"] < 0:
        fail("_state_revision must be a non-negative integer")

    # -- Prompt hash verification (hard error) --
    prompt_versions = state["prompt_versions"]
    for name, relative_path in PROMPT_FILES.items():
        value = prompt_versions.get(name)
        if not isinstance(value, str) or not is_hex12(value):
            fail(
                f"prompt_versions.{name} must be a non-blank 12-char hex hash. "
                f"Run: python .agents/scripts/prompt-hash.py --write-state "
                f"--expected-revision {state['_state_revision']}"
            )
        actual = prompt_hash(root / relative_path)
        if actual != value:
            fail(
                f"prompt_versions.{name} is out of date: "
                f"state has {value}, current file hash is {actual}. "
                f"Run: python .agents/scripts/prompt-hash.py --write-state "
                f"--expected-revision {state['_state_revision']}"
            )

    # -- Feature entry validation --
    features = state.get("features", {})
    today = date.today()
    sprint_phases = {1, 2, 3}  # extend if needed

    for name, feature in features.items():
        if not isinstance(feature, dict) or is_template_key(name) or name.startswith("_"):
            continue

        # Runtime bundle consistency
        runtime_values = [
            feature.get("runtime_port"),
            feature.get("test_db"),
            feature.get("resource_claim_id"),
            feature.get("compose_project_name"),
            feature.get("cache_namespace"),
        ]
        if any(v is not None for v in runtime_values):
            if not all(v is not None for v in runtime_values):
                fail(f"features.{name} has a partial runtime bundle")
            if not isinstance(feature["runtime_port"], int) or not 3100 <= feature["runtime_port"] <= 3199:
                fail(f"features.{name}.runtime_port must be within 3100-3199")

        # BUILDING without a flag is a policy violation
        status = feature.get("status", "")
        flag = feature.get("flag")
        if status == "BUILDING" and not flag:
            warn(
                f"features.{name} has status BUILDING but no flag entry. "
                f"Features under active development should be behind a flag."
            )

        # Stale BUILDING detection (> 60 days)
        started = feature.get("started")
        if status == "BUILDING" and started and not is_template_key(started):
            try:
                started_date = date.fromisoformat(started)
                age_days = (today - started_date).days
                if age_days > 60:
                    warn(
                        f"features.{name} has been BUILDING for {age_days} days "
                        f"(started {started}). Consider breaking it down or marking BLOCKED."
                    )
            except ValueError:
                pass  # non-parseable date - skip stale check

        # spec_status validation
        spec_status = feature.get("spec_status")
        valid_spec_statuses = {
            "INTERVIEW_NEEDED", "INTERVIEW_DONE", "SPEC_APPROVED", None,
        }
        if spec_status not in valid_spec_statuses and not is_template_key(str(spec_status)):
            fail(
                f"features.{name}.spec_status has invalid value {spec_status!r}. "
                f"Allowed: INTERVIEW_NEEDED, INTERVIEW_DONE, SPEC_APPROVED"
            )

    # -- known_issues validation --
    known_issue_ids: set[str] = set()
    for item in state.get("known_issues", []):
        if not isinstance(item, dict):
            fail("known_issues entries must be objects")
        issue_id = item.get("id")
        if isinstance(issue_id, str) and not is_template_key(issue_id):
            if not issue_id.startswith("ISSUE-"):
                fail(f"known issue ID has invalid format: {issue_id!r} (must start with ISSUE-)")
            known_issue_ids.add(issue_id)

    # -- blocker validation --
    for blocker_id, blocker in state.get("blockers", {}).items():
        if blocker_id.startswith("_") or is_template_key(blocker_id):
            continue
        if not blocker_id.startswith("BLOCKER-"):
            fail(f"blocker ID has invalid format: {blocker_id!r} (must start with BLOCKER-)")
        if not isinstance(blocker, dict):
            fail(f"{blocker_id} must be an object")

    # -- design_requests validation --
    for request in state.get("design_requests", {}).get("items", []):
        if not isinstance(request, dict):
            fail("design request entries must be objects")
        request_id = request.get("id")
        if request_id is not None and not str(request_id).startswith("DESIGN-REQ-"):
            fail(f"design request ID has invalid format: {request_id!r}")

    # -- task_tree validation --
    for node in state.get("task_tree", {}).get("nodes", []):
        node_id = node.get("id")
        if node_id is not None and not str(node_id).startswith("TASK-"):
            fail(f"task node ID has invalid format: {node_id!r}")

    return ["STATE.json", f"known_issue_ids_available: {sorted(known_issue_ids)}"]


# ---------------------------------------------------------------------------
# Session log validation
# ---------------------------------------------------------------------------

def validate_sessions(root: Path) -> list[str]:
    validated: list[str] = []
    for path in list_artifact_files(root / ".agents" / "sessions", ".md"):
        meta, _body = parse_frontmatter(path)
        required = {
            "session_id", "role", "feature", "_prompt_version",
            "_state_revision_at_start", "resource_claim_id",
            "started_at", "ended_at", "legacy",
        }
        missing = sorted(required - meta.keys())
        if missing:
            fail(f"{path.name} is missing session frontmatter keys: {', '.join(missing)}")

        if meta["role"] not in ALLOWED_ROLES:
            fail(f"{path.name} has invalid role: {meta['role']!r}")

        if not meta["legacy"]:
            if not SESSION_FILE_RE.fullmatch(path.name):
                fail(f"{path.name} does not match the per-session filename format")
            if not is_hex12(str(meta["_prompt_version"])):
                fail(f"{path.name} must use a 12-char hex _prompt_version")
        else:
            if "legacy" not in path.name:
                fail(f"{path.name} is marked legacy but filename does not say so")
            if not str(meta["_prompt_version"]).strip():
                fail(f"{path.name} legacy note still needs a non-blank _prompt_version")

        parse_iso_datetime(str(meta["started_at"]))
        parse_iso_datetime(str(meta["ended_at"]))

        if not isinstance(meta["_state_revision_at_start"], int):
            fail(f"{path.name} _state_revision_at_start must be an integer")

        # Context budget fields - optional but validated if present
        for budget_field in ("context_budget_start_percent", "context_budget_end_percent"):
            val = meta.get(budget_field)
            if val is not None:
                if not isinstance(val, int) or not 0 <= val <= 100:
                    fail(
                        f"{path.name} {budget_field} must be an integer 0-100, "
                        f"got {val!r}"
                    )

        validated.append(path.name)
    return validated


# ---------------------------------------------------------------------------
# Gate artifact validation
# ---------------------------------------------------------------------------

def validate_gate_artifacts(root: Path, known_issue_ids: set[str]) -> list[str]:
    validated: list[str] = []
    for path in list_artifact_files(root / ".agents" / "gates", ".json"):
        data = load_json(path)
        required = {
            "gate_attempt_id", "feature", "gate", "date", "result",
            "verified_by", "_prompt_version", "functional_subpasses",
            "criteria_results", "known_issue_ids", "failures",
        }
        missing = sorted(required - data.keys())
        if missing:
            fail(f"{path.name} is missing gate fields: {', '.join(missing)}")

        if not GATE_FILE_RE.fullmatch(path.name):
            fail(f"{path.name} does not match the gate artifact filename format")

        if not is_hex12(str(data["_prompt_version"])):
            fail(f"{path.name} has invalid _prompt_version")

        criteria = data["criteria_results"]
        if not isinstance(criteria, dict) or not criteria:
            fail(f"{path.name} must include non-empty criteria_results")

        for criterion_id, result in criteria.items():
            if not isinstance(result, dict):
                fail(f"{path.name} criterion {criterion_id} must be an object")
            if result.get("status") not in {"PASS", "FAIL", "DEFERRED", "N/A"}:
                fail(
                    f"{path.name} criterion {criterion_id} has invalid status: "
                    f"{result.get('status')!r}"
                )
            if not str(result.get("evidence", "")).strip():
                fail(f"{path.name} criterion {criterion_id} needs evidence")

        # Cross-reference known_issue_ids against STATE.json
        gate_issue_ids = data.get("known_issue_ids", [])
        if known_issue_ids:  # only check if we have the state loaded
            for issue_id in gate_issue_ids:
                if issue_id and not is_template_key(str(issue_id)):
                    if issue_id not in known_issue_ids:
                        warn(
                            f"{path.name} references unknown issue {issue_id!r} "
                            f"in known_issue_ids - not found in STATE.json"
                        )

        validated.append(path.name)
    return validated


# ---------------------------------------------------------------------------
# Update envelope validation
# ---------------------------------------------------------------------------

def validate_update_envelopes(root: Path) -> list[str]:
    validated: list[str] = []
    for path in list_artifact_files(root / ".agents" / "updates", ".json"):
        data = load_json(path)
        required = {
            "update_id", "submitted_at", "submitted_by", "role",
            "_prompt_version", "_state_revision_at_start", "target_feature",
            "resource_claim_id", "summary", "changes",
        }
        missing = sorted(required - data.keys())
        if missing:
            fail(f"{path.name} is missing update fields: {', '.join(missing)}")

        if not UPDATE_FILE_RE.fullmatch(path.name):
            fail(f"{path.name} does not match the update filename format")

        if data["role"] not in ALLOWED_ROLES:
            fail(f"{path.name} has invalid role: {data['role']!r}")

        if not is_hex12(str(data["_prompt_version"])):
            fail(f"{path.name} has invalid _prompt_version")

        if not isinstance(data["changes"], list) or not data["changes"]:
            fail(f"{path.name} must include at least one change")

        validated.append(path.name)
    return validated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate agent-system artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root",  help="Optional repo root path")
    parser.add_argument("--state", help="Optional path to STATE.json")
    args = parser.parse_args()

    root = Path(args.root) if args.root else repo_root()

    try:
        state_result = validate_state(root, args.state)

        # Extract known issue IDs for cross-reference in gate validation
        known_issue_ids: set[str] = set()
        for item in state_result:
            if item.startswith("known_issue_ids_available:"):
                raw = item.split(":", 1)[1].strip()
                # Parse the list repr
                try:
                    import ast
                    known_issue_ids = set(ast.literal_eval(raw))
                except Exception:
                    pass

        summary = {
            "state":   [s for s in state_result if not s.startswith("known_issue_ids")],
            "sessions": validate_sessions(root),
            "gates":    validate_gate_artifacts(root, known_issue_ids),
            "updates":  validate_update_envelopes(root),
        }
        print(json.dumps(summary, indent=2))
        return 0

    except AgentSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
