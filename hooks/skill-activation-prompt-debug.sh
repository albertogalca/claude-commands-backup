#!/usr/bin/env bash
# Debug wrapper for skill-activation-prompt
# This logs all input/output to help diagnose issues

LOG_FILE="$HOME/.claude/hooks/debug.log"

{
    echo "=== $(date) ==="
    echo "PWD: $PWD"
    echo "SHELL: $SHELL"
    echo "PATH: $PATH"
    echo "CLAUDE_PROJECT_DIR: $CLAUDE_PROJECT_DIR"
    echo "Input:"

    # Read stdin into a variable
    input=$(cat)
    echo "$input"
    echo ""

    # Run the actual hook
    echo "Running hook..."
    echo "$input" | ~/.claude/hooks/skill-activation-prompt.sh 2>&1
    exit_code=$?

    echo "Exit code: $exit_code"
    echo ""
} >> "$LOG_FILE" 2>&1

# Exit with the same code as the hook
exit $exit_code
