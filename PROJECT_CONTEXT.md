# PROJECT_CONTEXT.md

## 1. Identity

**Project:** Agent System Template
**Version:** 0.1.0
**Status:** Pre-Alpha

This repository provides a lightweight coordination layer for AI coding agents.
It is meant to be copied into a real application repo, then used to coordinate
orchestrator, feature, verifier, infra, and design-system sessions through a
shared `.agents/STATE.json` file.

## 2. Audience

The primary audience is a solo developer or small team trying agent workflows
for the first time. The system should feel explicit, inspectable, and easy to
repair by hand.

## 3. Product Goal

Help developers split agent work into clear roles, preserve decisions across
sessions, and verify features without requiring a heavy framework.

## 4. Technology

- Helper scripts: Python 3.9+ stdlib only.
- Application stack: supplied by the project that adopts this template.
- Version control: Git is recommended for hooks and history, but the core
  scripts can be inspected and tested without Git on PATH.

## 5. Release Gate Checklist

- Helper scripts compile.
- `python -m unittest discover` passes.
- `python .agents/scripts/validate-agent-artifacts.py` passes.
- `python .agents/scripts/demo-smoke.py` passes.
- Docs reference files and commands that exist.

## 6. Current Process Decisions

- Root `.agents/STATE.json` describes the template, not an example app.
- Example app state lives under `examples/task-app/.agents/`.
- Session logs, update envelopes, and gate artifacts are append-only.
- Non-orchestrator agents submit update envelopes instead of editing state.

## 7. Examples

`examples/task-app/` contains the TaskFlow sample project with task-creation
and task-completion feature specs.

## 8. Out Of Scope

- Shipping a real TaskFlow web app from the template root.
- Adding npm, pytest, or packaging requirements before the stdlib workflow is
  healthy.

## 9. Key Decisions

- Prefer simple JSON/Markdown artifacts over databases.
- Prefer deterministic helper scripts over hidden agent memory.
- Prefer executable smoke demos over screenshots or marketing-style examples.

## 10. Known Risks

- Prompt hash drift must be refreshed whenever role prompts change.
- Artifact schemas are intentionally lightweight and should stay readable.

## 11. Human Notes

Use this file for durable project context. Use `.agents/STATE.json` for current
work state.
