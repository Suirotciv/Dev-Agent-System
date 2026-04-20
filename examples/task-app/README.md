# TaskFlow Example

This example preserves the TaskFlow improvements without making the template
root look like a real npm app.

It demonstrates:

- A project-specific `.agents/STATE.json`.
- A completed `task-creation` feature spec and gate artifact.
- A `task-completion` feature spec still in BUILDING.
- Session logs and update envelopes from an example agent workflow.

For beginners, the executable demo is:

```bash
python .agents/scripts/demo-smoke.py
```

That smoke demo creates a fresh temporary project, scaffolds a feature, dry-runs
an update merge, and validates artifacts. This TaskFlow folder is a richer
reference you can read after the smoke demo makes the loop feel concrete.
