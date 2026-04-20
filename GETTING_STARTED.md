# Getting Started with the Agent System

This guide walks you through your first day with the system. No prior experience
with agent frameworks required. By the end you will have a working project,
understand what every piece does, and be ready to assign your first feature.

---

## What this system actually is

Before anything else: this is not magic. It is a structured coordination layer
that makes it easier for AI agents - and you - to work on a codebase without
stepping on each other or losing track of what has been decided.

The core insight is simple: **shared state beats shared memory**. Instead of
every agent trying to remember what happened in previous conversations, there
is one file - `STATE.json` - that records the current truth about the project.
Agents read their slice of it at the start of a session and write changes back
through a controlled path. Nothing gets lost between sessions. Nothing gets
duplicated between agents.

Think of it like a project management board that is actually read by the people
(agents) doing the work.

---

## What you need before you start

**Model requirements:**
The system is model-agnostic. It works with local models (Ollama, LM Studio)
and cloud providers (Anthropic, OpenAI, Gemini). Before running this system,
read `MODELS.md` to confirm your model meets the minimum requirements for
the roles you plan to use. The short version: 128k context window minimum,
70B+ or frontier model for the Orchestrator role.

**Python 3.9+** - all helper scripts are pure stdlib Python.

**Git** - the system uses git for branch isolation. Initialize your repo first.

**A text editor** - you will be filling in `SPEC.md` files for each feature.
This is intentional: the spec is the one document only you can write well,
because only you know what "done" looks like from the user's perspective.

---

## Day 0: Initialize your project

Run the setup wizard from your repo root:

```bash
python .agents/scripts/bootstrap.py
```

The wizard asks you six questions, then:
- Stamps all template placeholders with your project's real values
- Initializes `STATE.json` with correct prompt hashes
- Creates a `SETUP_LOG.md` recording what was set and when

If you prefer a non-interactive setup (for scripting or CI), use:

```bash
python .agents/scripts/new-project.py \
  --name "YourProject" \
  --description "What it does and for who" \
  --output-dir /path/to/new/project
```

After bootstrap runs, open `PROJECT_CONTEXT.md` and fill in Section 1
(Identity) and Section 9 (Key Decisions). These are the parts that require
your judgment - the wizard fills in what it can, but you know your project.

---

## Day 1: Create your first feature

```bash
python .agents/scripts/new-feature.py --name your-feature-name --issue 1
```

This creates:
- `src/features/your-feature-name/SPEC.md` - the acceptance criteria doc
- `src/features/your-feature-name/AGENTS.md` - context for the feature agent
- An update envelope in `.agents/updates/` to add the feature to STATE.json

Now open `SPEC.md` and fill in the **Interview notes** section before writing
any acceptance criteria. This section asks:
- Who is the user and what are they trying to accomplish?
- What does success look like from their perspective?
- What are the three most likely failure modes?
- What is explicitly out of scope?

This feels like extra work. It is the highest-leverage thing you will do.
Features built without clear acceptance criteria are the leading cause of
rework. Five minutes of writing here saves hours of debugging later.

After the interview notes are filled in, write your acceptance criteria (AC-01
through at minimum AC-06). Each criterion is binary: it either passes or fails
a concrete, observable test. "User can log in" is not a criterion.
"User enters valid email and password, submits, and is redirected to the
dashboard within 2 seconds" is a criterion.

---

## The agent loop

Once your feature has approved acceptance criteria, the flow looks like this:

```
You (human)
  -> Orchestrator agent       reads STATE.json in full, assigns work
    -> Feature Agent          builds the feature in src/features/[name]/
      -> emits update envelope when done
    -> Orchestrator           merges envelope, advances feature to FUNCTIONAL
    -> Verifier Agent         runs FUNCTIONAL gate (no knowledge of implementation)
      -> writes gate artifact  pass or fail, with per-criterion evidence
    -> Orchestrator           records gate result, moves to SHIP_READY or back
  -> You (human)              final sign-off before release
```

Each role has a prompt file in `.agents/`. The Orchestrator reads STATE.json
in full. Feature and Verifier agents read only their scoped slice. This means
agents start sessions with precisely the context they need - no more, no less.

**Why is the Verifier separate from the Feature Agent?**

The person who built something is the worst person to evaluate whether it works.
Not because they are careless, but because they have absorbed all the same
assumptions that caused any bugs in the first place. An independent Verifier
with only the spec and the artifact catches what the builder missed.
This is true of human engineers too - it is why code review works.

---

## What the Orchestrator does (and does not do)

The Orchestrator coordinates. It assigns work, claims runtime bundles for
parallel sessions, merges update envelopes from other agents, and records
gate results. It does not write application code.

When you start an Orchestrator session, give it STATE.json in full. Its job
is to read the current state, check for pending update envelopes in
`.agents/updates/`, merge them, and decide what to assign next.

The Orchestrator's judgment calls:
- Which features are ready to build (spec approved, no blockers)
- Whether two features can be built in parallel (different directories)
- Whether a gate result should advance or block a feature
- How to resolve blockers logged by feature agents

---

## When to intervene as a human

You are the tech lead. The agents work; you direct. Read `.agents/HUMAN_OPERATOR.md`
for the full breakdown. The short list:

**Always requires you:**
- Approving `spec_status: SPEC_APPROVED` on a new feature
- Merging `develop` -> `main`
- Overriding a Verifier FAIL decision (requires a logged reason)
- Resolving a `BLOCKER-` entry that has been open more than one sprint

**You can do at any time:**
- Read any file in `.agents/`
- Create a manual update envelope and ask the Orchestrator to merge it
- Run any script directly

**You should not do:**
- Edit a session log after it is written
- Skip the Verifier because "you know it works"
- Advance a feature past a gate without a gate artifact

---

## When things go wrong

**The validator is failing:**
```bash
python .agents/scripts/validate-agent-artifacts.py
```
Read the error output carefully. The most common causes are:
1. A session log is missing required frontmatter fields
2. A gate artifact references a known issue ID that does not exist in STATE.json
3. Prompt hashes in STATE.json are out of date (you edited a prompt file)

To fix prompt hashes:
```bash
python .agents/scripts/prompt-hash.py --write-state --expected-revision <n>
```

**An update envelope failed to merge:**
The merge script validates envelopes before applying them. Common errors:
- The feature name in the envelope does not exist in STATE.json yet
- The `_state_revision_at_start` does not match the current revision
  (another merge happened first - re-read STATE.json and resubmit)
- Invalid JSON syntax in the envelope (see MODELS.md for output format guidance)

**An agent session ended mid-task:**
Check the last session log in `.agents/sessions/`. If the agent left a
`SESSION_STATE.md` in the feature directory, it recorded its progress before
compacting. Start a new session and ask the agent to read that file first.

**STATE.json revision conflict:**
Two merges happened out of order. Read the current STATE.json, increment
`_state_revision` by 1 from the current value, and re-run the merge with
`--expected-revision <current>`.

---

## Where to go next

- `MODELS.md` - capability matrix for choosing models per role
- `QUICK_REFERENCE.md` - the 5-second overview of the whole system
- `PROJECT_CONTEXT.md` - your project's human-readable reference
- `.agents/HUMAN_OPERATOR.md` - full breakdown of the human role
- `.agents/ORCHESTRATOR.md` - system prompt for Orchestrator sessions
- `examples/task-app/` - a fully filled-out example project to reference

---

## The one-paragraph philosophy

Good project management is not about process for its own sake. It is about
making it easy to know what is true about your project at any given moment:
what is done, what is in progress, what is blocked, and why. This system
encodes that philosophy in files and scripts. The agents are not the point.
The discipline of writing specs before building, verifying independently,
and recording decisions is the point. The agents just make that discipline
cheap enough to maintain on a solo project.
