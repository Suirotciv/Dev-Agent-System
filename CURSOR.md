# Using this template with Cursor

You do **not** plug this repo into a “model API” or install a Cursor extension. The template is three things together:

1. **Files** — `STATE.json`, specs, session logs, gate JSON — so work stays out of chat-only memory.
2. **Prompts** — `.agents/ORCHESTRATOR.md`, `FEATURE_AGENT.md`, `VERIFIER_AGENT.md`, etc. — you copy the relevant file (or sections) into a Cursor chat **as instructions** for that “role.”
3. **Scripts** — Python in `.agents/scripts/` — you run them in a terminal (Cursor’s terminal is fine).

Cursor is just the IDE where you chat, edit, and run commands. The model is whatever you pick in Cursor for that chat.

---

## How a “role” maps to Cursor

| Role | What you do in Cursor |
|------|----------------------|
| **You (human)** | Approve specs, merge branches, override gates if needed. |
| **Orchestrator** | New chat → paste or @-reference `ORCHESTRATOR.md` → attach **full** `.agents/STATE.json` (or your project’s copy). Merge update envelopes, assign work. |
| **Feature agent** | New chat → `FEATURE_AGENT.md` + **only** that feature’s `SPEC.md` + scoped `STATE` slice. Builds code in `src/features/...`. |
| **Verifier** | New chat → `VERIFIER_AGENT.md` + `SPEC.md` + **built app / code** — **not** the feature agent’s session log (independence). |

Use **separate chats** (or Composer sessions) per role when you can — that mimics separate agents and reduces context bleed.

---

## What model should I use?

There is **no** required Cursor model. Rough guidance:

- **Orchestrator** — strongest model you have in Cursor (long planning, merging JSON, resolving conflicts). In Cursor this is often **Sonnet-class**, **GPT-4.x**, or **Opus** if available on your plan.
- **Feature agent** — same tier is fine; this is mostly coding + following `SPEC.md`.
- **Verifier** — ideally **a different** model or at least a **fresh chat with no implementation history** so it doesn’t “agree” with the builder. If you only have one model, still use a **new chat** and only spec + artifact.

**Minimum quality bar** (from `MODELS.md`): **large context** (128k+) matters once `STATE.json`, specs, and code pile up. Cursor’s cloud models usually satisfy that; tiny local models often break structured JSON.

**Practical Cursor tip:** Use your **default / best** model for Orchestrator; use **Composer** for big multi-file feature work if that’s what you like; start a **new chat** for Verifier with the verifier prompt + spec.

---

## Smallest possible workflow (broken down)

1. **Create or adopt a project**  
   - From this template: run `bootstrap.py` or `new-project.py` (see `GETTING_STARTED.md`).  
   - Your **real app** lives in that project; this repo can stay a template you copied from.

2. **Add a feature**  
   - `python .agents/scripts/new-feature.py --name my-feature --issue 1`  
   - Merge the generated envelope when ready (`merge-updates.py`).

3. **Spec interview (Orchestrator chat)**  
   - Human answers questions; Orchestrator fills **Interview notes** and ACs in `SPEC.md`.  
   - Human sets `spec_status` to **SPEC_APPROVED** (via `STATE` or envelope).

4. **Build (Feature chat)**  
   - Agent implements against `SPEC.md`; emits **update envelope** + **session log**; does **not** silently edit `STATE.json` unless emergency.

5. **Verify (Verifier chat)**  
   - Runs “gate” mentally or via checklist; writes **gate JSON** + envelope.  
   - Orchestrator merges; feature advances in `STATE.json`.

6. **Validate**  
   - `python .agents/scripts/validate-agent-artifacts.py` before you trust the paper trail.

---

## Where the PixelForge demo fits

`Dev-Agent-System-Demo/` is a **fictional but consistent paper trail** (orchestrator / feature / verifier logs + gate JSON) showing that story end-to-end. It is **not** wired to Cursor — it’s an example of what **you** would produce in your own project’s `.agents/` folder.

---

## If you’re stuck on “which model in Cursor settings”

You don’t need to match names to “Orchestrator vs Feature.” Pick:

1. The **best** model for sessions that edit `STATE.json` and coordinate.  
2. The **same or another** strong model for coding.  
3. A **clean session** with a strong model for verification.

That’s enough for the template to work.
