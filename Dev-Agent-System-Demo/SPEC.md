# SPEC.md - Pixel Editor
# The Orchestrator owns acceptance criteria and status metadata in this file.
# The Verifier may append to "Failure patterns learned" only.

---

## Identity

**Feature:** pixel-editor
**Phase:** Phase 1
**Issue:** #1
**Branch:** feature/pixel-editor-#1
**Flag:** `FLAGS.PIXEL_EDITOR` (env: `FEATURE_PIXEL_EDITOR`)
**Started:** 2026-04-20
**Current status:** VERIFIED
**Spec status:** SPEC_APPROVED

---

## Interview Notes

_Completed 2026-04-20 by Orchestrator + human operator._

**Who is the user and what are they trying to accomplish?**
An indie game developer or hobbyist who needs to quickly sketch a sprite or
icon without leaving the browser. They are not professional pixel artists —
they need something fast and approachable. The tool should feel like a real
instrument, not a coding demo. If it feels toy-like, they won't use it.

**What does success look like from the user's perspective?**
They open it, immediately understand how to draw something, and within 2
minutes have a sprite they can export and drop into their game. The tools
should behave exactly as expected — pencil draws, eraser erases, fill fills.
No friction, no learning curve beyond what any paint tool requires.

**Most likely failure modes:**
1. The canvas interaction feels laggy or jittery during fast drawing — kills
   confidence in the tool immediately.
2. Exporting produces a blurry PNG (nearest-neighbor scaling not applied) —
   useless for game assets.
3. No way to undo a mistake — forces users to start over, very frustrating
   in a creative tool.

**Explicit out of scope:**
- Multiple layers — too complex for v1, would slow everything down
- Animation frames — tracked separately, issue #4
- Saving to cloud / account system — file download is sufficient for v1
- Canvas sizes other than 16×16 — keep scope tight, add later
- Zoom / pan — the canvas is already displayed at a usable size

**Existing patterns to follow:**
- Event handling pattern in `src/features/task-creation/` for mouse interactions
- State management: use useReducer, not scattered useState — see team AGENTS.md
- Export pattern: hidden canvas + toDataURL — no external libraries

**One requirement that came out of the interview (not in original prompt):**
The user specifically wanted an eyedropper tool and live preview at multiple
scales. Both added to ACs. This is why the interview exists.

---

## User Story

As an indie game developer,
I want to draw and export a 16×16 pixel sprite in the browser,
So that I can quickly create game assets without leaving my workflow.

---

## Acceptance Criteria

### Functional (FUNCTIONAL gate)

- [x] AC-01: User clicks or drags on the canvas to paint pixels in the
  selected color. Pixels update immediately with no perceptible lag.
  Mouse-drag paints a continuous stroke (not just single cells).
  Verified by: `pixel-editor.test.ts` → "paints on click and drag"

- [x] AC-02: Eraser tool removes pixels (sets to transparent). Drag erases
  continuously like the pencil.
  Verified by: `pixel-editor.test.ts` → "eraser removes pixels"

- [x] AC-03: Fill bucket tool flood-fills a contiguous region of same-colored
  pixels with the selected color. Diagonal pixels are NOT considered connected
  (4-directional fill only).
  Verified by: `pixel-editor.test.ts` → "fill replaces contiguous region"

- [x] AC-04: Eyedropper tool: clicking any pixel sets the active color to that
  pixel's color and switches the tool back to pencil automatically.
  Verified by: `pixel-editor.test.ts` → "eyedropper picks color and switches to pen"

- [x] AC-05: Undo (Ctrl/Cmd+Z) reverts the last committed stroke. Redo
  (Ctrl/Cmd+Y or Ctrl+Shift+Z) re-applies it. History supports at least
  20 steps.
  Verified by: `pixel-editor.test.ts` → "undo reverts stroke, redo re-applies"

- [x] AC-06: Export button downloads a PNG file. The exported image is exactly
  512×512 pixels (32× scale). Pixels are sharp — no anti-aliasing or blur.
  Transparent cells are transparent in the PNG.
  Verified by: manual inspection of exported file in image editor.

- [x] AC-07: Live preview panel shows the sprite at 1× (16×16px) and 4×
  (64×64px) and updates on every paint action.
  Verified by: visual inspection during testing.

- [x] AC-08: Feature is rendered only when `FLAGS.PIXEL_EDITOR` is true.
  When false, the app renders null.
  Verified by: `pixel-editor.test.ts` → "renders null when flag is off"

### Polish (SHIP_READY gate — not yet started)

- [ ] AC-09: Matches design reference at 375px, 768px, and 1280px
- [ ] AC-10: Keyboard shortcuts work: P pen, E eraser, F fill, I eyedrop, G grid toggle
- [ ] AC-11: Color picker input allows entering any hex value
- [ ] AC-12: Canvas has a visible checkerboard for transparent areas
- [ ] AC-13: Current tool is visually highlighted in the toolbar

---

## Out of Scope

- Layers, animation frames — issue #4
- Undo history persistence across page reloads
- Cloud save / user accounts
- Canvas sizes other than 16×16
- Zoom or pan

---

## API Contract

No backend API. The feature is entirely client-side.

State shape:
```typescript
interface EditorState {
  grid: (string | null)[][]  // 16×16, null = transparent
  history: (string | null)[][][]
  historyIndex: number
  color: string              // hex, e.g. "#ff4757"
  tool: 'pen' | 'eraser' | 'fill' | 'eyedropper'
  showGrid: boolean
}
```

Export output:
- PNG file, 512×512px, nearest-neighbor scaled
- Filename: `sprite.png`

---

## Test Plan

Unit tests (in `pixel-editor.test.ts`):
- Paints pixel on mousedown
- Continuous painting on mousemove while button held
- Eraser sets pixel to null
- Fill replaces contiguous region only
- Fill does not cross color boundaries
- Eyedropper picks color and switches tool to pen
- Undo/redo works for at least 3 steps
- Renders null when flag is off

Manual verification required:
- Export PNG quality (open in image editor, confirm sharp pixels)
- Preview updates in real time
- No lag during fast drag-painting

---

## Design Reference

Design file: not provided — agent to use own judgment for tool layout.
Aesthetic direction: dark IDE-style, functional, no decoration.
Key constraint: total width must fit 680px (single-column layout is acceptable).

---

## Gate Sign-offs

| Gate | Date | Result | Signed By |
|------|------|--------|-----------|
| FUNCTIONAL | 2026-04-20 | PASS | verifier-agent |
| SHIP_READY | | | |

---

## Failure Patterns Learned

- **2026-04-20** **Gate:** FUNCTIONAL (initial attempt — AC-06 FAIL)
  **Pattern:** Export canvas used `scale = 1` (exporting at 16×16px) instead of
  `scale = 32` (512×512px). The test checked that export triggered a download
  but did not assert canvas dimensions. Found only during manual inspection.
  **Future tests should cover:** Assert canvas.width === W * expectedScale and
  canvas.height === H * expectedScale before testing the download URL.

---

## Change Log

- **2026-04-20**: Initial spec written after interview. Added eyedropper (AC-04)
  and multi-scale preview (AC-07) based on interview — these were not in the
  original feature request.
