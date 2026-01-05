# Quick Reference: Global Claude Code Hooks

## ✅ Your Setup (Already Working Globally!)

Your hooks are configured in `~/.claude/settings.json` with **absolute paths**, which means they work from **any project directory** on your machine.

## 🚀 Quick Commands

### Verify hooks are working (from any directory)
```bash
~/.claude/hooks/verify-global-setup.sh
```

### View current configuration
```bash
cat ~/.claude/settings.json | jq '.hooks'
```

### List configured skills
```bash
jq '.skills | keys' ~/.claude/skills/skill-rules.json
```

### Test skill activation manually
```bash
echo '{
  "session_id": "test",
  "transcript_path": "/tmp/test.txt",
  "cwd": "'$(pwd)'",
  "permission_mode": "acceptEdits",
  "prompt": "YOUR TEST PROMPT HERE"
}' | ~/.claude/hooks/skill-activation-prompt.sh 2>&1
```

## 📂 File Locations

```
~/.claude/
├── settings.json                    # Global Claude settings
├── hooks/
│   ├── skill-activation-prompt.sh   # UserPromptSubmit hook
│   ├── skill-activation-prompt.ts   # TypeScript logic
│   ├── post-tool-use-tracker.sh     # PostToolUse hook
│   ├── verify-global-setup.sh       # Verification script
│   ├── GLOBAL-SETUP.md              # Detailed documentation
│   └── QUICK-REFERENCE.md           # This file
└── skills/
    └── skill-rules.json             # Skill definitions
```

## 🔧 Common Tasks

### Add a new skill globally
```bash
# Edit skill rules
code ~/.claude/skills/skill-rules.json

# Or use your preferred editor
vim ~/.claude/skills/skill-rules.json
```

### Update hook behavior
```bash
# Edit TypeScript logic
code ~/.claude/hooks/skill-activation-prompt.ts

# Rebuild (no build step needed - tsx runs TypeScript directly)
```

### Check hook logs
Debug output goes to stderr. Run hooks manually to see:
```bash
echo '{"session_id":"test","transcript_path":"/tmp/test.txt","cwd":"'$(pwd)'","permission_mode":"acceptEdits","prompt":"test"}' \
  | ~/.claude/hooks/skill-activation-prompt.sh 2>&1
```

## 🎯 Skill Configuration

Your current skills (edit in `~/.claude/skills/skill-rules.json`):

1. **skill-developer** - Skill system development
2. **backend-dev-guidelines** - Laravel backend patterns
3. **frontend-dev-guidelines** - React/TypeScript frontend patterns
4. **route-tester** - API route testing
5. **error-tracking** - Sentry error tracking

### Enforcement Levels
- `suggest`: Silent (logs to stderr only) ← **Recommended**
- `warn`: Shows warning but continues
- `block`: Blocks execution until skill is used

### Priority Levels
- `critical`: Always trigger
- `high`: Trigger for most matches
- `medium`: Trigger for clear matches
- `low`: Trigger only for explicit matches

## 🔍 Troubleshooting

### Hooks not running?
```bash
# Check settings
cat ~/.claude/settings.json | jq '.hooks'

# Verify hook files exist and are executable
ls -la ~/.claude/hooks/*.sh

# Make sure they're executable
chmod +x ~/.claude/hooks/*.sh
```

### Dependencies missing?
```bash
cd ~/.claude/hooks
npm install
```

### Skill not triggering?
Check keyword and intent patterns in `~/.claude/skills/skill-rules.json`:
```bash
jq '.skills["SKILL_NAME"].promptTriggers' ~/.claude/skills/skill-rules.json
```

## 📚 More Info

- **Full Documentation**: `~/.claude/hooks/GLOBAL-SETUP.md`
- **Hook Config**: `~/.claude/hooks/CONFIG.md`
- **Hook Examples**: `~/.claude/hooks/README.md`

---

**Remember**: Your hooks work globally across ALL projects. No per-project setup needed! 🎉
