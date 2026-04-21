#!/usr/bin/env bash
# Reproducible "Day 0 + Day 1" for terminal recording (non-interactive).
# Usage: from Dev-Agent-System template repo root:
#   bash Dev-Agent-System-Demo/recordings/run-noninteractive-demo.sh
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "error: run from inside the Dev-Agent-System git repo (or set ROOT manually)." >&2
  exit 1
fi

OUT="${PIXELFORGE_DEMO_OUT:-/tmp/pixelforge-demo}"
rm -rf "${OUT}"

echo "==> new-project.py -> ${OUT}"
python "${ROOT}/.agents/scripts/new-project.py" \
  --name "PixelForge" \
  --description "Pixel art editor for indie devs" \
  --type "Web App" \
  --frontend "React, TypeScript, Vite" \
  --backend "None" \
  --output-dir "${OUT}"

echo "==> new-feature.py (pixel-editor)"
python "${OUT}/.agents/scripts/new-feature.py" \
  --name pixel-editor \
  --issue 1 \
  --quiet

echo "==> done. Project at: ${OUT}"
echo "    Next: copy agent narrative artifacts from Dev-Agent-System-Demo/ or merge envelopes as in your real run."
