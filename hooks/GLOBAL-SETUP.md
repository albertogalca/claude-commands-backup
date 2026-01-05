# Global Hooks Setup Guide

Your Claude Code hooks are configured **globally** and work across all projects on your machine.

## ✅ Current Global Setup

### File Locations

```
~/.claude/
├── settings.json           # Global settings with hook configurations
├── hooks/                  # Global hook scripts
│   ├── skill-activation-prompt.sh
│   ├── skill-activation-prompt.ts
│   ├── post-tool-use-tracker.sh
│   ├── package.json
│   └── node_modules/
└── skills/
    └── skill-rules.json    # Global skill definitions
```

### How It Works

1. **Global Settings** (`~/.claude/settings.json`):
   - Hooks use absolute paths: `/Users/albertogallegocastro/.claude/hooks/...`
   - These paths work from **any project directory**

2. **Skill Rules Priority**:
   - First checks: `$CLAUDE_PROJECT_DIR/.claude/skills/skill-rules.json` (project-specific)
   - Falls back to: `~/.claude/skills/skill-rules.json` (global)

3. **Hook Execution**:
   - UserPromptSubmit: Runs on every prompt, suggests relevant skills
   - PostToolUse: Tracks edited files and repositories after Edit/Write operations

## 🔧 Per-Project Customization (Optional)

If you want **different skill rules** for specific projects:

### Option 1: Override Entire Skill Rules

Create project-specific rules:

```bash
cd /path/to/your/project
mkdir -p .claude/skills
cp ~/.claude/skills/skill-rules.json .claude/skills/skill-rules.json
# Edit .claude/skills/skill-rules.json for this project
```

### Option 2: Project-Specific Hooks

Override hooks for a specific project:

```bash
cd /path/to/your/project
mkdir -p .claude

# Create project settings
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/custom-hook.sh"
          }
        ]
      }
    ]
  }
}
EOF
```

### Option 3: Extend Global Skills

Keep global skills but add project-specific ones by modifying the skill-activation-prompt.ts to merge both files.

## 📋 Current Skills

Your global skills (from `~/.claude/skills/skill-rules.json`):

- **skill-developer** (suggest, high): Meta-skill for skill system work
- **backend-dev-guidelines** (suggest, high): Laravel + Inertia.js backend patterns
- **frontend-dev-guidelines** (suggest, high): React/TypeScript + MUI v7 patterns
- **route-tester** (suggest, high): API route testing with authentication
- **error-tracking** (suggest, high): Sentry error tracking patterns

## 🧪 Testing

Test hooks from any project:

```bash
cd /path/to/any/project

# Test skill activation
echo '{
  "session_id": "test",
  "transcript_path": "/tmp/test.txt",
  "cwd": "'$(pwd)'",
  "permission_mode": "acceptEdits",
  "prompt": "Create a React component"
}' | ~/.claude/hooks/skill-activation-prompt.sh 2>&1
```

Expected output: `[DEBUG] Suggested skills: frontend-dev-guidelines`

## 🔍 Debugging

- **Hook output**: Check stderr for `[DEBUG]` messages
- **Hook errors**: Will appear as "UserPromptSubmit hook error" in Claude Code
- **Verify hook execution**: Add `echo "Hook running" >&2` to shell scripts

## 📝 Adding New Skills

Edit `~/.claude/skills/skill-rules.json`:

```json
{
  "version": "1.0",
  "skills": {
    "your-new-skill": {
      "type": "domain",
      "enforcement": "suggest",
      "priority": "high",
      "promptTriggers": {
        "keywords": ["your", "keywords"],
        "intentPatterns": ["your.*regex.*patterns"]
      }
    }
  }
}
```

Skill triggers automatically across all projects!

## ⚙️ Configuration Settings

### Enforcement Levels

- **suggest**: Silent debug log (recommended for most skills)
- **warn**: Shows warning but allows proceeding
- **block**: Blocks execution until skill is used (use sparingly!)

### Priority Levels

- **critical**: Always trigger when matched
- **high**: Trigger for most matches
- **medium**: Trigger for clear matches
- **low**: Trigger only for explicit matches

## 🎯 Best Practices

1. **Keep most skills at "suggest"** - avoid interrupting the user
2. **Use "block" only for critical guardrails** (e.g., security issues)
3. **Test skills before deploying** globally
4. **Document project-specific overrides** in project README
5. **Use descriptive skill names** that match your actual skills in `.claude/skills/`

---

Last updated: 2025-12-29
