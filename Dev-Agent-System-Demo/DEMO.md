# PixelForge — Demo package (pre-recorded storyboard)

**Pitch for indie hackers:** The spec interview caught requirements your first prompt missed. An independent verifier caught a bug the feature agent’s tests green-lit. Every step is in files you can diff — not vibes.

---

## Before you hit record

1. **Terminal proof (add this first):** Record the real commands with [asciinema](https://asciinema.org/) or [VHS](https://github.com/charmbracelet/vhs). That makes “one command” visceral instead of claimed. See [`recordings/README.md`](recordings/README.md) for a copy-paste flow and a `demo.tape` template.
2. **App:** Use your working PixelForge build (pencil, fill, eyedrop, palette, undo/redo, grid, PNG export). Position the widget where the camera/screen capture can see it cleanly.
3. **This folder:** Open artifacts from `Dev-Agent-System-Demo/` (paths below) so viewers see real filenames.

---

## Act 1 — Two commands (~10s)

Show **both** invocations from a clean shell (template repo root for PixelForge, or your recording script).

```bash
# Day 0: initialize the project (interactive wizard)
python .agents/scripts/bootstrap.py

# Day 1: scaffold the feature (writes SPEC + envelope)
python .agents/scripts/new-feature.py --name pixel-editor --issue 1
```

**On-screen cue:** `STATE.json` + prompt hashes after bootstrap; `SPEC.md` / `AGENTS.md` + `.agents/updates/*.json` after `new-feature`.

**Recording tip:** Interactive `bootstrap` is awkward for automation. For a terminal-only take, use the non-interactive equivalent documented in [`recordings/README.md`](recordings/README.md) (`new-project.py` + `new-feature.py`) — same architecture, zero prompts.

---

## Act 2 — Orchestrator session (~30s)

**File:** [`2026-04-20-0900-orchestrator.md`](2026-04-20-0900-orchestrator.md)

**Narrative beat:** The spec interview surfaced **two gaps the original build prompt did not specify:**

- **Eyedropper** — user: “obviously I need to sample colors from the canvas.”
- **Multi-scale preview** — user: “I need to see how the sprite reads at game scale, not only at cell size.”

Those became **AC-04** and **AC-07** in [`SPEC.md`](SPEC.md). That is the system’s argument: *intent before implementation.*

---

## Act 3 — Gate artifact (~20s)

**File:** [`2026-04-20-1400-pixel-editor-functional.json`](2026-04-20-1400-pixel-editor-functional.json)

**Narrative beat:** Eight criteria — each line of evidence is **specific**, not “looks good”:

| AC | Example of specificity (from the artifact) |
|----|---------------------------------------------|
| AC-01 | Drag across 6 cells — all painted, no gaps; fast drag tested |
| AC-06 | PNG opened in Preview: **512×512px**, pixels sharp, **no antialiasing** |
| AC-07 | **1×** (16×16) and **4×** (64×64) previews update on every paint |
| … | Open the JSON — same tone for fill, eraser, undo, flag-off |

**Verifier independence:** Session log [`2026-04-20-1400-verifier-agent-pixel-editor.md`](2026-04-20-1400-verifier-agent-pixel-editor.md) — blackbox: **did not** read the feature agent’s session log.

**Bug story:** First export attempt was **16×16** (wrong scale). Verifier caught it; feature agent fixed; **ISSUE-001** documents the test gap. That is “auditable” in one sentence.

---

## Act 4 — Running app (~30s)

Draw live: pencil strokes, bucket fill, eyedrop from palette or canvas, toggle grid, undo/redo, export PNG and optionally open the file to show sharp pixels.

**Closing line (optional):** “The interview caught what the prompt missed. The verifier caught what the tests didn’t. The paper trail is the product.”

---

## Artifact index (this folder)

| Artifact | Role |
|----------|------|
| [`STATE.json`](STATE.json) | Final snapshot: `pixel-editor` **VERIFIED**, flags, gates, ISSUE-001 |
| [`SPEC.md`](SPEC.md) | Interview notes + ACs (eyedropper + previews called out) |
| [`2026-04-20-0900-orchestrator.md`](2026-04-20-0900-orchestrator.md) | Spec interview + approvals |
| [`2026-04-20-1015-feature-agent-pixel-editor.md`](2026-04-20-1015-feature-agent-pixel-editor.md) | Build notes (for your B-roll — verifier does not rely on this) |
| [`2026-04-20-1400-verifier-agent-pixel-editor.md`](2026-04-20-1400-verifier-agent-pixel-editor.md) | Evidence narrative |
| [`2026-04-20-1400-pixel-editor-functional.json`](2026-04-20-1400-pixel-editor-functional.json) | Gate: per-AC evidence |
| [`2026-04-20-1445-verifier-pixel-editor.json`](2026-04-20-1445-verifier-pixel-editor.json) | Update envelope (status → VERIFIED) |

---

## Why this demo exists

Structured coordination — shared `STATE.json`, interviews, independent verification, gate JSON — is the difference between *shipping* and *hoping*. PixelForge is one concrete walkthrough; these files are the receipt.
