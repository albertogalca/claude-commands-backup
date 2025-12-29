#!/bin/bash
set -e

# Use HOME for global hooks, fallback to CLAUDE_PROJECT_DIR for project-specific
HOOKS_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/hooks"
if [ ! -d "$HOOKS_DIR" ]; then
    HOOKS_DIR="$HOME/.claude/hooks"
fi

cd "$HOOKS_DIR"
cat | npx tsx skill-activation-prompt.ts
