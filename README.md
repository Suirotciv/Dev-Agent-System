# Dev-Agent-System

A reusable **agent coordination template**: shared `.agents/STATE.json`, role prompts, append-only session and gate artifacts, and **stdlib-only Python** helpers so you can validate and scaffold without extra dependencies.

## Quick start

```bash
git clone https://github.com/Suirotciv/Dev-Agent-System.git
cd Dev-Agent-System

python .agents/scripts/bootstrap.py
# or non-interactive:
python .agents/scripts/new-project.py --name "My App" --description "What it does" --output-dir ../my-app

python -m unittest discover
python .agents/scripts/validate-agent-artifacts.py
python .agents/scripts/demo-smoke.py
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | First-day walkthrough |
| [AGENTS.md](AGENTS.md) | Repo commands and layout |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Roles, flow, defaults |
| [MODELS.md](MODELS.md) | Model / context requirements |
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Template identity and decisions |

Example project state (TaskFlow sample): [examples/task-app/](examples/task-app/).

## Requirements

- **Python 3.9+** (helpers use the standard library only)
- **Git** recommended (worktrees, hooks)

## License

MIT — see [LICENSE](LICENSE).
