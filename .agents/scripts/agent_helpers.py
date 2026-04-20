from __future__ import annotations

import copy
import hashlib
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

PROMPT_FILES = {
    "ORCHESTRATOR.md": Path(".agents/ORCHESTRATOR.md"),
    "FEATURE_AGENT.md": Path(".agents/FEATURE_AGENT.md"),
    "VERIFIER_AGENT.md": Path(".agents/VERIFIER_AGENT.md"),
    "INFRA_AND_DESIGN_AGENTS.md": Path(".agents/INFRA_AND_DESIGN_AGENTS.md"),
}

ALLOWED_ROLES = {
    "orchestrator",
    "feature-agent",
    "verifier-agent",
    "infra-agent",
    "design-system-agent",
}

HEX12_RE = re.compile(r"^[0-9a-f]{12}$")
SESSION_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9-]+\.md$")
GATE_FILE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9-]+-(functional|ship_ready|release)\.json$"
)
UPDATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9-]+\.json$")


class AgentSystemError(RuntimeError):
    """Raised when an agent-system artifact is invalid."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_path(path: str | Path | None, default: Path) -> Path:
    return Path(path) if path is not None else default


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=destination.parent,
    ) as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
        temp_name = handle.name
    Path(temp_name).replace(destination)


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def prompt_hash(path: str | Path) -> str:
    text = Path(path).read_text(encoding="utf-8")
    normalized = normalize_text(text).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()[:12]


def read_state(state_path: str | Path | None = None) -> dict[str, Any]:
    return load_json(resolve_path(state_path, repo_root() / ".agents" / "STATE.json"))


def write_state(
    state: dict[str, Any],
    *,
    expected_revision: int,
    actor: str,
    state_path: str | Path | None = None,
) -> dict[str, Any]:
    target = resolve_path(state_path, repo_root() / ".agents" / "STATE.json")
    current = load_json(target)
    current_revision = current.get("_state_revision")
    if current_revision != expected_revision:
        raise AgentSystemError(
            f"STATE revision mismatch: expected {expected_revision}, found {current_revision}"
        )

    updated = copy.deepcopy(state)
    updated["_state_revision"] = expected_revision + 1
    updated["_updated"] = datetime.now().date().isoformat()
    updated["_updated_by"] = actor
    write_json(target, updated)
    return updated


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return cleaned or "feature"


def generate_resource_claim_id(feature: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    shortid = hashlib.sha1(f"{feature}-{timestamp}".encode("utf-8")).hexdigest()[:6]
    return f"RC-{timestamp}-{slugify(feature)}-{shortid}"


def parse_iso_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def parse_frontmatter(path: str | Path) -> tuple[dict[str, Any], str]:
    text = Path(path).read_text(encoding="utf-8")
    normalized = normalize_text(text)
    if not normalized.startswith("---\n"):
        raise AgentSystemError(f"{path} is missing YAML frontmatter")
    try:
        _, frontmatter, body = normalized.split("---\n", 2)
    except ValueError as exc:
        raise AgentSystemError(f"{path} frontmatter is malformed") from exc

    data: dict[str, Any] = {}
    for raw_line in frontmatter.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise AgentSystemError(f"{path} frontmatter line is malformed: {raw_line}")
        key, value = line.split(":", 1)
        data[key.strip()] = parse_scalar(value.strip())
    return data, body


def parse_scalar(raw: str) -> Any:
    if raw in {"null", "~"}:
        return None
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    return raw


def is_template_key(key: str) -> bool:
    return key.startswith("[") and key.endswith("]")


def is_hex12(value: str) -> bool:
    return bool(HEX12_RE.fullmatch(value))


def dotted_parent(
    container: dict[str, Any],
    path: str,
    *,
    create: bool,
) -> tuple[dict[str, Any], str]:
    parts = path.split(".")
    current: Any = container
    for part in parts[:-1]:
        if not isinstance(current, dict):
            raise AgentSystemError(f"Non-object path segment while resolving {path}")
        if part not in current:
            if not create:
                raise AgentSystemError(f"Missing path in state: {path}")
            current[part] = {}
        current = current[part]
    if not isinstance(current, dict):
        raise AgentSystemError(f"Cannot assign through non-object path: {path}")
    return current, parts[-1]


def apply_change(container: dict[str, Any], change: dict[str, Any]) -> None:
    op = change.get("op")
    path = change.get("path")
    if op not in {"set", "append"}:
        raise AgentSystemError(f"Unsupported change op: {op}")
    if not isinstance(path, str) or not path:
        raise AgentSystemError("Change path must be a non-empty string")

    parent, leaf = dotted_parent(container, path, create=True)
    if op == "set":
        parent[leaf] = change.get("value")
        return

    if leaf not in parent:
        parent[leaf] = []
    target = parent[leaf]
    if not isinstance(target, list):
        raise AgentSystemError(f"Append target is not a list: {path}")
    target.append(change.get("value"))


def list_artifact_files(directory: Path, suffix: str) -> list[Path]:
    files: list[Path] = []
    if not directory.exists():
        return files
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.name in {"README.md", ".gitkeep"}:
            continue
        if path.suffix != suffix:
            continue
        files.append(path)
    return files
