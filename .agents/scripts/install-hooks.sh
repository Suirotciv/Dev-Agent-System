#!/bin/bash
# install-hooks.sh
# Installs the agent-system validation pre-commit hook.
#
# Usage: bash .agents/scripts/install-hooks.sh
#
# The hook runs validate-agent-artifacts.py before every commit.
# It blocks the commit if any artifact is invalid, preventing corrupted
# state from entering git history.
#
# To uninstall: rm .git/hooks/pre-commit

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SOURCE="$SCRIPTS_DIR/pre-commit-hook"
REPO_ROOT="$(git -C "$SCRIPTS_DIR" rev-parse --show-toplevel 2>/dev/null || echo "")"

if [ -z "$REPO_ROOT" ]; then
  echo "error: could not find git repo root from $SCRIPTS_DIR"
  exit 1
fi

HOOKS_DIR="$REPO_ROOT/.git/hooks"
HOOK_DEST="$HOOKS_DIR/pre-commit"

if [ ! -f "$HOOK_SOURCE" ]; then
  echo "error: pre-commit-hook not found at $HOOK_SOURCE"
  exit 1
fi

if [ -f "$HOOK_DEST" ]; then
  echo "  pre-commit hook already exists at $HOOK_DEST"
  read -r -p "  Overwrite? [y/N]: " answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "  Keeping existing hook."
    exit 0
  fi
fi

cp "$HOOK_SOURCE" "$HOOK_DEST"
chmod +x "$HOOK_DEST"
echo "  OK pre-commit hook installed at $HOOK_DEST"
echo ""
echo "  The hook runs .agents/scripts/validate-agent-artifacts.py"
echo "  before every commit. Commits are blocked if artifacts are invalid."
echo ""
echo "  To disable temporarily:  git commit --no-verify"
echo "  To uninstall:             rm $HOOK_DEST"
