# AGENTS.md - Task Creation
# Feature-specific context for agents working on task-creation.
# Keep under 80 lines. Only what cannot be inferred from reading the code.

## Feature Overview

**What it does:** Lets users add a new task by typing a title and pressing Enter.
**Status:** see `.agents/STATE.json` -> `features.task-creation.status`
**Spec:** `SPEC.md` in this directory
**Flag:** `FLAGS.TASK_CREATION` (env: `FEATURE_TASK_CREATION`)
**Issue:** #3

## Ownership Notes

- `SPEC.md` is orchestrator-owned. Verifier may only append to "Failure patterns learned".
- This feature agent owns everything in `src/features/task-creation/`.
- Shared task types live in `src/types/Task.ts` - file a blocker to change them.

## Non-Obvious Constraints

- The task list is rendered by the `task-list` feature (separate directory).
  This feature only handles creation. It emits a `taskCreated` event that the
  list feature listens to - do not render the list from here.
- The API uses optimistic updates: append the new task to local state immediately
  on submit, then confirm or rollback on API response. This is the pattern used
  in `src/features/task-list/useTaskList.ts` - follow it exactly.
- `FLAGS.TASK_CREATION` is also checked server-side on the `/api/tasks POST`
  route. Sending a request with the flag off returns 404, not 403. This is
  intentional - the endpoint should not be discoverable when the flag is off.

## Files in This Feature

```text
task-creation/
  AGENTS.md
  SPEC.md
  index.ts
  TaskCreationForm.tsx
  TaskCreationForm.test.ts
  useTaskCreation.ts
  useTaskCreation.test.ts
  types.ts
  api.ts
```

## Known Gotchas

- Whitespace-only validation: trim BEFORE the non-empty check, not after.
  `"   ".trim().length === 0` is the correct guard. See ISSUE-001 in STATE.json.
- The Add button must be `type="submit"` not `type="button"` - otherwise
  Enter key submission does not work in all browsers.
- Do NOT use `autofocus` HTML attribute - it breaks in React StrictMode
  (double-mount fires the focus twice and then loses it). Use a `useEffect`
  with `inputRef.current?.focus()` instead.

## Good Examples to Follow

- Optimistic update pattern: `src/features/task-list/useTaskList.ts`
- Error state + loading state: `src/features/user-profile/UserProfileForm.tsx`
- API error handling with retry: `src/features/user-profile/api.ts`

## Do Not Touch From This Directory

- `src/types/Task.ts` - file a BLOCKER if you need a change
- `src/utils/flags.ts` - request through orchestrator
- `src/styles/tokens.css` - Design System Agent owns this
- `src/features/task-list/` - separate feature's territory
