# SPEC.md - Task Creation
# The Orchestrator owns acceptance criteria and status metadata in this file.
# The Verifier may append to "Failure patterns learned" only.

---

## Identity

**Feature:** task-creation
**Phase:** Phase 1
**Issue:** #3
**Branch:** feature/task-creation-#3
**Flag:** `FLAGS.TASK_CREATION` (env: `FEATURE_TASK_CREATION`)
**Started:** 2026-04-18
**Current status:** see `.agents/STATE.json` -> `features.task-creation.status`
**Spec status:** SPEC_APPROVED

---

## Interview Notes

_Completed 2026-04-18 by Orchestrator + human operator._

**Who is the user and what are they trying to accomplish?**
A solo developer or small team member who needs to quickly capture a task
before they forget it. They are often mid-flow doing something else. Speed
and simplicity matter more than features - they should be able to add a task
in under 5 seconds without breaking their current context.

**What does success look like from the user's perspective?**
They type a task title, press Enter (or tap Add), and the task appears
immediately in their list. No page reload. No confirmation dialog. No
required fields beyond the title. It just works.

**Most likely failure modes:**
1. The form submits but the task does not appear in the list immediately -
   user does not know if it worked and submits again (duplicate tasks).
2. The input field is not focused on page load - user has to click before
   typing, which breaks the "quick capture" goal.
3. Whitespace-only titles are accepted and create empty-looking tasks
   that cannot be distinguished from real tasks.

**Explicit out of scope:**
- Task descriptions, due dates, tags, assignees - Phase 2
- Reordering tasks - Phase 2
- Task editing after creation - separate feature, tracked in issue #7
- Keyboard shortcuts beyond Enter to submit

**Existing patterns to follow:**
- Form validation pattern in `src/features/user-profile/UserProfileForm.tsx`
- API call pattern in `src/features/user-profile/api.ts`
- Loading state pattern in `src/components/shared/Button.tsx`

---

## User Story

As a developer managing my workday,
I want to quickly add a task to my list by typing a title and pressing Enter,
So that I can capture what I need to do without interrupting my current flow.

---

## Acceptance Criteria

### Functional (FUNCTIONAL gate)

- [x] AC-01: User types a task title (1-200 characters, non-whitespace) and
  presses Enter or clicks Add - task appears in the list within 300ms without
  page reload. Verified by: `task-creation.test.ts` -> "adds task on Enter"

- [x] AC-02: Input field is focused automatically on page load.
  Verified by: `task-creation.test.ts` -> "input is focused on mount"

- [x] AC-03: Whitespace-only titles (e.g. "   ") are rejected client-side.
  Input shows inline error "Task title cannot be empty" in red below the field.
  Form is not submitted to the API. Verified by: `task-creation.test.ts` ->
  "rejects whitespace-only input" - **NOTE: client-side trim is incomplete,
  see ISSUE-001**

- [x] AC-04: Title longer than 200 characters is rejected client-side with
  error "Title must be 200 characters or fewer (N/200)".
  Verified by: `task-creation.test.ts` -> "rejects title over 200 chars"

- [x] AC-05: When API call is in flight, Add button shows a spinner and is
  disabled. Input is also disabled. On success, input clears and task appears.
  Verified by: `task-creation.test.ts` -> "shows loading state during submit"

- [x] AC-06: When API returns an error (5xx), inline error "Something went wrong -
  please try again" is shown below the form. Previously entered title is
  preserved in the input. Verified by: `task-creation.test.ts` -> "handles API error"

- [x] AC-07: Form is functional at 375px viewport. Input and button are full-width.
  Error messages are visible and do not overflow. Verified via DevTools mobile sim.

- [x] AC-08: Feature is rendered only when `FLAGS.TASK_CREATION` is true.
  When flag is false, the route renders null. Covered by:
  `task-creation.test.ts` -> "renders null when flag is off"

### Polish (SHIP_READY gate - not yet started)

- [ ] AC-09: Matches Figma reference at 375px, 768px, and 1280px
- [ ] AC-10: Tab order is logical: input -> button. Enter submits. Escape clears.
- [ ] AC-11: Screen reader announces "Task added" after successful creation.
- [ ] AC-12: Color contrast on error text passes 4.5:1 (currently using
  --color-border-danger as temporary - see DESIGN-REQ-001)
- [ ] AC-13: Copy approved: "Add task" placeholder, "Add" button label,
  all error messages

---

## Out of Scope

- Task descriptions, due dates, assignees - Phase 2
- Reordering - Phase 2
- Editing an existing task title - issue #7

---

## API Contract

Input (what the form submits):

```typescript
interface CreateTaskInput {
  title: string  // 1-200 chars, trimmed, non-empty
}
```

Output (what the API returns):

```typescript
interface Task {
  id: string       // UUID
  title: string
  completed: boolean
  createdAt: string  // ISO 8601
}
```

Error response:

```typescript
interface ApiError {
  message: string
  code: string  // e.g. "VALIDATION_ERROR", "INTERNAL_ERROR"
}
```

---

## Test Plan

Unit tests (in `task-creation.test.ts`):
- Adds task on Enter key
- Adds task on button click
- Input is focused on mount
- Rejects whitespace-only input (client-side)
- Rejects title over 200 characters
- Shows loading state during submit
- Handles API error (5xx)
- Renders null when FLAGS.TASK_CREATION is false

Integration tests:
- Full flow: user types title -> presses Enter -> task appears in list
- Error flow: API returns 500 -> error message shown -> title preserved

E2E tests (written by Verifier after FUNCTIONAL):
- Critical path: create task -> task visible in list -> survives page reload

---

## Design Reference

Design file: Figma - TaskFlow v0.1 - "Task Creation" frame
Key screens: Empty state, Form active, Loading, Success, Error
Deviations approved: Using --color-border-danger for error text temporarily
pending DESIGN-REQ-001 resolution.

---

## Gate Sign-offs

| Gate | Date | Result | Signed By |
|------|------|--------|-----------|
| FUNCTIONAL | 2026-04-19 | PASS | verifier-agent |
| SHIP_READY | | | |

---

## Failure Patterns Learned

- **2026-04-19** **Gate:** FUNCTIONAL (initial attempt - FAIL before fix)
  **Pattern:** Client-side whitespace trim was not applied before the
  non-empty check. `"   ".length > 0` evaluates to true, so the validation
  passed with whitespace-only input. Server correctly rejected it, but the
  client showed no error and the user saw a form submit with no visible result.
  **Future tests should cover:** Trim before length check. Test with
  single space, multiple spaces, and tab characters specifically.
  **Status:** Partially fixed - server trim added, client-side trim incomplete.
  ISSUE-001 tracks the remaining client gap.

---

## Change Log

- **2026-04-18**: Initial spec written after interview. AC-01 through AC-08 approved.
- **2026-04-19**: AC-07 renumbered (was AC-06) to insert mobile viewport criterion
  before flag criterion. Approved by human operator.
