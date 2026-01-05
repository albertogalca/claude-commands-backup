#!/bin/bash
# Quick verification that global hooks are working from current directory

set -e

echo "🔍 Verifying Global Claude Code Hooks"
echo "======================================"
echo ""
echo "Current directory: $(pwd)"
echo "Home directory: $HOME"
echo ""

# Check global settings exist
if [ -f "$HOME/.claude/settings.json" ]; then
    echo "✅ Global settings found: ~/.claude/settings.json"
else
    echo "❌ Global settings NOT found"
    exit 1
fi

# Check hooks directory
if [ -d "$HOME/.claude/hooks" ]; then
    echo "✅ Hooks directory found: ~/.claude/hooks/"
else
    echo "❌ Hooks directory NOT found"
    exit 1
fi

# Check skill rules
if [ -f "$HOME/.claude/skills/skill-rules.json" ]; then
    echo "✅ Skill rules found: ~/.claude/skills/skill-rules.json"
    skill_count=$(jq '.skills | length' "$HOME/.claude/skills/skill-rules.json")
    echo "   → $skill_count skills configured"
else
    echo "❌ Skill rules NOT found"
    exit 1
fi

# Check dependencies
if ! command -v npx &> /dev/null; then
    echo "⚠️  WARNING: npx not found (needed for TypeScript hooks)"
fi

if [ ! -d "$HOME/.claude/hooks/node_modules" ]; then
    echo "⚠️  WARNING: node_modules not found in hooks directory"
    echo "   Run: cd ~/.claude/hooks && npm install"
fi

echo ""
echo "Testing hooks from current directory..."
echo ""

# Test skill activation hook
test_output=$(echo '{
  "session_id": "verify-test",
  "transcript_path": "/tmp/test.txt",
  "cwd": "'$(pwd)'",
  "permission_mode": "acceptEdits",
  "prompt": "Create a React component with MUI"
}' | "$HOME/.claude/hooks/skill-activation-prompt.sh" 2>&1)

if echo "$test_output" | grep -q "frontend-dev-guidelines"; then
    echo "✅ Skill activation hook working"
    echo "   Detected: frontend-dev-guidelines"
else
    echo "❌ Skill activation hook NOT working"
    echo "   Output: $test_output"
    exit 1
fi

# Test post-tool-use hook
test_dir=$(mktemp -d)
test_file="$test_dir/test.ts"
mkdir -p "$test_dir"

test_output=$(echo '{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "'$test_file'",
    "old_string": "test",
    "new_string": "updated"
  },
  "session_id": "verify-test",
  "cwd": "'$(pwd)'"
}' | CLAUDE_PROJECT_DIR="$test_dir" "$HOME/.claude/hooks/post-tool-use-tracker.sh" 2>&1)

if [ -f "$test_dir/.claude/tsc-cache/verify-test/affected-repos.txt" ]; then
    echo "✅ Post-tool-use hook working"
    echo "   Created tracking cache"
else
    echo "⚠️  Post-tool-use hook may have issues"
fi

# Cleanup
rm -rf "$test_dir"

echo ""
echo "Testing in minimal environment (simulating Claude Code)..."
echo ""

# Test with minimal PATH (like Claude Code uses)
test_output=$(env -i HOME="$HOME" PATH=/usr/bin:/bin bash -c 'echo "{\"session_id\":\"verify-minimal\",\"transcript_path\":\"/tmp/test.txt\",\"cwd\":\"'$(pwd)'\",\"permission_mode\":\"acceptEdits\",\"prompt\":\"create a React component\"}" | ~/.claude/hooks/skill-activation-prompt.sh 2>&1; echo "EXIT:$?"')

if echo "$test_output" | grep -q "EXIT:0"; then
    echo "✅ Hooks work in minimal environment (Claude Code compatible)"
else
    echo "❌ Hooks fail in minimal environment"
    echo "   This might cause 'UserPromptSubmit hook error' in Claude Code"
    echo "   Output: $test_output"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Global hooks are properly configured!"
echo "======================================"
echo ""
echo "Your hooks will work in ALL projects."
echo "No additional setup needed per project."
echo ""
echo "📚 Documentation: ~/.claude/hooks/GLOBAL-SETUP.md"
