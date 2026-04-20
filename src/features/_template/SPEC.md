# SPEC.md - [Feature Name]
# The Orchestrator owns acceptance criteria and status metadata in this file.
# The Verifier may append to "Failure patterns learned" only.
# Do not change criteria without Orchestrator approval.

---

## Identity

**Feature:** [feature-name]
**Phase:** Phase [X]
**Issue:** #[number]
**Branch:** feature/[feature-name]-#[issue]
**Flag:** `FLAGS.[NAME]` (env: `FEATURE_[NAME]`) | no flag needed
**Started:** YYYY-MM-DD
**Current status:** see `.agents/STATE.json` -> `features.[name].status`
**Spec status:** see `.agents/STATE.json` -> `features.[name].spec_status`

---

## Interview Notes

_Complete this section before setting spec_status to SPEC_APPROVED.
The Orchestrator conducts the interview with the human operator.
Record answers here so the feature agent builds to user intent, not just
the acceptance criteria._

**Who is the user and what are they trying to accomplish?**
(The goal, not the technical solution.)

**What does success look like from the user's perspective?**
(What do they see, experience, or accomplish when this works correctly?)

**Most likely failure modes:**
1.
2.
3.

**Explicit out of scope:**
-

**Existing patterns in the codebase to follow:**
-

---

## User Story

As a [type of user],
I want to [action],
So that [outcome/value].

---

## Acceptance Criteria

These are binary. Pass means observable, testable behavior.
Write criteria from the user's perspective, not the implementation's.

Good: "User submits the form with a missing email field and sees 'Email is required' in red below the email input."
Bad: "Email validation exists."

### Functional (FUNCTIONAL gate)

- [ ] AC-01: [User can do X] - verified by: [test name or manual step]
- [ ] AC-02: [When Y happens, Z is shown] - verified by: [test name]
- [ ] AC-03: [Error state: when API fails, user sees message M] - test: [name]
- [ ] AC-04: [Empty state: when no data, shows empty state component] - test: [name]
- [ ] AC-05: [Loading state: spinner shown while fetching] - test: [name]
- [ ] AC-06: [Works on mobile viewport 375px] - tested via: [DevTools / device]

### Polish (SHIP_READY gate - added after FUNCTIONAL passes)

- [ ] AC-07: [Matches design reference at all breakpoints]
- [ ] AC-08: [Keyboard navigable - all actions reachable without mouse]
- [ ] AC-09: [Screen reader: announces state changes correctly]
- [ ] AC-10: [Color contrast passes 4.5:1]
- [ ] AC-11: [Copy approved by project owner]

---

## Out of Scope

- [Feature X] is NOT part of this feature - tracked separately
- [Edge case Y] is deferred to Phase [N] - see `PROJECT_CONTEXT.md`

---

## API Contract

Input (from API / store):

```typescript
interface [FeatureName]Input {
  // define here
}
```

Output (what user sees / what events are emitted):

```typescript
interface [FeatureName]Output {
  // define here
}
```

---

## Test Plan

Unit tests required:
- [List specific behaviors that need unit tests]

Integration tests required:
- [Primary user flow: describe it]
- [Error flow: describe it]

E2E tests (written by Verifier):
- [Critical user journey this feature is part of]

---

## Design Reference

Design file: [Figma link | "not yet created" | "follows existing patterns"]
Key screens: [list screen names]
Deviations approved: [none | describe any approved deviation]

---

## Gate Sign-offs

| Gate | Date | Result | Signed By |
|------|------|--------|-----------|
| FUNCTIONAL | | | |
| SHIP_READY | | | |

---

## Failure Patterns Learned

Append-only. The Verifier adds entries here after failed gates so future
work converts failures into tests.

Format:
- [YYYY-MM-DD] **Gate / issue:** [FUNCTIONAL | SHIP_READY | ISSUE-XXX]
  **Pattern:** [what went wrong]
  **Future tests should cover:** [concrete behavior or edge case]

---

## Change Log

Append-only. Document any acceptance-criteria changes after work started.

- [YYYY-MM-DD]: [What changed and why, approved by whom]
