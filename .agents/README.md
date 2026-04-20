# Agent System Control Center

This directory contains the control-plane documents, state snapshot,
append-only artifacts, and helper tooling for the agent system.

## Structure

- `STATE.json` - Live machine-readable snapshot. The Orchestrator is the
  default sole writer.
- `updates/` - Append-only state update envelopes from non-orchestrator agents.
- `sessions/` - Per-session Markdown logs with YAML frontmatter.
- `gates/` - Per-attempt JSON gate artifacts.
- `scripts/` - Lightweight helper scripts for setup, hashes, runtime claims,
  update merges, validation, and demos.
- `schemas/` - JSON schemas documenting artifact formats.
- `ORCHESTRATOR.md`, `FEATURE_AGENT.md`, `VERIFIER_AGENT.md`,
  `INFRA_AND_DESIGN_AGENTS.md` - Role prompts.

Run `python .agents/scripts/validate-agent-artifacts.py` after changing
control-plane files or artifacts.
