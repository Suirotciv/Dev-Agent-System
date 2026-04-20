# SPEC.md - Task Completion
# The Orchestrator owns acceptance criteria and status metadata in this file.
# The Verifier may append to "Failure patterns learned" only.

---

## Identity

**Feature:** task-completion
**Phase:** Phase 1
**Issue:** #5
**Branch:** feature/task-completion-#5
**Flag:** `FLAGS.TASK_COMPLETION` (env: `FEATURE_TASK_COMPLETION`)
**Started:** 2026-04-19
**Current status:** see `.agents/STATE.json` -> `features.task-completion.status`
**Spec status:** SPEC_APPROVED

---

## Interview Notes

_Completed 2026-04-19 by Orchestrator + human operator._

**Who is the user and what are they trying to accomplish?**
Same user as task creation - a developer or small team member working through
their task list. They have completed a task and want to mark it done so it
stops demanding their attention. The act of marking something complete is also
psychologically satisfying - the UI should make that moment feel good, not
clinical.

**What does success look like from the user's perspective?**
They click a checkbox next to a task. The task visually dims or gets a
strikethrough. It stays visible in the list (so they can see what they
accomplished) but is clearly distinguished from remaining tasks. The change
persists if they reload the page.

**Most likely failure modes:**
1. The visual change happens but the API call fails silently - the task
   looks done but reverts on reload.
2. Clicking the checkbox is too small a tap target on mobile - users
   accidentally miss it and nothing happens.
3. Completed tasks become invisible or get moved to a separate section
   immediately, which feels jarring and makes users feel like they "lost" the task.

**Explicit out of scope:**
- Uncompleting (un-checking) a task - tracked separately in issue #9
- Deleting completed tasks - Phase 2
- Filtering completed tasks out of the list - Phase 2
- Bulk completion - Phase 2

**Existing patterns to follow:**
- Optimistic update pattern from `task-creation` feature
- Checkbox component: use existing `src/components/shared/Checkbox.tsx`

---

## User Story

As a developer reviewing my task list,
I want to mark a task as complete by clicking a checkbox,
So that I can track my progress and focus on what remains.

---

## Acceptance Criteria

### Functional (FUNCTIONAL gate)

- [ ] AC-01: Clicking the checkbox next to a task marks it complete.
  Task title gets a CSS strikethrough. Task opacity reduces to 0.5.
  Change is visible within 100ms (optimistic update).
  Verified by: `task-completion.test.ts` -> "marks task complete on click"

- [ ] AC-02: Completion state persists - reloading the page shows the
  task still marked complete.
  Verified by: integration test -> "completion survives page reload"

- [ ] AC-03: If the API call fails (5xx), the optimistic update is rolled
  back. Task returns to uncompleted appearance. Inline error "Could not save -
  please try again" is shown near the task row.
  Verified by: `task-completion.test.ts` -> "rolls back on API error"

- [ ] AC-04: Checkbox tap target is at least 44x44px on all viewports
  (WCAG 2.5.5). Verified via DevTools mobile simulation at 375px.

- [ ] AC-05: Completed tasks remain in the list in their original position.
  They do not move or disappear on completion.
  Verified by: `task-completion.test.ts` -> "completed task stays in position"

- [ ] AC-06: Feature is rendered only when `FLAGS.TASK_COMPLETION` is true.
  When false, checkboxes are not rendered (tasks appear without a checkbox).
  Covered by: `task-completion.test.ts` -> "renders without checkbox when flag off"

- [ ] AC-07: Works at 375px viewport. Checkbox and task title are on the
  same row. Error message is visible and does not overflow.
  Verified via DevTools mobile simulation.

### Polish (SHIP_READY gate - not yet started)

- [ ] AC-08: Matches Figma reference for completed state at all breakpoints
- [ ] AC-09: Checkbox is keyboard-accessible (Space bar toggles, Tab focuses)
- [ ] AC-10: Screen reader announces "Task marked complete" on check
- [ ] AC-11: Strikethrough + reduced opacity meets contrast requirements for
  completed state (readability still required, not just distinguishability)
- [ ] AC-12: Animation on completion is subtle (0.15s ease) - not distracting

---

## Out of Scope

- Uncompleting a task - issue #9
- Deleting tasks - Phase 2
- Filtering or hiding completed tasks - Phase 2

---

## API Contract

Input (PATCH request to update completion state):

```typescript
interface UpdateTaskInput {
  id: string
  completed: boolean  // always true for this feature (uncomplete is separate)
}
```

Output (updated task from API):

```typescript
interface Task {
  id: string
  title: string
  completed: boolean
  createdAt: string
  completedAt: string | null  // set by server on completion
}
```

---

## Test Plan

Unit tests (in `task-completion.test.ts`):
- Marks task complete on click
- Rolls back on API error
- Completed task stays in original list position
- Renders without checkbox when FLAGS.TASK_COMPLETION is false
- Checkbox tap target is at least 44px

Integration tests:
- Full flow: click checkbox -> optimistic update -> API confirms -> task persists on reload
- Error flow: click checkbox -> API 500 -> rollback -> error message shown

E2E tests (written by Verifier after FUNCTIONAL):
- Create task -> complete task -> reload -> task still marked complete

---

## Design Reference

Design file: Figma - TaskFlow v0.1 - "Task List" frame (completed state)
Key screens: Task row (incomplete), Task row (complete), Error state
Deviations approved: None

---

## Gate Sign-offs

| Gate | Date | Result | Signed By |
|------|------|--------|-----------|
| FUNCTIONAL | | | |
| SHIP_READY | | | |

---

## Failure Patterns Learned

_None yet - feature is still in BUILDING._

---

## Change Log

- **2026-04-19**: Initial spec written after interview. AC-01 through AC-07 approved.
