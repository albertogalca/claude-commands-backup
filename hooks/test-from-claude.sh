#!/bin/bash
# Test script to help diagnose UserPromptSubmit hook errors
# Run this and share the output to help debug

echo "🔍 Hook Diagnostic Test"
echo "======================="
echo ""

echo "1. Environment Info:"
echo "   Shell: $SHELL"
echo "   PWD: $(pwd)"
echo "   HOME: $HOME"
echo ""

echo "2. Testing hook with minimal environment (like Claude Code):"
result=$(env -i HOME="$HOME" PATH=/usr/bin:/bin bash -c '
  echo "{\"session_id\":\"diagnostic\",\"transcript_path\":\"/tmp/test.txt\",\"cwd\":\"'$(pwd)'\",\"permission_mode\":\"acceptEdits\",\"prompt\":\"test prompt\"}" |
  ~/.claude/hooks/skill-activation-prompt.sh 2>&1
  echo "EXIT_CODE:$?"
')

echo "$result"
echo ""

if echo "$result" | grep -q "EXIT_CODE:0"; then
    echo "✅ Hook works correctly"
else
    echo "❌ Hook failed"
    echo ""
    echo "Error details:"
    echo "$result" | grep -v "EXIT_CODE"
fi

echo ""
echo "3. Testing with React prompt:"
result2=$(env -i HOME="$HOME" PATH=/usr/bin:/bin bash -c '
  echo "{\"session_id\":\"diagnostic\",\"transcript_path\":\"/tmp/test.txt\",\"cwd\":\"'$(pwd)'\",\"permission_mode\":\"acceptEdits\",\"prompt\":\"create a React component\"}" |
  ~/.claude/hooks/skill-activation-prompt.sh 2>&1
  echo "EXIT_CODE:$?"
')

echo "$result2"
echo ""

if echo "$result2" | grep -q "EXIT_CODE:0" && echo "$result2" | grep -q "frontend-dev-guidelines"; then
    echo "✅ Skill detection works"
else
    echo "❌ Skill detection failed"
fi

echo ""
echo "4. Hook file check:"
ls -la ~/.claude/hooks/skill-activation-prompt.sh
echo ""

echo "5. Dependencies check:"
ls -la ~/.claude/hooks/node_modules/.bin/tsx 2>/dev/null || echo "❌ tsx not found - run: cd ~/.claude/hooks && npm install"
echo ""

echo "======================="
echo "Diagnostic complete"
echo "======================="
