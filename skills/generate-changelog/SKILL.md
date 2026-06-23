---
name: generate-changelog
description: Update the repo's changelog for a given version (or Unreleased), grouping changes into New features / Improvements / Bug fixes, then humanize the copy and commit. Use when the user says "generate changelog", "update changelog", "changelog for vX.Y.Z", or runs /generate-changelog.
model: sonnet
---

# generate-changelog

Update the changelog for a version, categorize the changes, humanize the prose, and commit.

## Argument

The argument is the version: `1.5.3`, `v1.5.3`, or `unreleased` (default if omitted).
Normalize to match how existing headings in the file are written (with or without a leading `v`).

## Steps

1. **Find the changelog.** Look for `CHANGELOG.md` at the repo root (fall back to `CHANGES.md`, `HISTORY.md`, or `docs/CHANGELOG.md`). If none exists, ask the user before creating one.

2. **Read the top of the file** to learn its conventions: heading level for versions, whether versions carry a leading `v`, and the date format. Match those. The one thing you *do* impose is structure: every version entry you write is organized into the category sub-headings below, even if older entries in the file are flat bullets — see step 5.

3. **Gather the changes.** Pull from, in order of preference:
   - The diff since the last released version tag: `git log <last-tag>..HEAD --oneline` and `git diff <last-tag>..HEAD --stat`. Find the last tag with `git describe --tags --abbrev=0` (fall back to the last version heading in the changelog if there are no tags).
   - Uncommitted work: `git status` and `git diff` (staged + unstaged).
   Read the actual diffs of the meaningful files so each entry describes user-facing behavior, not the code. Skip purely internal churn (refactors, deps, formatting) unless the user asks for it.

4. **Categorize** each change into:
   - **New features** — capabilities that didn't exist before.
   - **Improvements** — existing things made better, faster, clearer.
   - **Bug fixes** — things that were broken and now work.
   Drop any empty category. If a change doesn't fit, use a fourth group only if needed (e.g. **Other**).

5. **Write the entry.**
   - For a real version: heading with the version and today's date in the file's existing date format.
   - For `unreleased`: an `## Unreleased` section (reuse the existing one if present — merge, don't duplicate).
   - Place it above the most recent version, below the title.
   - **Always organize the bullets under category sub-headings**, one level deeper than the version heading (so `### New features`, `### Improvements`, `### Bug fixes` under an `## 1.2.3` version). Keep that order; drop any sub-heading whose category has no entries. This applies even when older version entries in the file are flat, unordered bullets — the new entry still gets sub-headings. If you're asked to (re)organize an existing entry that's a flat list, convert it into these same sub-sections in place.
   - One bullet per change, user-facing voice. Lead each with **what changed** in bold, then a plain-language explanation.

6. **Humanize the copy.** Invoke the `humanize-copy` skill on the changelog file so the new entries read like a person wrote them, not a release-notes generator. This rewrites in place.

7. **Commit.** Invoke the `commit` skill to commit all repo changes.

## Notes

- Keep the user's voice and the file's existing tone (wording, spelling, bullet style). The category sub-headings (`### New features` / `### Improvements` / `### Bug fixes`) are the one structural element you always add, regardless of how older entries are laid out — match the neighbours on everything else.
- Show the proposed entry before humanizing/committing only if the changes are ambiguous; otherwise proceed.
