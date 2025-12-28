---
description: Comprehensive code review with testing and quality checks
---
# Code Review

Review the current changes for quality, correctness, and best practices.

## Process

1. Run `git status` and `git diff` in parallel to see changes
2. Ask what the purpose of these changes is
3. Run tests, type checking, and linting in parallel
4. Review the changes focusing on:
   - Correctness and bugs
   - Security vulnerabilities
   - Performance issues
   - Maintainability and architecture
   - Consistency with codebase patterns

## Output

Organize findings by severity:
- 🔴 **CRITICAL** - Must fix (bugs, security, breaking changes)
- 🟡 **SUGGESTED** - Should fix (performance, maintainability)
- ℹ️ **NOTES** - Consider (style, minor improvements)

For each issue provide:
- Specific location (file:line)
- What's wrong and why
- Suggested fix
- Impact if not addressed

End with verdict: Approve / Approve with notes / Request changes
