# AGENTS.md
# Agent System - Repository Instructions

This repository is a reusable agent-system template. Keep the root focused on
the template itself; project-specific examples live under `examples/`.

## Commands

```bash
# Validate the template control plane
python .agents/scripts/validate-agent-artifacts.py

# Check prompt hashes recorded in .agents/STATE.json
python .agents/scripts/prompt-hash.py --check

# Refresh prompt hashes after editing role prompts
python .agents/scripts/prompt-hash.py --write-state --expected-revision <n>

# Create a new project from this template
python .agents/scripts/new-project.py --name "My Project" --description "What it does"

# Scaffold a feature in a project that uses this template
python .agents/scripts/new-feature.py --name feature-name --issue 1

# Merge the newest pending envelope (solo workflow — no long filename)
python .agents/scripts/merge-updates.py --expected-revision <n> --latest

# Fill SPEC.md Interview notes via terminal prompts (no AI required)
python .agents/scripts/spec-interview.py --feature feature-name

# Run the beginner smoke demo
python .agents/scripts/demo-smoke.py

# Run tests
python -m unittest discover
```

## Repo Shape

- `.agents/` contains role prompts, state, schemas, scripts, sessions, gates,
  and update envelopes.
- `src/features/_template/` contains the feature-spec template used by the
  system and examples.
- `examples/task-app/` contains the TaskFlow example that demonstrates a real
  project state without confusing it with the template root.
- `tests/` contains stdlib-only regression tests for helper scripts.

## Safety

- Keep helper scripts stdlib-only unless the docs are updated with setup steps.
- Do not put application-specific live state in root `.agents/STATE.json`.
- Do not commit `.env` files.
- Run `python -m unittest discover` and
  `python .agents/scripts/validate-agent-artifacts.py` before calling the repo
  clean.
