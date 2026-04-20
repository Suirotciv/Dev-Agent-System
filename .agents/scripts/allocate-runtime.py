from __future__ import annotations

"""
allocate-runtime.py - Claim or release local runtime bundles for parallel agents.

Usage:
    python .agents/scripts/allocate-runtime.py claim feature-name --expected-revision N
    python .agents/scripts/allocate-runtime.py release feature-name --expected-revision N
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts_dir))

from agent_helpers import (  # noqa: E402
    AgentSystemError,
    generate_resource_claim_id,
    read_state,
    slugify,
    write_state,
)

RUNTIME_FIELDS = (
    "runtime_port",
    "test_db",
    "resource_claim_id",
    "compose_project_name",
    "cache_namespace",
)


def used_ports(features: dict[str, Any], feature_to_skip: str) -> set[int]:
    ports: set[int] = set()
    for name, entry in features.items():
        if name == feature_to_skip or name.startswith("_") or not isinstance(entry, dict):
            continue
        port = entry.get("runtime_port")
        if isinstance(port, int):
            ports.add(port)
    return ports


def first_available_port(features: dict[str, Any], feature_name: str) -> int:
    used = used_ports(features, feature_name)
    for port in range(3100, 3200):
        if port not in used:
            return port
    raise AgentSystemError("no runtime ports available in range 3100-3199")


def runtime_is_empty(feature: dict[str, Any]) -> bool:
    return all(feature.get(field) is None for field in RUNTIME_FIELDS)


def runtime_is_complete(feature: dict[str, Any]) -> bool:
    return all(feature.get(field) is not None for field in RUNTIME_FIELDS)


def claim_runtime(
    state: dict[str, Any],
    feature_name: str,
    *,
    requested_port: int | None,
    worktree_path: str | None,
) -> dict[str, Any]:
    features = state.get("features")
    if not isinstance(features, dict) or feature_name not in features:
        raise AgentSystemError(f"feature not found in STATE.json: {feature_name}")

    feature = features[feature_name]
    if not isinstance(feature, dict):
        raise AgentSystemError(f"feature entry is not an object: {feature_name}")
    if runtime_is_complete(feature):
        raise AgentSystemError(f"feature already has a runtime bundle: {feature_name}")
    if not runtime_is_empty(feature):
        raise AgentSystemError(f"feature has a partial runtime bundle: {feature_name}")

    if requested_port is None:
        port = first_available_port(features, feature_name)
    else:
        if requested_port < 3100 or requested_port > 3199:
            raise AgentSystemError("--port must be within 3100-3199")
        if requested_port in used_ports(features, feature_name):
            raise AgentSystemError(f"runtime port already in use: {requested_port}")
        port = requested_port

    slug = slugify(feature_name)
    feature["runtime_port"] = port
    feature["test_db"] = f"agent_{slug.replace('-', '_')}_test"
    feature["resource_claim_id"] = generate_resource_claim_id(slug)
    feature["compose_project_name"] = f"agent_{slug}_{port}".replace("-", "_")
    feature["cache_namespace"] = f"agent:{slug}:{port}"
    feature["worktree_path"] = worktree_path
    return feature


def release_runtime(state: dict[str, Any], feature_name: str) -> dict[str, Any]:
    features = state.get("features")
    if not isinstance(features, dict) or feature_name not in features:
        raise AgentSystemError(f"feature not found in STATE.json: {feature_name}")

    feature = features[feature_name]
    if not isinstance(feature, dict):
        raise AgentSystemError(f"feature entry is not an object: {feature_name}")

    for field in RUNTIME_FIELDS:
        feature[field] = None
    feature["worktree_path"] = None
    return feature


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Claim or release an agent runtime bundle.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("action", choices=["claim", "release"])
    parser.add_argument("feature", help="Feature slug in STATE.json")
    parser.add_argument("--expected-revision", type=int, required=True)
    parser.add_argument("--state", help="Optional path to STATE.json")
    parser.add_argument("--port", type=int, help="Requested runtime port, 3100-3199")
    parser.add_argument("--worktree-path", help="Optional feature worktree path")
    parser.add_argument("--dry-run", action="store_true", help="Print result without writing STATE.json")
    args = parser.parse_args()

    try:
        state = read_state(args.state)
        feature_name = slugify(args.feature)

        if args.action == "claim":
            feature = claim_runtime(
                state,
                feature_name,
                requested_port=args.port,
                worktree_path=args.worktree_path,
            )
        else:
            feature = release_runtime(state, feature_name)

        if not args.dry_run:
            updated = write_state(
                state,
                expected_revision=args.expected_revision,
                actor="allocate-runtime",
                state_path=args.state,
            )
            revision = updated["_state_revision"]
        else:
            revision = args.expected_revision

        print(
            json.dumps(
                {
                    "action": args.action,
                    "feature": feature_name,
                    "state_revision": revision,
                    "runtime": {field: feature.get(field) for field in (*RUNTIME_FIELDS, "worktree_path")},
                    "dry_run": args.dry_run,
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
