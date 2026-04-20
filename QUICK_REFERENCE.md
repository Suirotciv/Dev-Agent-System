# Agent System - Quick Reference

This repo is an agent-system template: one live state snapshot plus append-only
artifacts, lightweight helper scripts, and role prompts.

---

## The 5-second version

- **Orchestrator** - reads the full snapshot, runs spec interviews, assigns work,
  claims runtime bundles, merges update envelopes
- **Feature Agent** - owns one feature end to end, plus feature-local unit/component coverage
- **Verifier Agent** - runs tiered verification, writes per-attempt gate artifacts,
  owns E2E/regression suites. Never reads the feature agent's session logs.
- **Design System Agent** - owns shared tokens and visual primitives
- **Infra Agent** - owns CI/CD, environments, runtime-isolation conventions
- **Human Operator** - approves specs, signs off gates, resolves blockers. See `.agents/HUMAN_OPERATOR.md`.

> **PM principle:** Role separation is not bureaucracy - it is the same reason
> surgeons do not also write surgical review papers about their own operations.
> Each role has a different relationship to the work, and that difference is the value.

---

## Control-plane map

```
/
+-- AGENTS.md
+-- GETTING_STARTED.md        <- start here if you are new
+-- MODELS.md                 <- confirm your model before first session
+-- PROJECT_CONTEXT.md
+-- QUICK_REFERENCE.md        <- this file
+-- EVIDENCE.md
+-- CHANGELOG.md
+-- .env.example
+-- .agents/
    +-- STATE.json            <- live snapshot, Orchestrator is default sole writer
    +-- ORCHESTRATOR.md
    +-- FEATURE_AGENT.md
    +-- VERIFIER_AGENT.md
    +-- INFRA_AND_DESIGN_AGENTS.md
    +-- HUMAN_OPERATOR.md
    +-- RUNTIME_ISOLATION.md
    +-- SETUP_LOG.md          <- created by bootstrap.py
    +-- updates/              <- YYYY-MM-DD-HHMM-[role][-feature].json
    +-- gates/                <- YYYY-MM-DD-HHMM-[feature]-[gate].json
    +-- sessions/             <- YYYY-MM-DD-HHMM-[role][-feature].md
    +-- schemas/
    +-- scripts/
```

---

## How work flows

```
1. Bootstrap  ->  python .agents/scripts/bootstrap.py
2. New feature ->  python .agents/scripts/new-feature.py --name x --issue N
3. Interview   ->  Orchestrator + human fill SPEC.md interview notes
4. Spec approval -> human sets spec_status: SPEC_APPROVED
5. Build       ->  Feature Agent session (reads SPEC.md, builds, emits envelope)
6. Verify      ->  Verifier Agent session (reads SPEC.md + artifact only)
7. Gate record ->  gate artifact written, envelope emitted
8. Orchestrator merges, advances feature status
9. Human signs off -> SHIP_READY -> release
```

> **PM principle:** Every step that separates "deciding what to build" from
> "building it" reduces rework. The spec interview (step 3) exists because
> acceptance criteria written without user-intent context describe
> implementations, not outcomes.

---

## Key scripts

```bash
# Day 0
python .agents/scripts/bootstrap.py

# New feature
python .agents/scripts/new-feature.py --name feature-name --issue N

# Merge an update envelope
python .agents/scripts/merge-updates.py --expected-revision N path/to/envelope.json

# Validate all artifacts
python .agents/scripts/validate-agent-artifacts.py

# Refresh prompt hashes after editing a prompt file
python .agents/scripts/prompt-hash.py --write-state --expected-revision N

# Claim a runtime bundle for parallel work
python .agents/scripts/allocate-runtime.py claim feature-name --expected-revision N

# Release a runtime bundle
python .agents/scripts/allocate-runtime.py release feature-name --expected-revision N

# Install the pre-commit validation hook (optional)
bash .agents/scripts/install-hooks.sh
```

---

## Defaults worth remembering

**STATE.json is the live snapshot, not the audit log.**
It records the current truth. Session logs and gate artifacts are the history.
Do not put "current work" notes in PROJECT_CONTEXT.md - that belongs in STATE.json.

> **PM principle:** Separating the current state from the history of how you got
> there is the same reason a balance sheet and an income statement are different
> documents. One answers "where are we now?" and the other answers "how did we
> get here?"

---

**Non-orchestrator agents submit update envelopes instead of patching STATE directly.**
This keeps the single-writer guarantee intact. Two agents writing STATE.json
simultaneously would produce corrupted state with no conflict record.

> **PM principle:** This is the same reason PRs exist. Direct commits to main
> are fast but fragile. A merge step - even a lightweight one - creates a
> checkpoint where conflicts become visible before they become damage.

---

**Session logs and gate artifacts are append-only.**
Never overwrite a prior attempt. The history of failed gates is as important
as the passing ones - it shows what was tried and why it failed.

> **PM principle:** This is the same reason lawyers do not erase notes.
> The record of decisions is often more valuable than the decisions themselves,
> especially when something breaks six months later.

---

**SPEC.md is orchestrator-owned; the Verifier may append "Failure patterns learned" only.**
The Verifier must not change acceptance criteria - that would allow the
verification standard to drift toward whatever was built, rather than
what was intended.

> **PM principle:** Requirements are set before implementation, not adjusted
> to match it. If the criteria are wrong, that is a discovery worth recording -
> not a silent correction.

---

**The Verifier does not read the feature agent's session logs.**
Independence is the Verifier's only asset. The moment it absorbs the
implementation's assumptions, it becomes a rubber stamp.

> **PM principle:** The person who built something is the worst person
> to evaluate whether it works. Not because they are careless, but because
> they have absorbed the same blind spots as the thing they built.
> Always. This is true of human engineers too.

---

**Tiered FUNCTIONAL gate: static checks before behavioral.**
Static checks (typecheck, lint, unit tests) are fast and cheap. Behavioral
checks (E2E, integration, acceptance criteria) are slow and expensive.
Failing fast on static saves the expensive behavioral pass for when it matters.

> **PM principle:** Do cheap verification first. Every QA process, code review,
> and acceptance test workflow that works well does this. Sequence your checks
> by cost, not by what feels most thorough.

---

**Scoped STATE.json reads per role.**
Feature agents read only their slice. This is not just about performance -
it reduces the surface area for agents to make wrong assumptions based on
context they were not meant to have.

> **PM principle:** Agents with less context make fewer assumptions.
> Assumptions are where bugs hide. Giving someone exactly what they need
> and nothing more is a discipline, not a limitation.

---

**Prompt hashes prevent silent drift.**
Every session records the hash of the prompt it ran under. If a prompt file
changes, the system detects the mismatch and requires a rehash before new work
is assigned. This means you always know whether agents are running on the
same instructions.

> **PM principle:** Version your process, not just your code. When something
> goes wrong, knowing exactly which instructions were in effect is the fastest
> path to diagnosis.

---

**spec_status gates feature assignment.**
No feature agent is assigned until `spec_status: SPEC_APPROVED`. This is the
enforcement mechanism for the interview protocol - it makes it structurally
impossible to skip requirements clarity.

> **PM principle:** The cost of discovering a misunderstood requirement
> compounds with every hour spent building the wrong thing. The interview
> is cheap. Rebuilding is not.

---

## Common failure modes and fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Validator fails with "prompt hash mismatch" | Prompt file was edited | `python .agents/scripts/prompt-hash.py --write-state --expected-revision N` |
| Merge fails with "revision mismatch" | Another merge happened first | Re-read STATE.json, use current `_state_revision` |
| Merge fails with "non-existent feature" | Envelope sets status before feature entry exists | Create feature entry first, or let `new-feature.py` do it |
| Agent produced malformed JSON | Model added markdown fences or trailing commas | See OUTPUT FORMAT RULES in each agent prompt and MODELS.md |
| Feature stuck in BUILDING > 60 days | Scope too large, or blocker unresolved | Break into smaller features or escalate the blocker |
| Gate keeps failing same criterion | Pattern not recorded | Verifier appends to "Failure patterns learned" in SPEC.md |

---

## The design rationale behind this system

The rationale and external evidence for key design decisions is in `EVIDENCE.md`.
Refresh it quarterly (January, April, July, October) or when a major
agent-platform release invalidates current guidance.

Key sources backing the current design:
- Orchestrator-as-sole-writer -> Anthropic multi-agent research on vague
  delegation causing duplicated work
- Worktrees + runtime bundles -> OpenAI Codex and Claude Code documentation
  on parallel agent isolation
- Tiered gates -> Anthropic "Demystifying evals" on separating static from
  behavioral verification
- Prompt hash tracking -> Vellum release tags and deployment evidence
