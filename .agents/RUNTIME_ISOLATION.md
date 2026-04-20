# Runtime Isolation

Parallel agents can share files safely through git worktrees, but they also
need separate local runtime resources.

`allocate-runtime.py claim` assigns:

- `runtime_port`: first free port in 3100-3199 unless `--port` is provided.
- `test_db`: feature-specific test database name.
- `resource_claim_id`: unique claim identifier.
- `compose_project_name`: Docker Compose namespace.
- `cache_namespace`: cache key namespace.
- `worktree_path`: optional path passed by the orchestrator.

Release the bundle when the session is finished:

```bash
python .agents/scripts/allocate-runtime.py release feature-name --expected-revision <n>
```
