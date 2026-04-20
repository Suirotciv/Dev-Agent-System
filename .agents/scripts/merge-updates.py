from __future__ import annotations

"""
merge-updates.py - Merge update envelopes into STATE.json with full validation.

Validates envelope structure AND semantic correctness before applying.
Detects and logs path conflicts when multiple envelopes touch the same key.

Usage:
    python .agents/scripts/merge-updates.py --expected-revision <n> [envelopes...]
    python .agents/scripts/merge-updates.py --expected-revision <n> --dry-run [envelopes...]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_helpers import (
    ALLOWED_ROLES,
    AgentSystemError,
    apply_change,
    is_hex12,
    load_json,
    read_state,
    write_state,
)

# ---------------------------------------------------------------------------
# Allowed status values for features
# ---------------------------------------------------------------------------

ALLOWED_FEATURE_STATUSES = {
    "BUILDING",
    "FUNCTIONAL",
    "VERIFIED",
    "SHIP_READY",
    "BLOCKED",
}

ALLOWED_SPEC_STATUSES = {
    "INTERVIEW_NEEDED",
    "INTERVIEW_DONE",
    "SPEC_APPROVED",
}

REQUIRED_KNOWN_ISSUE_FIELDS = {"id", "description", "owner", "priority", "opened"}
REQUIRED_GATE_SUMMARY_FIELDS = {"gate_attempt_id", "artifact", "gate", "date", "result"}


# ---------------------------------------------------------------------------
# Envelope structural validation
# ---------------------------------------------------------------------------

def validate_envelope_structure(envelope: dict[str, Any], path: Path) -> None:
    required = {
        "update_id",
        "submitted_at",
        "submitted_by",
        "role",
        "_prompt_version",
        "_state_revision_at_start",
        "target_feature",
        "resource_claim_id",
        "summary",
        "changes",
    }
    missing = sorted(required - envelope.keys())
    if missing:
        raise AgentSystemError(
            f"{path.name} is missing required fields: {', '.join(missing)}"
        )
    if envelope["role"] not in ALLOWED_ROLES:
        raise AgentSystemError(
            f"{path.name} has invalid role: {envelope['role']!r}"
        )
    if not isinstance(envelope["changes"], list) or not envelope["changes"]:
        raise AgentSystemError(
            f"{path.name} must include at least one change"
        )
    if not is_hex12(str(envelope["_prompt_version"])):
        raise AgentSystemError(
            f"{path.name} has invalid _prompt_version: "
            f"{envelope['_prompt_version']!r} (must be 12 hex chars)"
        )
    for index, change in enumerate(envelope["changes"], start=1):
        if not isinstance(change, dict):
            raise AgentSystemError(
                f"{path.name} change #{index} is not an object"
            )
        if change.get("op") not in {"set", "append"}:
            raise AgentSystemError(
                f"{path.name} change #{index} has invalid op: {change.get('op')!r}"
            )
        if not isinstance(change.get("path"), str) or not change["path"]:
            raise AgentSystemError(
                f"{path.name} change #{index} needs a non-empty path"
            )


# ---------------------------------------------------------------------------
# Semantic validation (checks against STATE.json content)
# ---------------------------------------------------------------------------

def validate_envelope_semantics(
    envelope: dict[str, Any],
    state: dict[str, Any],
    path: Path,
) -> list[str]:
    """
    Validate semantic correctness of changes against current state.
    Returns a list of warning strings (non-fatal issues).
    Raises AgentSystemError for fatal semantic errors.
    """
    warnings: list[str] = []
    features = state.get("features", {})

    for idx, change in enumerate(envelope["changes"], start=1):
        op = change["op"]
        change_path: str = change["path"]
        value = change.get("value")

        # -- features.[name].status --
        if change_path.startswith("features.") and change_path.endswith(".status"):
            parts = change_path.split(".")
            if len(parts) == 3:
                feature_name = parts[1]
                # Feature must already exist unless this is a set on the full feature key
                if feature_name not in features:
                    raise AgentSystemError(
                        f"{path.name} change #{idx}: cannot set status on "
                        f"non-existent feature '{feature_name}'. "
                        f"Create the feature entry first."
                    )
                if value not in ALLOWED_FEATURE_STATUSES:
                    raise AgentSystemError(
                        f"{path.name} change #{idx}: invalid feature status "
                        f"{value!r}. Allowed: {sorted(ALLOWED_FEATURE_STATUSES)}"
                    )

        # -- features.[name].spec_status --
        if change_path.startswith("features.") and change_path.endswith(".spec_status"):
            if op == "set" and value not in ALLOWED_SPEC_STATUSES:
                raise AgentSystemError(
                    f"{path.name} change #{idx}: invalid spec_status "
                    f"{value!r}. Allowed: {sorted(ALLOWED_SPEC_STATUSES)}"
                )

        # -- features.[name] (setting entire feature entry) --
        if change_path.startswith("features.") and change_path.count(".") == 1:
            feature_name = change_path.split(".")[1]
            if feature_name.startswith("_"):
                warnings.append(
                    f"Change #{idx} sets a metadata key ('{feature_name}') - "
                    f"this is unusual."
                )
            if op == "set" and isinstance(value, dict):
                status = value.get("status")
                if status and status not in ALLOWED_FEATURE_STATUSES:
                    raise AgentSystemError(
                        f"{path.name} change #{idx}: new feature entry has "
                        f"invalid status {status!r}"
                    )

        # -- known_issues append --
        if change_path == "known_issues" and op == "append":
            if not isinstance(value, dict):
                raise AgentSystemError(
                    f"{path.name} change #{idx}: known_issues append value "
                    f"must be an object"
                )
            missing = REQUIRED_KNOWN_ISSUE_FIELDS - value.keys()
            if missing:
                raise AgentSystemError(
                    f"{path.name} change #{idx}: known_issues entry is missing "
                    f"fields: {sorted(missing)}"
                )
            issue_id = value.get("id", "")
            if issue_id and not str(issue_id).startswith("ISSUE-"):
                raise AgentSystemError(
                    f"{path.name} change #{idx}: known_issues id must start "
                    f"with 'ISSUE-', got {issue_id!r}"
                )

        # -- gates.[feature] append --
        if change_path.startswith("gates.") and op == "append":
            if not isinstance(value, dict):
                raise AgentSystemError(
                    f"{path.name} change #{idx}: gates append value must be an object"
                )
            missing = REQUIRED_GATE_SUMMARY_FIELDS - value.keys()
            if missing:
                warnings.append(
                    f"Change #{idx}: gates entry is missing recommended "
                    f"fields: {sorted(missing)}"
                )

    return warnings


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def detect_conflicts(
    envelopes: list[tuple[Path, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Find cases where two envelopes both `set` the same dotted path.
    Returns a list of conflict records. Does not raise - conflicts are
    resolved by last-submitted-at timestamp.
    """
    seen: dict[str, tuple[str, str]] = {}  # path -> (envelope filename, submitted_at)
    conflicts: list[dict[str, Any]] = []

    for path, envelope in envelopes:
        submitted_at = envelope.get("submitted_at", "")
        for change in envelope["changes"]:
            if change["op"] != "set":
                continue
            change_path = change["path"]
            if change_path in seen:
                prev_name, prev_time = seen[change_path]
                winner = path.name if submitted_at >= prev_time else prev_name
                conflicts.append(
                    {
                        "path":          change_path,
                        "envelope_1":    prev_name,
                        "envelope_2":    path.name,
                        "winner":        winner,
                        "detected_at":   datetime.now(timezone.utc).isoformat(),
                    }
                )
            seen[change_path] = (path.name, submitted_at)

    return conflicts


# ---------------------------------------------------------------------------
# Duplicate update_id check
# ---------------------------------------------------------------------------

def check_duplicate_update_ids(
    envelopes: list[tuple[Path, dict[str, Any]]],
    state: dict[str, Any],
) -> None:
    """Raise if any envelope's update_id has already been merged."""
    merged_ids: set[str] = set(state.get("_merged_update_ids", []))
    incoming_ids: dict[str, str] = {}

    for path, envelope in envelopes:
        uid = envelope.get("update_id", "")
        if uid in merged_ids:
            raise AgentSystemError(
                f"{path.name} has already been merged (duplicate update_id: {uid!r}). "
                f"This envelope is being re-submitted. Remove it from .agents/updates/ "
                f"or generate a new update_id."
            )
        if uid in incoming_ids:
            raise AgentSystemError(
                f"Duplicate update_id {uid!r} in two envelopes being merged "
                f"simultaneously: {incoming_ids[uid]} and {path.name}"
            )
        if uid:
            incoming_ids[uid] = path.name


# ---------------------------------------------------------------------------
# Main merge logic
# ---------------------------------------------------------------------------

def merge(
    state: dict[str, Any],
    envelopes: list[tuple[Path, dict[str, Any]]],
    dry_run: bool,
    verbose: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Apply all envelope changes to a copy of state.
    Envelopes are sorted by submitted_at so last-write-wins is deterministic.
    Returns (updated_state, conflicts).
    """
    import copy

    merged = copy.deepcopy(state)

    # Sort by submitted_at so conflict resolution is deterministic
    sorted_envelopes = sorted(
        envelopes,
        key=lambda pair: pair[1].get("submitted_at", ""),
    )

    conflicts = detect_conflicts(sorted_envelopes)

    if conflicts and verbose:
        print(
            f"  warning: {len(conflicts)} path conflict(s) detected - "
            f"last submitted_at wins",
            file=sys.stderr,
        )
        for c in conflicts:
            print(
                f"    {c['path']}: {c['envelope_1']} vs {c['envelope_2']} "
                f"-> {c['winner']} wins",
                file=sys.stderr,
            )

    for path, envelope in sorted_envelopes:
        for change in envelope["changes"]:
            apply_change(merged, change)

    # Record merged update IDs for idempotency
    existing_ids = merged.get("_merged_update_ids", [])
    new_ids = [env.get("update_id", "") for _, env in envelopes if env.get("update_id")]
    merged["_merged_update_ids"] = list(set(existing_ids) | set(new_ids))

    # Record conflicts
    if conflicts:
        merged["_conflicts"] = merged.get("_conflicts", []) + conflicts

    return merged, conflicts


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge update envelopes into STATE.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--state",             help="Optional path to STATE.json")
    parser.add_argument("--expected-revision", type=int, required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and apply updates in memory without writing STATE.json",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress warnings (errors still shown)",
    )
    parser.add_argument("updates", nargs="+", help="One or more update envelope paths")
    args = parser.parse_args()
    verbose = not args.quiet

    try:
        state = read_state(args.state)

        # Load and validate all envelopes before applying any
        loaded: list[tuple[Path, dict[str, Any]]] = []
        for raw_path in args.updates:
            path = Path(raw_path)
            envelope = load_json(path)
            validate_envelope_structure(envelope, path)
            warnings = validate_envelope_semantics(envelope, state, path)
            if warnings and verbose:
                for w in warnings:
                    print(f"  warning ({path.name}): {w}", file=sys.stderr)
            loaded.append((path, envelope))

        # Check for duplicate update IDs
        check_duplicate_update_ids(loaded, state)

        # Merge
        merged, conflicts = merge(state, loaded, dry_run=args.dry_run, verbose=verbose)

        if not args.dry_run:
            write_state(
                merged,
                expected_revision=args.expected_revision,
                actor="orchestrator",
                state_path=args.state,
            )

        result = {
            "merged_updates":       [str(p) for p, _ in loaded],
            "state_revision_before": args.expected_revision,
            "state_revision_after": (
                args.expected_revision if args.dry_run
                else args.expected_revision + 1
            ),
            "dry_run":    args.dry_run,
            "conflicts":  len(conflicts),
        }
        print(json.dumps(result, indent=2))
        return 0

    except AgentSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
