# Claude Code Commands & Skills

A collection of custom commands and skills for [Claude Code](https://claude.com/claude-code) to enhance your development workflow.

## What's Included

### Commands (8)
Commands are slash commands you invoke manually (e.g., `/commit`, `/review`).

### Skills (3)
Skills are automatically triggered based on your request context.

---

## Installation

### Quick Install

```bash
# Clone this repository
git clone https://github.com/YOUR_USERNAME/claude-commands-backup.git

# Copy commands to your Claude config
cp -r claude-commands-backup/commands/* ~/.claude/commands/

# Copy skills to your Claude config
cp -r claude-commands-backup/skills/* ~/.claude/skills/
```

### Manual Install

1. Create directories if they don't exist:
   ```bash
   mkdir -p ~/.claude/commands ~/.claude/skills
   ```

2. Copy individual commands or skills you want:
   ```bash
   cp claude-commands-backup/commands/review.md ~/.claude/commands/
   cp -r claude-commands-backup/skills/creating-landing-pages ~/.claude/skills/
   ```

---

## Commands

### `/bug-analysis`
**Purpose:** Analyze bugs with structured reporting

Creates a comprehensive bug analysis report including:
- Environment details and reproduction steps
- Expected vs actual behavior
- Logs and error messages
- Root cause hypotheses
- Debugging recommendations

**Usage:**
```bash
/bug-analysis <description of the bug>
```

---

### `/commit`
**Purpose:** Git commit helper with conventional commits

Features:
- Runs pre-commit checks (linting, building, docs)
- Auto-stages files if none are staged
- Suggests commit splits for complex changes
- Uses conventional commit format with emojis
- Encourages atomic commits

**Usage:**
```bash
/commit
/commit --no-verify  # Skip pre-commit hooks
```

**Example commits:**
- `✨ feat: add user authentication system`
- `🐛 fix: resolve memory leak in rendering process`
- `📝 docs: update API documentation`

---

### `/debug`
**Purpose:** Systematic debugging with root cause analysis

Process:
1. Reproduce the issue and capture errors
2. Investigate root cause (errors, logs, recent changes)
3. Apply minimal, focused fix
4. Validate with tests and manual testing
5. Add regression prevention tests

**Debugging strategies:**
- **Failing tests:** Check expectations, run in isolation
- **Runtime errors:** Follow stack trace, check variable states
- **Logic bugs:** Trace data transformations, check boundaries
- **Performance:** Profile hot paths, identify N+1 queries
- **Integration:** Verify API contracts, test in isolation

**Usage:**
```bash
/debug
/debug <specific-area>
```

---

### `/refactor`
**Purpose:** Large-scale refactoring with phased execution

Strategy:
- Small phases (change one thing at a time)
- Continuous testing (validate after each phase)
- Type-driven (let compiler catch breaks)
- Reversible (each phase can be rolled back)

Process:
1. Analyze scope and dependencies
2. Plan incremental phases
3. Establish test baseline
4. Execute phases with validation
5. Cleanup and final review
6. Report summary

**Usage:**
```bash
/refactor
/refactor <specific-area>
```

---

### `/research`
**Purpose:** Research codebase and external docs

Combines:
- Codebase analysis (patterns, implementations, file references)
- External documentation (best practices, examples, pitfalls)
- Gap analysis (current state vs recommendations)

Delivers actionable recommendations with specific references.

**Usage:**
```bash
/research
/research <specific-topic>
```

---

### `/review`
**Purpose:** Comprehensive code review with testing

Process:
1. Gather context (`git status`, `git diff`)
2. Run automated checks (tests, types, linting)
3. Manual review focusing on:
   - Correctness and bugs
   - Security vulnerabilities
   - Performance issues
   - Maintainability
   - Consistency with codebase

Output organized by severity:
- 🔴 **CRITICAL** - Must fix
- 🟡 **SUGGESTED** - Should fix
- ℹ️ **NOTES** - Consider

**Usage:**
```bash
/review
/review <specific-files>
```

---

### `/rmslop`
**Purpose:** Remove AI-generated code patterns

Removes:
- Unnecessary comments inconsistent with codebase
- Extra defensive checks or try/catch blocks
- Type casts to `any` to bypass type issues
- Any style inconsistent with the file

**Usage:**
```bash
/rmslop
```

---

### `/test`
**Purpose:** Write comprehensive tests (TDD or verification)

Supports two modes:
- **TDD:** Write tests first, then implementation
- **Verification:** Test existing code

Test priorities:
- **Must test:** Core logic, public APIs, error handling, security
- **Should test:** Edge cases, integration points, data transformations
- **Skip:** Trivial getters/setters, framework code, third-party libs

**Usage:**
```bash
/test
/test <specific-files>
```

---

## Skills

Skills are automatically triggered when your request matches their description.

### `creating-landing-pages`
**Auto-triggers when:** Creating landing pages, marketing sites, product pages

Creates distinctive, award-winning landing pages as single-file HTML with embedded CSS/JS. Generates production-ready marketing pages with bold typography, orchestrated animations, and memorable aesthetics. Avoids generic AI patterns.

---

### `frontend-design`
**Auto-triggers when:** Building web components, pages, or applications

Creates distinctive, production-grade frontend interfaces with exceptional design quality. Focuses on:

**Design Thinking:**
- Bold aesthetic direction (minimal, maximalist, retro-futuristic, brutalist, etc.)
- Purpose-driven design that solves real problems
- Unforgettable differentiation

**Frontend Aesthetics:**
- **Typography:** Distinctive, characterful fonts (avoiding generic choices)
- **Color:** Cohesive themes with CSS variables, dominant colors with sharp accents
- **Motion:** High-impact animations, orchestrated page loads, scroll-triggered effects
- **Spatial Composition:** Unexpected layouts, asymmetry, generous negative space
- **Visual Details:** Gradient meshes, noise textures, geometric patterns, custom cursors

**Implementation:**
- Production-grade, functional code
- Visually striking and memorable
- Matches implementation complexity to aesthetic vision
- Avoids generic "AI slop" aesthetics

Works with HTML/CSS/JS, React, Vue, and other frameworks.

---

### `typescript-advanced-types`
**Auto-triggers when:** Working with advanced TypeScript types

Provides expert guidance on TypeScript's type system including:
- Generics and constraints
- Conditional types
- Mapped types
- Template literal types
- Type inference patterns
- Utility types

---

## Backup & Restore

### Backup Your Config

```bash
# From your Claude config directory
cp -r ~/.claude/commands ~/claude-commands-backup/commands/
cp -r ~/.claude/skills ~/claude-commands-backup/skills/
cd ~/claude-commands-backup
git add .
git commit -m "Backup Claude config"
git push
```

### Restore From Backup

```bash
git clone https://github.com/YOUR_USERNAME/claude-commands-backup.git
cp -r claude-commands-backup/commands/* ~/.claude/commands/
cp -r claude-commands-backup/skills/* ~/.claude/skills/
```

---

## Creating Custom Commands

Commands are markdown files in `~/.claude/commands/` with YAML frontmatter:

```markdown
---
description: Brief description of what this command does
---
# Command Name

Instructions for Claude on how to execute this command.

You can reference $ARGUMENTS for user-provided input.
```

**Example:**

```markdown
---
description: Format code with prettier
---
# Format Code

Run prettier on $ARGUMENTS (or all files if not specified).

1. Run `prettier --write <files>`
2. Report what was formatted
```

---

## Creating Custom Skills

Skills are directories in `~/.claude/skills/` with a `SKILL.md` file:

```yaml
---
name: your-skill-name
description: What it does and when to use it (triggers automatic activation)
---

# Skill Name

Instructions for Claude on how to use this skill.
```

**Best practices:**
- Make descriptions specific with trigger keywords
- Keep SKILL.md under 500 lines
- Use supporting files for complex skills
- Restrict tools with `allowed-tools` if needed

---

## Project-Specific Setup

To share commands/skills with your team, create `.claude/` in your project root:

```bash
mkdir -p .claude/commands .claude/skills
cp ~/.claude/commands/review.md .claude/commands/
git add .claude/
git commit -m "Add Claude Code config"
```

**Priority:** Enterprise > Personal (`~/.claude/`) > Project (`.claude/`) > Plugin

---

## Troubleshooting

**Command not found?**
- Ensure file is in `~/.claude/commands/` or `.claude/commands/`
- Check file has `.md` extension
- Verify YAML frontmatter is valid

**Skill not triggering?**
- Make description more specific with trigger keywords
- Check YAML frontmatter starts on line 1
- Ensure file is named `SKILL.md`

**Need to see available commands/skills?**
Ask Claude: "What commands are available?" or "What skills are available?"

---

## Contributing

Feel free to submit issues or pull requests with:
- New commands
- New skills
- Improvements to existing commands/skills
- Documentation updates

---

## License

MIT - Feel free to use and modify for your own workflow.

---

## Resources

- [Claude Code Documentation](https://code.claude.com/docs)
- [Claude Code Skills Guide](https://code.claude.com/docs/en/skills.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
