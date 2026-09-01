---
name: skill-dedupe
description: Find and remove genuinely redundant skills across every installed skill root. Invoke explicitly with /skill-dedupe, best right after installing a new skill. Scans all four skill roots, dedupes symlinks and package mirrors, pre-filters before spending subagents, checks routers and invocation flags before proposing any deletion, and makes deletions durable by clearing lock-file and marketplace registrations.
disable-model-invocation: true
---

Find skills that genuinely duplicate each other, then remove them in a way that keeps them removed.

This replaces the naive "compare every pair, delete the loser" approach. Three things make that approach wrong at real scale, and each has a stage below: pair count explodes, identity is not the same as file count, and a high similarity score does not mean a skill is safe to delete.

## Stage 1: Collect

Scan **all four** roots. Missing any of them produces a wrong skill count and hides real duplicates:

1. `~/.claude/skills/**/SKILL.md` — personal
2. `~/.agents/skills/**/SKILL.md` — shared agent root (Codex CLI and others read this)
3. `~/.claude/plugins/cache/**/SKILL.md` — plugin
4. `~/.claude/plugins/skills/**/SKILL.md` — cloned skill marketplaces

Then collapse two kinds of false duplicate before counting anything:

- **Symlinks.** Dedupe by `os.path.realpath`. A symlinked skill is one skill, not two.
- **Same-package mirrors.** Plugins commonly ship the same skill two or three times inside one package (`source/skills/`, `.claude/skills/`, `cli/assets/skills/`). Collapse on `(name, package_root)`. Deleting a mirror gains nothing and breaks the plugin.

Report the deduped count and name each root's contribution. If the count differs from a previous run, say why.

## Stage 2: Pre-filter before spending subagents

Pick the mode first. **Targeted is the default** — nearly every real duplicate arrives with an install, so check the arriving skill rather than re-sweeping a stable set.

### Targeted mode (a skill was just added or installed)

Rank the new skill against all others. That is only N-1 comparisons, so it can afford a far lower bar than a global sweep, and it is the mode that catches same-purpose pairs a global threshold structurally cannot.

```python
name_tok  = {stem(w) for w in name.split("-")}          # stem plurals; do NOT stopword these
combined  = 0.6 * max(desc_jaccard, 0.8*desc_containment, name_jaccard) + 0.4 * body_containment
```

`body_containment` is over 4+ letter words with frontmatter stripped, divided by the smaller set. Judge the **top 10** with subagents regardless of absolute score, and expect the new skill's whole topic family to cluster there.

### Global mode (periodic audit)

At ~290 skills, all pairs is ~42,000. Narrow with cheap description scoring, then spend subagents only on survivors:

```python
score = 0.6 * jaccard(desc_tokens) + 0.4 * jaccard(name_tokens)   # candidates at >= 0.26
```

- **Stopwords matter.** Without a stopword list, near-identical descriptions score low and get missed. Strip common English and boilerplate ("use", "when", "triggers"). Do **not** strip domain nouns from name tokens.
- **Jaccard punishes long descriptions.** An 85-token description will not pair with a 30-token one even when it contains it. Add a **containment** pass: `len(a & b) / len(smaller)`, flag at >= 0.70.

**Global mode has a recall floor, and you must say so in the report.** Measured example: `skill-dedupe` vs `clean-skills` do the same job and score **0.039** — an 11-token description gives containment 0.27, and stemmed names share nothing. Body-content scoring does not rescue it either: the pair sits at 0.505 body-containment, and the threshold needed to catch it returns ~300 pairs, because same-genre skills share vocabulary. Targeted mode ranks that same pair **#1 of 287**. Never present a global sweep's "0 candidates" as proof the set is clean.

Skip pairs already judged in an earlier run, and skip known workflow families (see Stage 3). Batch survivors 10 at a time in parallel.

Subagent prompt: compare Purpose, Trigger, Process, Output. High similarity requires solving the same problem the same way. Different roles are complementary. Same principles in a different domain scores LOW. Different workflow stages are NOT duplicates. Return `similarity_percent`, `overlapping_features`, `differences`, `recommendation`.

## Stage 3: Structural context — run before proposing any deletion

**A subagent reads two files in isolation. It cannot see what makes a skill load-bearing.** Skip this stage and you will propose deleting a router's main entry point. For every pair at or above threshold, gather:

- **Inbound references.** `grep -rln "<name>"` across all four roots plus `~/.claude/agents` and `CLAUDE.md`, excluding the skill's own directory. A skill with zero inbound references is a safe candidate. A skill named by a family router is not.
- **Invocation flags.** Read the flag from the **frontmatter only** (`awk '/^---$/{n++;next} n==1'`), never a whole-file grep, which matches prose about the flag and reports a false positive. Manual-only on both means they **cannot collide**. High textual overlap between two manual variants is a maintenance concern, not a trigger conflict.
- **Family membership.** Read any orchestrator or router skill that names either one. Routers document the real distinction, which the file pair alone will not reveal (for example stateful vs stateless, or explore vs exploit stage).
- **Content coverage.** Before calling one a superset, verify with `diff` and byte counts per shared reference file. Confirm the surviving copy actually carries the sections the other one had.

Known families that are topic-split, not duplicated. Do not re-judge these:
`sdd-*` (workflow stages), `inertia-rails-*` (distinct tasks), `seo` and its `seo-*` children (orchestrator names them in its own body), `better-*` (members of the `better-interface` roster).

## Stage 4: Report

Only pairs at 70% or above, sorted descending. Bar is 20 chars: `██████████████████░░ 85%`.
Grades: 90%+ 🔴 remove candidate, 70-89% 🟡 review, below 70% excluded.

Per pair show both sources (personal/plugin) and full paths when names collide, an Overlap list, a Diff list, and one arrow line with the recommendation. State findings from Stage 3 explicitly — inbound reference counts, manual-only flags, router relationships — because they often invert the recommendation the score implies.

End with a summary of counts by grade, plus what was skipped and why.

## Stage 5: Interactive selection

Ask about **one pair at a time**, descending. Wait for a response before the next.

```
#1  skill-a  VS  skill-b  (85%)

    a) Remove skill-a
    b) Remove skill-b
    c) Keep both (skip)
```

If the user picks a skill that Stage 3 found is load-bearing, say so plainly with the evidence and re-offer, then honor the decision if they reaffirm. Auto-skip later pairs containing an already-removed skill and say so.

## Stage 6: Delete durably

Confirm before deleting anything. Then, per skill, in this order:

1. **Back up first.** `tar -czf ~/<name>-backup.tar.gz` into the home directory, not a session scratchpad, which is ephemeral. Use distinct archive paths when backing up two trees that share a basename, or extraction overwrites one with the other.
2. **Remove both ends.** A skill often exists as a symlink in one root and a real directory in another. `rm -f` the symlink and `rm -rf` the target. Verify both.
3. **Clear the lock entry.** `~/.agents/.skill-lock.json` holds a `skills` map for `npx skills`. A stale entry reinstalls the skill on the next update. Remove the key, keep a `.bak`, and confirm the file is still valid JSON.
4. **Handle plugin registration.** Deleting from `~/.claude/plugins/cache/` alone is temporary. Also run `claude plugin uninstall <plugin>` and `claude plugin marketplace remove <name>`, otherwise it returns. Check `installed_plugins.json` first: a cache directory carrying an `.orphaned_at` marker is already uninstalled and only the marketplace registration needs removing.
5. **Repair inbound references.** Repoint every reference Stage 3 found, then re-grep to confirm no dead pointers remain.
6. **Verify no broken symlinks.** For each symlink in `~/.claude/skills`, confirm `SKILL.md` is readable.

Report each deletion inline with its result. On failure, show the error and continue with the next skill.

## Completion summary

```
Review complete.

  ✅ Removed: N skills (names)
  ✅ Cleaned: N stale lock entries / marketplace registrations
  ❌ Failed:  N skills (name — reason)
  Kept:      N unique skills
  Skipped:   N pairs
```

Then state remaining carry-overs: pairs that need a merge rather than a delete, and any decision deferred to the user.

## Common mistakes

| Mistake | Correct approach |
|---|---|
| Scanning only two roots | Scan all four; report each one's contribution |
| Counting symlinks and package mirrors as duplicates | Dedupe by realpath and by `(name, package_root)` |
| Generating N*(N-1)/2 subagents | Pre-filter, then batch survivors by 10 |
| Missing near-identical pairs | Use a stopword list; add a containment pass for umbrella skills |
| Trusting a similarity score alone | Run Stage 3 first; routers and invocation flags often invert it |
| Calling one skill a superset on a model's say-so | Verify with `diff` and per-file byte counts |
| `rm -rf` on the cache only | Also uninstall the plugin and remove the marketplace |
| Ignoring `.skill-lock.json` | Clear the entry or `npx skills update` reinstalls it |
| Deleting one end of a symlink pair | Remove the symlink and the target |
| Backing up to a session scratchpad | Back up to the home directory; scratchpads are cleaned up |
| Deleting without checking inbound references | Grep first, repoint after |
| Treating workflow stages or manual-only variants as duplicates | Score low; note the family and move on |
| Reporting a global sweep's "0 candidates" as proof the set is clean | Global mode has a measured recall floor; run targeted mode on anything recently added |
