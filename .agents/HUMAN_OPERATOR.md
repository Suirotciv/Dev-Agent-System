# HUMAN_OPERATOR.md
# The human operator's role in the agent system.
# Read this before your first session.

---

## The core idea

You are the tech lead. Agents are your team. You set direction, you approve
decisions that affect the whole project, you unblock blockers, and you do
the final sign-off before anything ships. You do not micromanage
implementation - that is what the Feature Agent is for.

This division matters because it keeps you at the right level of abstraction.
A tech lead who rewrites every pull request is a bottleneck. A tech lead who
never reviews anything ships bugs. The system is designed to keep you in the
middle: directing and approving, not implementing.

---

## What always requires your approval

### Spec approval
Before a feature agent is assigned, `spec_status` must be `SPEC_APPROVED`.
You are the one who sets this. Fill in the Interview notes in `SPEC.md`,
review the acceptance criteria, and when you are satisfied that the criteria
are testable and complete, update the envelope:

```json
{ "op": "set", "path": "features.[name].spec_status", "value": "SPEC_APPROVED" }
```

Or update `STATE.json` directly if you are the Orchestrator.

**Why this matters:** Acceptance criteria written without user-intent context
describe implementations, not outcomes. You are the only one who knows what
the user actually needs.

### Merging develop -> main
This always requires you. The Release Gate checklist in `PROJECT_CONTEXT.md`
section 5 must be complete. No agent can authorize a production deploy.

### SHIP_READY advancement
After the Verifier passes the FUNCTIONAL gate, SHIP_READY requires additional
review (visual, accessibility, copy). You sign off on this gate.

### Overriding a Verifier FAIL
If you believe a Verifier FAIL decision is wrong, you can override it - but you
must log a reason in the gate artifact. Create a new gate artifact manually with
`result: "PASS"` and include `override_reason` in the `failures` array explaining
what you reviewed and why you are satisfied. Do not silently skip the gate.

### Resolving BLOCKER entries
If an agent files a `BLOCKER-` entry and it has been unresolved for more than
one sprint, you must step in. Options:
- Resolve it yourself (make the shared type change, add the missing util)
- Descope the feature to avoid the blocked dependency
- Explicitly defer the feature and update STATUS to `BLOCKED`

---

## What you can do at any time

**Read any file in `.agents/`.**
STATE.json, session logs, gate artifacts - all of it is yours to read. You are
not limited to the Orchestrator's scoped view.

**Create a manual update envelope.**
If you need to change STATE.json directly and the Orchestrator is not running,
write an update envelope in `.agents/updates/` and merge it yourself:

```bash
python .agents/scripts/merge-updates.py --expected-revision <n> .agents/updates/your-envelope.json
```

Your envelope should use `role: "orchestrator"` and document what you changed
and why in the `summary` field.

**Inject a decision into a session.**
If an agent needs your input mid-session (a blocker, a scope question, a
design decision), you can add a note to STATE.json directly using the
Orchestrator's compare-and-swap path. Record the decision in a session log
so the history is preserved.

**Run any script directly.**
```bash
python .agents/scripts/validate-agent-artifacts.py
python .agents/scripts/prompt-hash.py --check
python .agents/scripts/allocate-runtime.py claim [feature] --expected-revision <n>
```

**Adjust acceptance criteria before a feature starts.**
Once a feature reaches `BUILDING` status, criteria changes require a Change Log
entry in `SPEC.md`. Before `BUILDING`, you can edit freely.

---

## What you should not do

**Edit a session log after it is written.**
Session logs are append-only records. Editing them breaks the audit trail.
If you need to correct something, write a new session log or an update envelope
documenting the correction.

**Skip the Verifier because you know it works.**
You might be right. You are also the person most likely to have absorbed the
same blind spots as the feature agent. The Verifier finds things you missed -
not because it is smarter, but because it has not been living inside the
implementation for the last several sessions. The gate artifact is also your
safety net when a future change breaks something.

**Merge without a gate artifact.**
Even for small features, write the artifact. It takes 10 minutes and gives you
a record of what was verified and when. Six months from now, when something
breaks, you will want that record.

**Change acceptance criteria after FUNCTIONAL is in progress without logging it.**
Changing what "done" means while someone is building to the old definition is
the single largest source of wasted effort in software projects. If you must
change criteria, log it in `SPEC.md -> Change Log` and notify the feature agent.

---

## The escalation path

When something is stuck:

1. **BLOCKER- unresolved for more than one sprint:**
   - Assign it to yourself in the update envelope
   - Set `status: "IN_PROGRESS"` with your name as resolver
   - Update the blockers entry when resolved

2. **Agent is looping or producing garbage:**
   - Stop the session
   - Read the last session log to understand where it is
   - Start a fresh session with a narrower scope
   - Refer to `MODELS.md` if this is a recurring issue with a local model

3. **STATE.json is corrupted or inconsistent:**
   - Run `python .agents/scripts/validate-agent-artifacts.py`
   - Fix the reported errors manually
   - Increment `_state_revision` and update `_updated` / `_updated_by`
   - Run validation again to confirm

4. **Two agents produced conflicting changes:**
   - The merge script records conflicts in `_conflicts` at the root of STATE.json
   - Review each conflict - the later timestamp wins by default
   - If the default is wrong, set the correct value manually and remove the conflict entry

---

## Decision injection: how to record a human decision

When you make a decision that should be part of the project record, write
it as an update envelope with your reasoning:

```json
{
  "update_id": "UPD-20260419-120000-human-decision-01",
  "submitted_at": "2026-04-19T12:00:00+00:00",
  "submitted_by": "human-operator",
  "role": "orchestrator",
  "_prompt_version": "[current hash from STATE.json]",
  "_state_revision_at_start": 7,
  "target_feature": "user-auth",
  "resource_claim_id": null,
  "summary": "Descoped OAuth from v1. Will use email/password only for launch.",
  "changes": [
    {
      "op": "append",
      "path": "known_issues",
      "value": {
        "id": "ISSUE-003",
        "description": "OAuth deferred from v1 - email/password only for launch",
        "owner": "human-operator",
        "priority": "LOW",
        "opened": "2026-04-19"
      }
    }
  ]
}
```

Then merge it: `python .agents/scripts/merge-updates.py --expected-revision 7 [path]`

This keeps the decision in the record without requiring an agent session.

---

## A note on autonomy

As the system matures and you build trust with specific agent configurations,
you may want to give agents more autonomy - letting the Orchestrator run
multi-session sequences without checking in between each one, for example.

This is reasonable. The system is designed to support it. But start with more
oversight and relax it as you gain confidence in the outputs, not the other
way around. The gate artifacts are your insurance - they make it safe to give
agents more room because you can always see exactly what was verified and when.
