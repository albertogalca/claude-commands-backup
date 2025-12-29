# Claude Code Commands & Skills

A collection of custom commands and skills for [Claude Code](https://claude.com/claude-code) to enhance your development workflow.

## What's Included

### Commands (11)
Commands are slash commands you invoke manually (e.g., `/commit`, `/review`).

### Skills (10)
Skills are automatically triggered based on your request context.

### Hooks
Pre-configured hooks for enhanced development workflow.

### Settings
Customized Claude Code settings for optimal experience.

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

# Copy hooks to your Claude config (optional)
cp -r claude-commands-backup/hooks/* ~/.claude/hooks/
cd ~/.claude/hooks && npm install

# Copy settings (review and merge with your existing settings)
# Note: backup your existing settings first!
cp ~/.claude/settings.json ~/.claude/settings.json.backup
cp claude-commands-backup/settings.json ~/.claude/settings.json
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

### `/dev-docs`
**Purpose:** Create comprehensive strategic plans with structured task breakdown

Creates a complete planning structure with:
- Executive Summary
- Current State Analysis
- Proposed Future State
- Implementation Phases
- Detailed Tasks with acceptance criteria
- Risk Assessment
- Success Metrics

Automatically creates task management directory structure in `dev/active/[task-name]/` with:
- `[task-name]-plan.md` - The comprehensive plan
- `[task-name]-context.md` - Key files, decisions, dependencies
- `[task-name]-tasks.md` - Checklist for tracking progress

**Usage:**
```bash
/dev-docs <what needs to be planned>
```

**Example:**
```bash
/dev-docs refactor authentication system
```

---

### `/dev-docs-update`
**Purpose:** Update dev documentation before context compaction

Updates development documentation to ensure seamless continuation after context reset:
- Active task state and progress
- Key decisions made this session
- Files modified and why
- Blockers or issues discovered
- Next immediate steps
- Session context and learnings

**Usage:**
```bash
/dev-docs-update
/dev-docs-update <specific context to focus on>
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

### `/route-research-for-testing`
**Purpose:** Map edited routes and launch tests (Laravel-specific)

Automatically identifies modified route files and creates comprehensive tests:
1. Lists changed route files from session
2. Extracts route definitions using `php artisan route:list`
3. Analyzes route structure (methods, middleware, controllers)
4. Generates feature test JSON records
5. Launches route smoke tests

Ideal for ensuring all modified Laravel routes are properly tested.

**Usage:**
```bash
/route-research-for-testing
/route-research-for-testing /extra/path
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

### `swift-development`
**Auto-triggers when:** Building iOS, macOS, watchOS, or tvOS apps with SwiftUI

Provides modern SwiftUI development guidance following Apple's latest architectural recommendations:

**Core Principles:**
- Embrace SwiftUI's declarative nature
- Use native state management (`@State`, `@Observable`, `@Environment`)
- Prefer `async/await` over Combine
- Keep views focused and composable
- Organize by feature, not by type

**Key Patterns:**
- Modern state management with `@Observable` (iOS 17+)
- Lifecycle-aware async work with `.task` modifier
- Simple, focused view composition
- Swift Concurrency (async/await, actors)

**Integrations:**
- Automatically uses Context7 for code generation and documentation

---

### `backend-dev-guidelines`
**Auto-triggers when:** Working with Laravel backend code

Comprehensive Laravel + Inertia.js backend development guide covering:

**Architecture:**
- Layered architecture (routes → controllers → services → repositories)
- Controller patterns (invokable, resource)
- Service layer for business logic
- Repository pattern for complex database operations

**Key Features:**
- Eloquent ORM and relationships
- Form Request validation
- Middleware patterns
- Error tracking and logging
- Inertia.js responses
- Testing strategies (Feature + Unit)

Includes detailed examples and best practices for Laravel backend development.

---

### `node-backend-dev-guidelines`
**Auto-triggers when:** Working with Node.js/Express/TypeScript backend

Comprehensive guide for Node.js/Express/TypeScript microservices:

**Architecture:**
- Layered architecture (routes → controllers → services → repositories)
- BaseController pattern
- Dependency injection
- Async/await error handling

**Key Features:**
- Express APIs
- Prisma database access
- Sentry error tracking
- Zod validation
- Performance monitoring
- Migration from legacy patterns

Covers testing strategies and modern Node.js backend patterns.

---

### `error-tracking`
**Auto-triggers when:** Adding error handling or creating controllers

Enforces comprehensive Sentry v8 error tracking and performance monitoring:

**Critical Rule:**
- ALL ERRORS MUST BE CAPTURED TO SENTRY - no exceptions

**Coverage:**
- Controller error handling
- Artisan commands and Jobs
- Database performance tracking
- Performance spans
- Workflow error tracking

Provides Laravel Sentry SDK integration patterns for complete observability.

---

### `route-tester`
**Auto-triggers when:** Testing Laravel routes or API endpoints

Provides patterns for testing authenticated routes in Laravel:

**Testing Methods:**
- Feature tests with Pest/PHPUnit
- Authentication testing (Sanctum, session)
- Request/response validation
- POST/PUT/DELETE operations

**Authentication Support:**
- Session-based authentication
- Laravel Sanctum (SPA & API tokens)
- Laravel Passport (OAuth2)

Includes comprehensive examples for testing authenticated Laravel routes.

---

### `skill-developer`
**Auto-triggers when:** Creating or modifying Claude Code skills

Expert guide for creating Claude Code skills following Anthropic best practices:

**Coverage:**
- Skill structure and YAML frontmatter
- Trigger patterns (keywords, intent, file paths, content)
- Hook mechanisms (UserPromptSubmit, PreToolUse)
- Enforcement levels (block, suggest, warn)
- Progressive disclosure and the 500-line rule
- Session tracking
- Debugging skill activation

Essential for creating effective, well-structured Claude Code skills.

---

## Hooks

Hooks are shell commands that execute in response to events during Claude Code sessions. This configuration includes several pre-built hooks.

### Available Hooks

#### `skill-activation-prompt.sh`
**Event:** UserPromptSubmit
**Purpose:** Enhances skill activation by providing context about available skills

Automatically triggers when you submit a prompt to help Claude better understand which skills might be relevant.

#### `post-tool-use-tracker.sh`
**Event:** PostToolUse (Edit, MultiEdit, Write)
**Purpose:** Tracks file modifications during the session

Maintains a log of edited files to help with:
- Understanding what changed during a session
- Route testing workflows
- Context documentation

#### `error-handling-reminder.ts` / `error-handling-reminder.sh`
**Purpose:** Reminds about proper error handling patterns

Ensures Sentry error tracking is properly implemented when working on error handling code.

#### `tsc-check.sh`
**Purpose:** TypeScript compilation checks

Validates TypeScript code compilation for projects using TypeScript.

#### `trigger-build-resolver.sh` / `stop-build-check-enhanced.sh`
**Purpose:** Build validation hooks

Ensures builds succeed before certain operations.

### Installing Hooks

```bash
# Copy hooks directory
cp -r claude-commands-backup/hooks/* ~/.claude/hooks/

# Install dependencies (for TypeScript hooks)
cd ~/.claude/hooks && npm install
```

**Note:** Hooks require configuration in `settings.json` to be active. See the Settings section below.

---

## Settings

The repository includes two settings files:

### `settings.json`
Main Claude Code configuration including:
- MCP server enablement (Context7, Figma, Playwright)
- Permission defaults for tools
- Hook configurations

**Key settings:**
```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["playwright", "figma", "context7"],
  "permissions": {
    "allow": ["Edit:*", "Write:*", "MultiEdit:*", "NotebookEdit:*", "Bash:*"],
    "defaultMode": "acceptEdits"
  },
  "hooks": {
    "UserPromptSubmit": [...],
    "PostToolUse": [...]
  }
}
```

### `settings.local.json`
Project-specific permission overrides.

**Important:** Review settings before copying to ensure they match your environment and security requirements.

### Applying Settings

```bash
# Backup existing settings first!
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# Review the settings file
cat claude-commands-backup/settings.json

# Copy if appropriate (or manually merge)
cp claude-commands-backup/settings.json ~/.claude/settings.json
```

---

## Backup & Restore

### Backup Your Config

```bash
# From your Claude config directory
cp -r ~/.claude/commands ~/claude-commands-backup/commands/
cp -r ~/.claude/skills ~/claude-commands-backup/skills/
cp -r ~/.claude/hooks ~/claude-commands-backup/hooks/
cp ~/.claude/settings.json ~/claude-commands-backup/settings.json
cp ~/.claude/settings.local.json ~/claude-commands-backup/settings.local.json

cd ~/claude-commands-backup
git add .
git commit -m "Backup Claude config"
git push
```

### Restore From Backup

```bash
git clone https://github.com/YOUR_USERNAME/claude-commands-backup.git

# Restore commands and skills
cp -r claude-commands-backup/commands/* ~/.claude/commands/
cp -r claude-commands-backup/skills/* ~/.claude/skills/

# Restore hooks (optional)
cp -r claude-commands-backup/hooks/* ~/.claude/hooks/
cd ~/.claude/hooks && npm install

# Restore settings (review first!)
cp ~/.claude/settings.json ~/.claude/settings.json.backup
cp claude-commands-backup/settings.json ~/.claude/settings.json
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
- [Claude Code Infrastructure Showcase](https://github.com/diet103/claude-code-infrastructure-showcase/tree/main) - Example infrastructure and patterns for Claude Code
- [Claude Code is a Beast: Tips from 6 Months of Use](https://www.reddit.com/r/ClaudeCode/comments/1oivs81/claude_code_is_a_beast_tips_from_6_months_of/) - Community insights and best practices
