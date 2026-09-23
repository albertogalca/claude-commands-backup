---
name: commit
description: Create atomic git commits with conventional-commit messages and a leading emoji. Runs pre-commit checks, stages what is unstaged, and splits unrelated work into separate commits. Use when the user says "commit", "commit this", "commit my changes", or runs /commit.
model: sonnet
---

# commit

Turn the current working tree into one or more well-formed commits.

## Arguments

- omitted — full run: checks, stage, split, commit.
- `--no-verify` — skip the pre-commit checks in step 1.
- Anything else — treat it as the intended message or scope hint.

## Steps

1. **Pre-commit checks** (skip on `--no-verify`). Run whatever the repo already
   defines: lint, typecheck, build, format. Read `package.json` scripts, the
   `Makefile`, or the project's CLAUDE.md. If a check fails, fix it or stop and
   report. Never commit over a red build.

2. **See the change.** `git status --short`, then `git diff --staged` and
   `git diff`. If nothing is staged, stage the files that belong to this work
   (`git add`). Never `git add -A` blindly: read the list first and leave out
   build output, secrets, and scratch files.

3. **Split.** Group the diff into atomic commits, one logical change each.
   Split when the diff mixes different types (a fix plus a refactor), touches
   unrelated areas, or the message would need the word "and" twice. Do not split
   a change from the test that covers it. Stage and commit each group in turn.

4. **Write the message.**

   ```
   <emoji> <type>(<scope>): <description>

   [body: why, not what. wrap at 72.]

   [footer: refs, breaking changes]
   ```

   - Imperative mood, lowercase description, no trailing period.
   - Scope is optional. Use it when it names a real area of the repo.
   - Body only when the why is not obvious from the subject. One-line changes
     need no body.
   - End every message with the `Co-Authored-By` line the harness gives for
     the current model.

5. **Commit**, then `git log --oneline -n <count>` to confirm. Do not push
   unless asked. If on the default branch and the user asked for a branch or a
   PR, branch first.

## Types and emoji

| Emoji | Type | For |
|---|---|---|
| ✨ | feat | new capability |
| 🐛 | fix | broken behavior now works |
| 📝 | docs | documentation only |
| 💄 | style | formatting, copy, visual detail, no logic change |
| ♻️ | refactor | same behavior, different code |
| ⚡️ | perf | speed or memory |
| ✅ | test | tests added or changed |
| 🔧 | chore | config, tooling, deps, housekeeping |
| 👷 | ci | pipelines and build scripts |
| ⏪️ | revert | undo a previous commit |

## Rules

- Message language is English, always, whatever language the conversation is in.
- Describe user-facing behavior where there is any. "fix: overwriting inside a
  protected folder no longer fails the batch" beats "fix: replaceItemAt error".
- Never mention the tooling that produced the change.
- No em dashes.
