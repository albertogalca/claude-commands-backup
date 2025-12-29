#!/usr/bin/env bash
# Disable errors for PATH setup (some paths may not exist)
set +e

# Setup minimal PATH for node - prepend common installation locations
# This works even when Claude Code runs with restrictive environment
PATH="$HOME/.local/share/mise/shims:$PATH"
PATH="$HOME/.local/share/mise/installs/node/22.11.0/bin:$PATH"
PATH="$HOME/.nvm/versions/node/latest/bin:$PATH"
PATH="$HOME/.local/bin:$PATH"
PATH="/opt/homebrew/bin:$PATH"
PATH="/usr/local/bin:$PATH"
export PATH

# Re-enable errors after PATH setup
set -e

# Determine hooks directory
if [ -n "$CLAUDE_PROJECT_DIR" ] && [ -d "$CLAUDE_PROJECT_DIR/.claude/hooks" ]; then
    HOOKS_DIR="$CLAUDE_PROJECT_DIR/.claude/hooks"
else
    HOOKS_DIR="$HOME/.claude/hooks"
fi

# Change to hooks directory
cd "$HOOKS_DIR" || exit 1

# Execute TypeScript hook using local tsx
if [ -x "./node_modules/.bin/tsx" ]; then
    cat | ./node_modules/.bin/tsx skill-activation-prompt.ts
    exit $?
else
    echo "Error: tsx not found in $HOOKS_DIR/node_modules/.bin/" >&2
    echo "Run: cd ~/.claude/hooks && npm install" >&2
    exit 1
fi
