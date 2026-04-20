# Changelog

This file tracks changes to both the agent system configuration and the
application codebase. It serves two purposes:

1. **System customizations** - when you fork and modify the agent system
   (prompt files, schemas, scripts), record those changes here so you can
   identify what diverges from upstream and why.

2. **Application releases** - a human-readable history of what shipped and when.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- Restored the root as a reusable agent-system template.
- Added stdlib-only tests and a beginner smoke demo.

### Changed
- Moved TaskFlow-specific artifacts into `examples/task-app/`.
- Restored control-plane files under `.agents/`.

### Fixed
- Missing helper script imports and documented command paths.

### Agent System Customizations
_Record any changes to .agents/ prompt files, schemas, or scripts here.
Include the prompt hash before and after so you can track drift from upstream._

-

---

## How to use this file

**For application changes:**
When you merge a feature to `develop` or `main`, add an entry here.
Do not wait until release - record when things land, not when they ship.
The gate artifacts in `.agents/gates/` give you the detail; this file gives
you the narrative.

```markdown
## [0.2.0] - 2026-05-01

### Added
- User authentication (email/password) - issue #12
- Task creation feature - issue #14

### Fixed
- Session token expiry was not refreshed on API calls - issue #17
```

**For agent system customizations:**
When you edit any file in `.agents/` that came from the upstream template,
record it here with the original prompt hash and the new hash (get the new
hash by running `python .agents/scripts/prompt-hash.py`). This makes it
easy to audit what you changed when pulling in upstream improvements.

```markdown
### Agent System Customizations
- Modified `.agents/FEATURE_AGENT.md`: added company-specific coding standards
  section. Old hash: `a1b2c3d4e5f6`. New hash: `7890abcdef12`.
  Reason: enforce internal TypeScript patterns not in the base template.
```

**Why this matters:**
The prompt hash system in `STATE.json` detects when prompts have changed
between sessions. This changelog is the companion record that explains *why*
they changed - so future you (or a new team member) understands the intent
behind the customization.

---

## [0.1.0] - [YYYY-MM-DD]

### Added
- Initial project setup via bootstrap.py
- Agent system configured for [PROJECT NAME]

### Agent System Customizations
- None - running base template at initialization.
  Prompt hashes recorded in `.agents/STATE.json`.
