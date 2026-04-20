# Helper Scripts

These scripts keep the agent system lightweight and operational.

## Scripts

- `bootstrap.py` - interactive project setup wizard.
- `new-project.py` - non-interactive project template stamper.
- `new-feature.py` - scaffold a feature spec and update envelope.
- `prompt-hash.py` - check or refresh prompt hashes in `STATE.json`.
- `allocate-runtime.py` - claim or release a local runtime bundle.
- `merge-updates.py` - merge update envelopes into `STATE.json`.
- `validate-agent-artifacts.py` - validate state and append-only artifacts.
- `demo-smoke.py` - run a disposable beginner workflow demo.

## Typical Usage

```bash
python .agents/scripts/prompt-hash.py --check
python .agents/scripts/prompt-hash.py --write-state --expected-revision 1
python .agents/scripts/allocate-runtime.py claim user-auth --expected-revision 2
python .agents/scripts/merge-updates.py --expected-revision 3 .agents/updates/example.json
python .agents/scripts/validate-agent-artifacts.py
python .agents/scripts/demo-smoke.py
```
