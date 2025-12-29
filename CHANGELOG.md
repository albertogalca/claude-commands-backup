# Changelog

## 2025-12-29 - Critical Hook Fix

### Fixed: UserPromptSubmit Hook Error

**Problem:**
The `skill-activation-prompt` hook was failing with error:
```
Error: ENOENT: no such file or directory, open '/path/to/project/.claude/skills/skill-rules.json'
```

This occurred because when Claude Code set `CLAUDE_PROJECT_DIR` environment variable, the hook tried to load project-specific skill rules that didn't exist, instead of falling back to global rules.

**Solution:**
Updated `hooks/skill-activation-prompt.ts` to:
1. Default to global skill rules (`~/.claude/skills/skill-rules.json`)
2. Check if project-specific rules exist before trying to load them
3. Gracefully fall back to global rules if project-specific don't exist

**Files Updated:**
- `hooks/skill-activation-prompt.ts` - Added `existsSync` check and fallback logic (lines 43-58)
- `hooks/skill-activation-prompt.sh` - Simplified PATH setup, removed complex nvm calls
- `hooks/TROUBLESHOOTING.md` - Documented the fix
- `hooks/GLOBAL-SETUP.md` - Created comprehensive global setup documentation
- `hooks/QUICK-REFERENCE.md` - Added quick reference guide
- `hooks/verify-global-setup.sh` - Added verification script with minimal env test
- `hooks/test-from-claude.sh` - Added diagnostic test script
- `hooks/skill-activation-prompt-debug.sh` - Added debug wrapper for troubleshooting
- `skills/skill-rules.json` - Changed `frontend-dev-guidelines` from `"enforcement": "block"` to `"enforcement": "suggest"`

**Testing:**
All tests pass:
```bash
~/Projects/claude-commands-backup/hooks/verify-global-setup.sh
```

**Impact:**
- Hooks now work globally across ALL projects
- No interruptions for suggested skills (only stderr debug logs)
- Proper fallback from project-specific to global skill rules
- Works in minimal environment (simulating Claude Code's restricted PATH)

---

## Previous Updates

See git history for previous changes.
