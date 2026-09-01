---
name: generate-changelog
description: Update the desktop (CHANGELOG.md) and mobile (mobile/CHANGELOG.md) changelogs for a version (or Unreleased), routing each change to the right file, grouping into New features / Improvements / Bug fixes, then humanizing the copy and committing. Use when the user says "generate changelog", "update changelog", "mobile changelog", "changelog for vX.Y.Z", or runs /generate-changelog.
model: sonnet
---

# generate-changelog

Update the changelog(s) for a version, categorize the changes, humanize the text, and commit. One run covers both product lines: read the whole changeset once, then send each change to the file its users read.

## The two files

| File | Holds | Read by |
|---|---|---|
| `CHANGELOG.md` (repo root) | Desktop-only changes **and** changes that ship on both desktop and mobile. | The GitHub release notes and the marketing site — markdown, no length limit, but keep it tight. |
| `mobile/CHANGELOG.md` | Changes only a phone user sees. | Pasted straight into App Store Connect — see the format rules below. |

Both files end up on the marketing site: `release-marketing` turns a desktop
version section into `changelog/<version>.md` and a mobile one into
`changelog/ios-<version>.md`, each its own page with its own URL. So write every
version section to stand on its own — a reader arrives at that one release, not
at the file.

A change lands in exactly one file — never both.

**Desktop-only surfaces:** Electron main process, native application menus, system tray, auto-update, multi-window and window management, desktop-only keyboard flows.

**Mobile-only surfaces:** `mobile/`, `ios/`, `android/`, `capacitor.config.ts`, and anything in the shared renderer gated to mobile (a mobile-only component, an `isMobile` branch, a Capacitor plugin call).

**Both sides:** the renderer in the root `src/` is shared between the Electron desktop app and the Capacitor mobile app, so most user-facing changes ship on both — by the rule above those go in the desktop `CHANGELOG.md` alone.

## Then: macOS, Windows, or both

The desktop file covers two platforms that ship on their own schedules, so every bullet you put in it also gets a platform verdict.

**macOS-only surfaces:** `process.platform === 'darwin'` branches, the dock, the menu bar, the quick-entry popover, `scripts/notarize.mjs`, signing and notarization, `.dmg` packaging.

**Windows-only surfaces:** `win32` branches, `scripts/build-win.mjs`, NSIS and the installer, Windows path handling (drive letters, backslashes, long paths).

**Both:** everything else — the shared renderer in `src/renderer/`, and any `src/main/` code with no platform branch in it.

**How to mark it.** A one-platform bullet names its platform in its own lead sentence, the way the shipped entries already do: "**Windows gets your journal's folder right.**" No tag syntax, no parser, nothing for a script to strip. A both-platforms bullet says nothing about platforms at all.

**The version heading** names the platforms that version reached: `## v1.2.6 — 2026-08-16 — macOS, Windows`. When cutting a version yourself, write only the platforms named in the argument. In the normal release flow you don't write it — `scripts/promote-changelog.mjs` does, reading the platforms off the release's own assets. Headings with no platform list predate the split and mean both.

That list is not decoration: `release-marketing` copies it into the site entry's `platforms` frontmatter, which decides the filter tab the release appears under and which installers the page offers. A version heading that claims Windows on a Mac-only release hands people an older `.exe` under a newer number.

None of this applies to `mobile/CHANGELOG.md`: iOS is one platform on its own version line, so its headings carry no platform list.

## Mobile entries are App Store release notes

A mobile version section gets copied into the "What's New" field as-is, so write it to Apple's rules from the start:

- **Plain text only.** No `**bold**`, no backticks, no links, no HTML — none of it renders there, it just shows the characters. The `##` version heading is the only markdown in the section, and it stays behind when the text is copied.
- **Category labels are bare lines** (`New features`, `Improvements`, `Bug fixes`), not `###` headings. Bullets start with `- `.
- **4000 characters max per version section.** Apple caps "What's New in This Version" release notes and product descriptions at 4,000 characters; anything past that won't paste. Count the section when you're done and aim well under. If it's too long, merge bullets and cut the least interesting ones rather than trimming every sentence to a stub.
- **Never mention other platforms, pricing, betas, or upcoming features.** No "on your Mac", no "coming soon", no Android. Apple rejects release notes for these.
- Phone language throughout: taps, swipes, the keyboard, Settings. Never "click" or "right-click".

The version lines are independent: mobile starts at `0.0.1`, desktop is on `1.x`. Desktop versions live in `package.json`; mobile versions live in `ios/App/App.xcodeproj/project.pbxproj` (`MARKETING_VERSION`) and `android/app/build.gradle` (`versionName`).

## Argument

- omitted / `unreleased` — both files get an `## Unreleased` section (the default).
- `1.5.3` / `v1.5.3` — cuts a **desktop** version heading; anything mobile-only in the changeset still goes to the mobile file's `Unreleased`.
- `1.5.3 mac` / `1.5.3 win` — same, but the heading names only that platform.
- `mobile 0.0.2` / `mobile v0.0.2` — cuts a **mobile** version heading; anything desktop or shared still goes to the desktop file's `Unreleased`.

Normalize the version to match how existing headings in that file are written (with or without a leading `v`).

## Steps

1. **Open both changelogs.** `CHANGELOG.md` at the repo root (fall back to `CHANGES.md`, `HISTORY.md`, or `docs/CHANGELOG.md`) and `mobile/CHANGELOG.md`. If one is missing, ask the user before creating it (title `# Changelog`).

2. **Read the top of each file** to learn its conventions: heading level for versions, whether versions carry a leading `v`, the date format, and whether bullets are separated by blank lines. Match those per file. The one thing you *do* impose is structure: every version entry you write is organized into the category sub-headings below, even if older entries in the file are flat bullets — see step 5.

3. **Gather the changes.** Always check *both* sources every run — uncommitted work is not a fallback, it's part of the changeset:
   - The diff since the last released version tag: `git log <last-tag>..HEAD --oneline` and `git diff <last-tag>..HEAD --stat`. Find the last tag with `git describe --tags --abbrev=0` (fall back to the last version heading in the changelog if there are no tags).
   - All pending working-tree changes: `git status --short` and `git diff HEAD` (covers staged + unstaged + untracked-as-needed).
   Read the actual diffs of every meaningful file from both sources so each entry describes user-facing behavior, not the code. Skip purely internal churn (refactors, deps, formatting) unless the user asks for it. Don't stop at the commit log — uncommitted features in the working tree must make it into the entry too.

4. **Route, then categorize.** For each change, pick its file using the table above, then its category:
   - **New features** — capabilities that didn't exist before.
   - **Improvements** — existing things made better, faster, clearer.
   - **Bug fixes** — things that were broken and now work.
   Drop any empty category, and skip a file entirely if nothing routed to it. If a change doesn't fit, use a fourth group only if needed (e.g. **Other**).
   For anything landing in the desktop file, also decide macOS / Windows / both from the surfaces listed above, and check the diff rather than guessing — a `process.platform` test or a `win32` branch is the tell.

5. **Write the entry** in each file that has changes.
   - For a real version: heading with the version and today's date in that file's existing date format.
   - For `unreleased`: an `## Unreleased` section (reuse the existing one if present — merge, don't duplicate).
   - Place it above the most recent version, below the title.
   - **Always group the bullets by category**, in the order New features → Improvements → Bug fixes, dropping any category with no entries. In `CHANGELOG.md` they're `###` sub-headings; in `mobile/CHANGELOG.md` they're bare text lines. This applies even when older version entries in the file are flat, unordered bullets — the new entry still gets grouped. If you're asked to (re)organize an existing entry that's a flat list, convert it in place.
   - One bullet per change, user-facing voice. Lead with what changed, then a plain-language explanation. Bold the lead in `CHANGELOG.md`; the mobile file takes no emphasis at all.
   - In `CHANGELOG.md`, a bullet that only reached one desktop platform says which one in that lead sentence. Never bury it at the end, and never leave a Mac user reading about a Windows-only fix as though it were theirs.
   - **Group related changes into the fewest bullets possible.** Several changes that are part of one feature (e.g. a color picker plus its opt-out toggle plus the accent it drives) belong in a single bullet, not three. Merge them; don't enumerate.
   - **Keep each bullet short.** A sentence or two. Say what it does and the one detail that matters — drop the step-by-step walkthrough and the "works the same as before" caveats. This holds for the desktop file too: no length limit is not a licence to ramble.
   - For a mobile entry, check it against the App Store rules above before you move on — 4,000 characters, plain text, no other platforms.

6. **Humanize the copy.** Invoke the `humanize-copy` skill on each changelog you touched so the new entries read like a person wrote them, not a release-notes generator. This rewrites in place.

7. **Commit.** Invoke the `commit` skill to commit all repo changes.

## Notes

- Keep the user's voice and each file's existing tone (wording, spelling, bullet style). The category grouping is the one structural element you always add, regardless of how older entries are laid out — match the neighbours on everything else.
- A shared-renderer change goes in the desktop file only. Don't repeat it in the mobile one, and never leave a mobile bullet describing something a phone user can't reach.
- Three platforms, three release lines: macOS and Windows share a version number but not a schedule, and iOS shares neither. The changelog is where that shows, so a reader can tell what reached their machine.
- Show the proposed entries before humanizing/committing only if the routing or the changes are ambiguous; otherwise proceed.
