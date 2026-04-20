# AGENTS.md
# TaskFlow - Agent Instructions
# Keep this file under 150 lines. Agents explore the repo for structure.
# Only what cannot be inferred from the codebase.

## Commands

```bash
# Development
npm run dev              # start dev server (default port 3000)
npm run build            # production build
npm run typecheck        # tsc --noEmit (must be zero errors)
npm run lint             # eslint + prettier check
npm run lint:fix         # auto-fix lint issues

# Testing
npm run test             # unit tests (Vitest)
npm run test:watch       # watch mode
npm run test:coverage    # coverage report (floor: 80% unit)
npm run test:integration # integration tests
npm run test:e2e         # Playwright E2E

# Database
npm run db:migrate       # run pending migrations
npm run db:seed          # seed dev data
```

## Non-Obvious Patterns

- Feature flags defined ONLY in `src/utils/flags.ts`. Never use raw env strings.
- All user-facing strings in `src/i18n/`. Never hardcode display text.
- API client is `src/api/client.ts`. Never fetch directly in components.
- Design tokens in `src/styles/tokens.css`. Never hardcode colors or spacing.
- Task creation and task list are separate features communicating via
  a `taskCreated` custom event - not through shared state or prop drilling.
- Optimistic updates: update local state immediately, confirm/rollback on API.
  Pattern in `src/features/task-list/useTaskList.ts`.

## Safety Constraints

NEVER:
- Commit `.env` files
- Edit another feature directory without a blocker logged
- Change `src/types/Task.ts` without a blocker and merged update

ALWAYS:
- Run `npm run typecheck` before marking any task complete
- Run `npm run test` before marking a feature ready for verification
- Write a session log in `.agents/sessions/`
- Use `.agents/updates/` for state changes unless you are the Orchestrator

## Current Sprint Focus

See `.agents/STATE.json` -> `sprint` for current tasks.
Sprint 1.0 goal: ship core task creation and completion.

## File Ownership

| Path | Owner |
|------|-------|
| `src/types/`, `src/utils/`, `src/api/` | Core (file blockers to change) |
| `src/features/task-creation/` | feature-agent:task-creation |
| `src/features/task-completion/` | feature-agent:task-completion |
| `src/features/[name]/SPEC.md` | Orchestrator (Verifier appends "Failure patterns" only) |
| `tests/e2e/`, `tests/regression/` | Verifier Agent |
| `src/styles/tokens.css` | Design System Agent |
| `.agents/STATE.json` | Orchestrator (others submit update envelopes) |
