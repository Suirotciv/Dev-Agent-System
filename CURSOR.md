# Using this template with Cursor

You do **not** plug this repo into a “model API” or install a Cursor extension. The template is three things together:

1. **Files** — `STATE.json`, specs, session logs, gate JSON — so work stays out of chat-only memory.
2. **Prompts** — `.agents/ORCHESTRATOR.md`, `FEATURE_AGENT.md`, `VERIFIER_AGENT.md`, etc. — you copy the relevant file (or sections) into a Cursor chat **as instructions** for that “role.”
3. **Scripts** — Python in `.agents/scripts/` — you run them in a terminal (Cursor’s terminal is fine).

Cursor is just the IDE where you chat, edit, and run commands. The model is whatever you pick in Cursor for that chat.

---

## Do I open a new window with only the demo folder?

**No — not for real work.** `Dev-Agent-System-Demo/` is a **sample story** (markdown + JSON). There is no app to run inside that folder alone; it is for reading, recording, or showing “what the paper trail looks like.”

**Do this instead:**

| Goal | What to open in Cursor |
|------|-------------------------|
| **Learn the system + run scripts** | Open the **whole repo** `Dev-Agent-System` (template root). You get `.agents/scripts/`, prompts, and you can read `Dev-Agent-System-Demo/` next to it. One window is fine. |
| **Build your actual product** | Open the **project folder you created** with `bootstrap.py` / `new-project.py` (e.g. `PixelForge`). That folder has **your** `src/`, **your** `.agents/STATE.json`, and is where chats should edit code. |
| **Only skim the PixelForge narrative** | You *can* open just `Dev-Agent-System-Demo` to read files — but you cannot “run the agent system” from only that folder. |

You do **not** need a separate Cursor window per role. You **do** need **separate chats** (see below) so Orchestrator / Feature / Verifier do not share one long thread.

---

## What you actually do inside Cursor (concrete)

1. **File → Open Folder** → pick the template root *or* your generated app root (see table above).

2. **Terminal** (`` Ctrl+` `` or View → Terminal) → run Python commands from that folder, e.g.  
   `python .agents/scripts/new-feature.py --name my-feature --issue 1`

3. **Orchestrator pass**  
   - Open **Chat** (or Composer).  
   - Use **@** to attach `.agents/ORCHESTRATOR.md` and `.agents/STATE.json`.  
   - Say something like: “Follow the START OF SESSION PROTOCOL in ORCHESTRATOR.md. Here is the repo. Pending envelopes are in `.agents/updates/`.”  
   - You type answers when it runs the **spec interview**; it (or you) updates `SPEC.md` and `STATE` per the template.

4. **Feature pass**  
   - **New chat** (fresh context).  
   - Attach `.agents/FEATURE_AGENT.md` and `src/features/<name>/SPEC.md` (and `AGENTS.md` if present).  
   - Say: “Implement this feature per SPEC; when done, write the session log and update envelope paths the prompt describes.”  
   - Use **Composer** or **Agent** mode if you want it to touch many files under `src/`.

5. **Verifier pass**  
   - **New chat** again.  
   - Attach `.agents/VERIFIER_AGENT.md` and the same `SPEC.md` + the **code / app** to verify.  
   - Do **not** attach the feature agent’s session log (independence).  
   - Ask it to produce gate JSON + envelope per `VERIFIER_AGENT.md`.

6. **You** merge envelopes / bump `STATE` with the scripts, then run  
   `python .agents/scripts/validate-agent-artifacts.py`

That is the whole loop: **folder choice → terminal scripts → three kinds of chats with @ files → validate.**

---

## Easier than editing SPEC.md by hand (terminal “form”)

If you do not want a blank `SPEC.md`, run this **from your project root** (e.g. `Pixel_App`):

```powershell
py .agents\scripts\spec-interview.py --feature pixel-editor
```

It asks a short set of questions and **writes the Interview notes section** for you. You can still use an Orchestrator chat afterward to tighten acceptance criteria.

**Duplicate files in `.agents\updates\`:** If you ran `new-feature.py` twice, you will see **two** JSON files. **Delete the older one**, then merge once.

**Merge without typing the long filename:**

```powershell
py .agents\scripts\merge-updates.py --expected-revision 1 --latest
```

Use the current `_state_revision` from `STATE.json` if it is not `1`.

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
