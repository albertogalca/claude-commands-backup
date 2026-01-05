# Troubleshooting Guide

## Common Issues and Solutions

### Issue: "UserPromptSubmit hook error" in Claude Code (SOLVED)

**Recent Fix (2025-12-29):**
The hook was failing because it tried to load skill-rules.json from the project directory when `CLAUDE_PROJECT_DIR` was set, but didn't fall back to the global rules file when the project-specific one didn't exist.

**Fix Applied:**
The TypeScript code now properly checks if a project-specific skill-rules.json exists before trying to load it. If it doesn't exist, it automatically falls back to the global `~/.claude/skills/skill-rules.json`.

**File Updated:** `/Users/albertogallegocastro/.claude/hooks/skill-activation-prompt.ts` (lines 43-58)

---

### Issue: "UserPromptSubmit hook error" - General Troubleshooting

**Symptoms:**
- Claude Code shows "UserPromptSubmit hook error" when you type prompts
- Hook works when tested manually in terminal
- Error appears inconsistently or on all prompts

**Root Cause:**
Claude Code runs hooks in a minimal shell environment with a restricted PATH. Node.js installed via nvm, mise, or other version managers may not be in the PATH, causing the hook to fail.

**Solution (FIXED in current version):**
The hook script now sets up PATH to include common node installation locations:
- mise shims: `~/.local/share/mise/shims`
- nvm installations: `~/.nvm/versions/node/*/bin`
- Homebrew: `/opt/homebrew/bin`, `/usr/local/bin`
- User binaries: `~/.local/bin`

**File:** `/Users/albertogallegocastro/.claude/hooks/skill-activation-prompt.sh`

Lines 4-13 handle PATH setup:
```bash
# Setup PATH for node/npm/npx - needed when Claude Code runs with minimal environment
export PATH="$HOME/.local/share/mise/shims:$PATH"
export PATH="$HOME/.nvm/versions/node/$(nvm version 2>/dev/null || echo "latest")/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export PATH="/opt/homebrew/bin:$PATH"
export PATH="/usr/local/bin:$PATH"

# Load nvm if available (for shells that use it)
[ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh" --no-use 2>/dev/null || true
```

**Verify the fix:**
```bash
~/.claude/hooks/verify-global-setup.sh
```

This tests hooks in both normal and minimal environments.

---

### Issue: Hook output causes interruptions

**Symptoms:**
- Every prompt shows hook notification
- Skill suggestions appear as interruptions
- User experience is disrupted

**Root Cause:**
When UserPromptSubmit hooks output to stdout, Claude Code shows it to the user as a notification/interruption.

**Solution (FIXED in current version):**
The hook now only outputs to stdout for blocking (`enforcement: "block"`) skills. Suggested skills are logged silently to stderr for debugging.

**File:** `/Users/albertogallegocastro/.claude/hooks/skill-activation-prompt.ts`

Lines 86-110:
```typescript
// Only output for blocking skills - suggestions should be silent
const blockingSkills = matchedSkills.filter(s => s.config.enforcement === 'block');

if (blockingSkills.length > 0) {
    // Output notification for blocking skills
    console.log(output);
}

// For non-blocking skills, log silently to stderr
const suggestedSkills = matchedSkills.filter(s => s.config.enforcement !== 'block');
if (suggestedSkills.length > 0) {
    const skillNames = suggestedSkills.map(s => s.name).join(', ');
    console.error(`[DEBUG] Suggested skills: ${skillNames}`);
}
```

**Configuration:** `/Users/albertogallegocastro/.claude/skills/skill-rules.json`

All skills should use `"enforcement": "suggest"` unless you want to block execution:
```json
{
  "your-skill": {
    "type": "domain",
    "enforcement": "suggest",  // ← Use "suggest" not "block"
    "priority": "high"
  }
}
```

---

### Issue: Hooks don't work in specific project

**Symptoms:**
- Hooks work globally but fail in one project
- Different behavior in different directories

**Possible Causes:**

1. **Project-specific settings override global hooks**
   - Check: `<project>/.claude/settings.json`
   - Solution: Remove project settings or merge with global

2. **Node/npm not available in project environment**
   - Check: Can you run `node --version` in the project?
   - Solution: Install node or fix PATH

3. **Permission issues**
   - Check: `ls -la ~/.claude/hooks/*.sh`
   - Solution: `chmod +x ~/.claude/hooks/*.sh`

---

### Issue: Skills not triggering

**Symptoms:**
- Hook runs successfully but doesn't detect skills
- Expected skill not suggested

**Debug Steps:**

1. **Check keyword matching:**
   ```bash
   jq '.skills["SKILL_NAME"].promptTriggers.keywords' ~/.claude/skills/skill-rules.json
   ```

2. **Test manual trigger:**
   ```bash
   echo '{
     "session_id": "test",
     "transcript_path": "/tmp/test.txt",
     "cwd": "'$(pwd)'",
     "permission_mode": "acceptEdits",
     "prompt": "YOUR PROMPT HERE"
   }' | ~/.claude/hooks/skill-activation-prompt.sh 2>&1
   ```

3. **Check for typos in skill-rules.json:**
   - Keyword matching is case-insensitive
   - Intent patterns use regex - test them carefully

---

### Issue: Dependencies missing

**Symptoms:**
- `npx: command not found`
- `tsx: not found`
- Hook fails with exit code 127

**Solution:**
```bash
cd ~/.claude/hooks
npm install
```

**Verify:**
```bash
ls -la ~/.claude/hooks/node_modules/.bin/tsx
```

Should show a symlink to tsx.

---

### Issue: Hook takes too long

**Symptoms:**
- Delay before Claude Code responds
- Timeout errors

**Possible Causes:**

1. **Complex skill rules with many regex patterns**
   - Solution: Simplify patterns, use simple keywords

2. **Slow TypeScript compilation**
   - Not applicable - we use tsx which is fast

3. **Network issues with npx**
   - Solution: Use local tsx (already configured)

---

## Testing Hooks

### Test in your current environment
```bash
~/.claude/hooks/verify-global-setup.sh
```

### Test specific prompt
```bash
echo '{
  "session_id": "test",
  "transcript_path": "/tmp/test.txt",
  "cwd": "'$(pwd)'",
  "permission_mode": "acceptEdits",
  "prompt": "YOUR TEST PROMPT"
}' | ~/.claude/hooks/skill-activation-prompt.sh 2>&1
```

### Test in minimal environment (simulates Claude Code)
```bash
env -i HOME="$HOME" PATH=/usr/bin:/bin bash -c '
  echo "{\"session_id\":\"test\",\"transcript_path\":\"/tmp/test.txt\",\"cwd\":\"'$(pwd)'\",\"permission_mode\":\"acceptEdits\",\"prompt\":\"test prompt\"}" |
  ~/.claude/hooks/skill-activation-prompt.sh 2>&1
  echo "Exit: $?"
'
```

Should exit with code 0.

---

## Debug Mode

Enable verbose logging:

```bash
# Edit skill-activation-prompt.ts
# Change console.error to console.log for debugging

# Or run hook manually with debug output
bash -x ~/.claude/hooks/skill-activation-prompt.sh <<< '...'
```

---

## Getting Help

1. Check this troubleshooting guide
2. Run verification: `~/.claude/hooks/verify-global-setup.sh`
3. Check Claude Code logs
4. Test hook manually with debug output

---

Last updated: 2025-12-29
