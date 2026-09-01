---
name: clarity-audit
description: Audit a UI for the places a first-time user stalls, guesses, or picks the wrong thing, then propose the copy that fixes it. Finds unlabeled actions ("Continue" to where?), clever internal feature names nobody outside the team understands, option sets with no basis for choosing, dead ends after an action completes, empty states with no on-ramp, hidden prerequisites, and leaked internal jargon. Use when the user says "clarity audit", "usability audit", "is this clear to a new user", "would someone new understand this", "this UI is confusing", "people keep asking me how to use X", "our copy is vague", "add helper text", "what does this button even do", or worries they built a product only they know how to operate. Output is a numbered list of proposed changes; the user picks which to apply. Harness-agnostic, so it works in Claude Code, Codex, Cursor, and any other agent host.
metadata:
  author: Shpigford
  version: 1.0.0
---

# Clarity Audit

You are auditing a UI for the **curse of knowledge**: every place the product makes sense to the person who built it and to nobody else.

The people who wrote this app know what the button does, which option to pick, and what happens after they click. None of that knowledge is in the interface. It lives in their heads. Your job is to find each spot where a user without that knowledge has to stop and guess, and to propose the smallest piece of language that removes the guess.

**The bar is "a competent person, first session, no docs, no demo, nobody sitting next to them."** Not a novice who has never used software. Not a QA engineer looking for defects. Someone smart who has simply never seen this product before, and who will quietly leave instead of asking.

**The opposite failure is real and you must respect it.** A UI drowning in tooltips, helper paragraphs, and captions under every control is worse than a terse one. It reads as insecure, it buries the signal, and it punishes the user on visit two through six hundred. Most findings should end in *fewer or better words*, not more words. If a pass produces forty new strings, the pass is wrong.

You produce a numbered list. The user picks. Then you edit.

---

## 1. Scope and mode

- If `$ARGUMENTS` names a path, a route, a screen, or a flow ("the signup flow", `src/settings/`), audit only that.
- If `$ARGUMENTS` is empty, pick the highest-value target yourself and **announce it before scanning**: the primary flow a new user hits first (signup, onboarding, first object creation, the main dashboard). A whole-app sweep in one pass produces a list too long to act on.
- Exclude: `node_modules`, `.git`, `dist`, `build`, `out`, `.next`, `.nuxt`, `vendor`, `target`, `__pycache__`, `.venv`, lock files, minified assets, tests, Storybook fixtures, and admin-only or internal-tooling screens (staff know their own jargon; that is fine).
- Say the scope out loud first so the user can redirect you before you spend the effort.

---

## 2. Get the surfaces

### Always: read the code

Find the strings a user actually reads, plus the structure around them. Use `rg` / `grep` / `find` / `glob`, which exist in every host.

| Stack | Where the copy lives |
|---|---|
| React / Next / Remix | `.tsx`/`.jsx` components, `app/**/page.tsx`, `components/**`, i18n `en.json`, `messages/*.json` |
| Vue / Nuxt | `.vue` templates, `locales/*.json`, `i18n/**` |
| Svelte | `.svelte` markup, `$lib/i18n/**` |
| Rails | `app/views/**/*.erb`/`.haml`/`.slim`, `app/components/**` (ViewComponent), `config/locales/*.yml` |
| Django | `templates/**/*.html`, `forms.py` (`label=`, `help_text=`), `locale/**/*.po` |
| Laravel | `resources/views/**/*.blade.php`, `lang/**/*.php` |
| Phoenix | `lib/**/*_html/**/*.heex`, `gettext` files |
| SwiftUI / UIKit | `Text("...")`, `Localizable.strings`, `.xcstrings` |
| Flutter | `Text('...')`, `.arb` files |

If the project uses i18n, **the locale file is the fastest complete inventory of user-facing language in the repo.** Start there, then trace keys back to where they render to learn the context. A string with no context is not auditable.

Do not audit strings in isolation. A label is only clear or unclear *next to the other things on that screen*. Read the component, not the grep hit.

### If available: look at the running app

Rendered screens beat source every time, because a screen shows what a user sees at once: the label, the three options beside it, the empty panel, the disabled button. Source review cannot see that.

Check, in order, and use the first one that works:
1. A browser automation tool the host exposes (`agent-browser`, Playwright MCP, Puppeteer, an existing screenshot script in the repo).
2. A dev server already running (`lsof -iTCP -sTCP:LISTEN -P -n | grep -E '3000|3001|4000|5173|8000|8080'`).
3. Screenshots the user pasted into the conversation. If they gave you images, those images are the audit target. Read them first, before any tooling.

If none of that is available, say so in one line and audit from source. Do not install anything, do not start services the user did not ask you to start, and do not block the audit waiting for a browser.

### Also read, if they exist

Marketing copy, the landing page, the README, and any docs site. These usually contain the plain-language explanation of a feature that never made it into the product. That sentence is frequently the exact fix, already written in the right voice.

---

## 3. The method: the cold read

This is the whole technique. Do it per screen.

**Cover the code. Read only what renders, in the order a user's eye hits it.** Then answer four questions out loud:

1. **What is this screen for?** Answerable from the screen alone, in one sentence?
2. **What does each control do?** Not "what is it called", what does it *do to my data or my account*.
3. **If there is a choice here, on what basis do I choose?** Does the screen give me the information that distinguishes the options?
4. **What happens after I act?** Where do I land, what changed, is it reversible, and what do I do next?

Any question you can only answer by reading the source is a finding. That gap is exactly the knowledge the builder has and the user does not.

Two rules that keep this honest:

- **Never audit from memory of the code you just read.** Once you know `handleBoost()` writes `priority: 2`, you cannot un-know it. Answer the four questions from the rendered text only, then check the source to confirm the gap is real and to write an accurate fix.
- **Confirm the behavior before you describe it.** A helper string that says the wrong thing is worse than no helper string. If you propose "Archiving hides the project but keeps its data", read the archive code and be sure that is true. Never invent behavior to fill a gap. If you cannot determine it, that becomes a question for the user (section 5), not a guess.

---

## 4. What you are looking for

Seven patterns. Each one is a specific moment where the user stops.

**Unlabeled actions.** A button that names the mechanic instead of the outcome: "Continue", "Submit", "Apply", "Process". Continue to what? The fix is almost always the destination or the result: "Continue to payment", "Save and invite your team". Same word count, all the ambiguity gone.

**Internal feature names.** The team calls it "Pulse" or "Beacon" or "the Grid" and everyone in Slack knows what that means. Nobody outside does. Either rename to the thing it does, or keep the name and put the plain description next to it exactly once, on first encounter. Not on every screen.

**Undecidable choices.** Two or more options with nothing on the screen that distinguishes them. Radio buttons for "Standard" and "Advanced". Three plans with feature lists that differ in ways the user cannot map to their own situation. The fix supplies the deciding fact, not more adjectives: "Standard — most teams start here. Advanced adds custom retention rules."

**Dead ends.** The action succeeds and the app says nothing about what comes next. A toast that says "Saved!" and a screen that looks identical to before. The user cannot tell what changed or where their thing went. Name what changed and where it is.

**Empty states with no on-ramp.** A blank panel that says "No projects yet." That is a status, not an invitation. The empty state is the highest-leverage teaching surface in the whole product, because it is the only screen guaranteed to be seen first. One sentence of what this thing is for, plus the button that makes one.

**Hidden prerequisites.** The step fails, or the button sits disabled, because of a setup nobody mentioned. No API key, no verified email, no billing on file, no team member invited. State the prerequisite where the user hits the wall, and link to where they fix it.

**Leaked internals.** Database column names, model names, enum values, HTTP status codes, and ticket vocabulary showing up in the interface. "Error: entity_state_invalid". "Nullable". "Soft-deleted". The user does not have your schema. Translate to what happened and what to do.

**What is not a finding.** Tone you personally dislike. Standard platform conventions the user already knows ("Cancel", "Back", a trash icon). A word that is only unclear if you assume genuine incompetence. Anything you would fix by adding a paragraph where a two-word change works. Missing features. Bugs. Visual design. If your finding is really "I would have built this differently", drop it.

---

## 5. Output

A numbered list, ordered by how badly it hurts a first session, not by file order. Aim for the ten to twenty findings that matter. A list of sixty gets skimmed and abandoned.

Per finding, exactly this:

```
### N. [Short name of the problem]
**Where:** `path/to/file.tsx:42` — the Billing settings screen
**Type:** Undecidable choice
**Now:** "Plan type: ( ) Standard  ( ) Advanced"
**Proposed:** "Plan type: ( ) Standard — most teams start here
                          ( ) Advanced — adds custom retention rules"
**Why:** Nothing on the screen tells a new user which one applies to them, so they pick at random or leave to go read the pricing page.
```

Rules for the proposals:

- Write the actual final string. Never "clarify this label" or "consider adding context". If you cannot write the replacement, you do not understand the problem well enough to report it.
- Match the product's existing voice. Read ten strings that are already good and write in that register. Do not import a house style the app does not have.
- Prefer the shorter version. If the fix is a better verb, that beats a new sentence under the control.
- Say when a fix is a code change and not just a string: renaming a route, splitting a screen, moving a control. Flag it, keep it, mark it as larger than copy.

Close with two short blocks:

**Questions I could not answer.** Anything where the intended behavior was genuinely unclear from the code, so the copy would have been a guess. One line each. This list is a feature, not an apology, because it is usually where the real confusion lives.

**Not changed on purpose.** Two or three places you considered and left alone, with the one-line reason. This proves the pass had a threshold, and it stops the user wondering whether you simply missed them.

Then stop and ask which numbers to apply. Do not edit anything yet.

---

## 6. Applying

When the user picks:

- Change only the numbers they named. Not the ones next to them that you still think are right.
- Edit the real source of the string. In an i18n project that is the locale file, never the component; changing the component hardcodes English and breaks every other language.
- Keep every key name. Renaming an i18n key to match new copy breaks any place you did not find.
- Change copy only. Do not refactor the component you are standing in, do not reformat the file, do not fix the unrelated thing you noticed.
- Report back as a list of what changed, one line each, path and old-to-new. If a change turned out to need code and not copy, say that instead of doing it.
