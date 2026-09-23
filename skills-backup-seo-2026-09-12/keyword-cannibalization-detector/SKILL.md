---
name: keyword-cannibalization-detector
description: >
  Detects true keyword cannibalization — one site fielding more than one of its own
  pages for a query. Use this skill whenever a user says things like "keyword
  cannibalization", "are my pages competing for the same keyword", "two of my pages
  rank for one term", "cannibalization audit/check", "which of my pages compete",
  "am I splitting authority", "should I consolidate these pages", "why are two URLs
  ranking for X", or asks to scan a keyword list for self-competition. It checks every
  keyword against the live Google SERP (never a stale database) and unions the domain's
  ranking URLs across live and historical snapshots to catch pages that compete over
  time. Ranks conflicts by estimated value at risk and delivers a prioritized PDF report
  plus a CSV worklist.
---

# Keyword Cannibalization Detector

The entire value of this skill is *not flagging things that aren't actually
cannibalization*. Two pages showing up for one keyword is normal and usually
harmless. Real cannibalization is: **the domain has more than one of its own pages
competing for one query** — and because modern Google usually shows only one URL per
domain per SERP, the tell is often that Google *rotates* which page it ranks across
searches and dates, never letting one consolidate. This skill catches that by checking
the **live** SERP for every keyword and unioning the domain's URLs across live +
historical snapshots, read **through** the lens of keyword intent and page type, then
priced by value at risk. Ranking status is always backed by live data, never a database.

---

**EXECUTION DIRECTIVE — READ THIS FIRST**

This skill is a strict protocol. Follow every step exactly as written.

- **Do not skip steps.** Every step exists for a reason. If a step says "wait for user reply", wait.
- **Do not substitute endpoints.** Use only the endpoint types listed. Do not call any other DataForSEO tool.
- **Do not invent data.** If an endpoint returns no data, log it and continue — never estimate or assume values.
- **Do not add unsolicited extras.** No extra sections, no bonus recommendations outside the defined output format, no tools beyond what is specified.
- **If something is unclear**, re-read the relevant step. Do not improvise.

---

## What This Skill Produces

| Output | What it is |
|--------|-----------|
| `[domain]_cannibalization_[YYYYMMDD].pdf` | Diagnostic report — summary counts, a priority-ordered conflict table, and a section per flagged keyword with a plain-English verdict + reason + fix |
| `[domain]_cannibalization_[YYYYMMDD].csv` | Actionable worklist — one row per candidate keyword, with positions, page types, verdict, clicks/value at risk, reason, and a specific recommended fix |
| Chat summary | Headline counts and the top conflicts by value at risk, printed in chat |

## How the work is split (read this)

The **diagnostic logic lives in code**, not in your head. You fetch data from DataForSEO,
hand it to two bundled scripts, and interpret the result. This is deliberate: the verdict
matrix, CTR/value math, dedupe, and page-type rules are deterministic and unit-tested
(`scripts/test_core.py`), so the same SERP always yields the same verdict.

- `scripts/cannibalization.py analyze <fetched.json> <data.json>` — the engine. Reads the
  data you fetched, writes the analysis JSON **and the CSV worklist**.
- `scripts/build_report.py <data.json>` — renders the PDF from that analysis JSON.

Your job: collect inputs, fan the SERP fetching out to **sub-agents** that return only the
compact extract, assemble one `fetched.json`, run the two scripts, and refine the
plain-English wording where judgment helps. Don't re-derive verdicts, priorities, or
severity by hand — the core owns those.

**Keeping memory flat — the core rule.** Raw DataForSEO responses are large (a live
depth-100 SERP is tens of KB; most of it — AI Overview, People-Also-Ask, videos, related
searches, per-element metadata — the report never uses) and they must **never enter your
(the orchestrator's) context.** Instead, fetch and parse **inside a sub-agent**: the
sub-agent calls the SERP tool(s), passes `items[]` to the bundled `extract_domain_urls()`,
and returns only `keyword → [(url, position)]` for the target domain's organic results.
The big payload lives and dies in the sub-agent; your context grows only with the tiny
extract, so peak memory stays roughly constant whether the list has ten keywords or ten
thousand. Response-shape note: results are top-level `items[]`; an `organic` item's
`rank_group` is its organic position (1,2,3…), `rank_absolute` counts shopping/other
blocks above it — the engine uses `rank_group`.

---

## Prerequisites

- **A DataForSEO connector must be connected.** If a call returns a 401 / credential
  error, stop: "Please connect and authenticate DataForSEO, then retry."
- **Python with `reportlab`** for the PDF (`pip install reportlab` if missing). The core
  and CSV need only the standard library.

## Choosing the connector — V1 or V3 (do this first)

There may be **two** DataForSEO MCP connectors available: an older **V1** and a newer
**V3**. Before any call, look at your available tools and decide which to use — this
choice does **not** change any detection logic, only where the same endpoints are called:

- If **both V1 and V3 are connected → use V3** for every DataForSEO call in the run.
- If **only one is connected → use that one.**
- **Never mix** connectors within a run, and **never hardcode a server prefix** — the
  prefix differs per connector and per session. Identify each tool by its endpoint
  *function*, not its prefix.
- Note the chosen connector in the run log and on the report's scope line
  (e.g. "DataForSEO connector: V3").

The two connectors call the **same** endpoints differently, but return the **same**
response (a flat `items[]`; organic items carry `url` + `rank_group`), so the engine and
`extract_domain_urls()` are unchanged either way. Endpoint names in this skill are
**functions**, not fixed tool names:

- **V1** — one named tool per endpoint, e.g.
  `serp_organic_live_advanced({keyword, location_name, language_code, depth})`.
- **V3** — a single generic tool `api_request`; select the endpoint with `path` and pass
  the body as a **task-object array**, e.g.
  `api_request({method:"POST", path:"/v3/serp/google/organic/live/advanced",
  data:[{keyword, location_name, language_code, depth}]})`. V3 also has `docs_search` to
  look up any path and supports the lighter `/regular` SERP.

See `references/endpoints.md` → "Two calling conventions" for the full V1-tool ⇄ V3-path
map. The data fields the engine needs are identical on both (organic `url` + `rank_group`,
snapshot `date`, intent `label` + `probability`, `search_volume`, `cpc`); if V3 ever
renames a field, map it to what the engine expects — do not change the engine.

---

## Step 1 — Collect Inputs

Ask these **one at a time**, waiting for a reply before the next.

**Q1 — Domain:**
```
Target domain (root domain, no https:// or www — e.g. "acme.com"):
```

**Q2 — Keywords:**
```
Keywords to check — one per line, or comma-separated, or a path to a .txt/.csv file
of keywords (one per line). These are the queries you want to test for cannibalization.
```

**Q3 — Location & language:**
```
Location and language for the SERP (e.g. "United States / English",
"California,United States / English", "Ukraine / Ukrainian"):
```

**Q4 — Subdomain scope:**
```
Include subdomains (e.g. docs.acme.com, help.acme.com) as the same site, or root domain
only? [root-only / include-subdomains] — default root-only:
```

**Q5 — Page-type map (optional but recommended):**
```
Optional: a path→type map so page types are exact instead of guessed, e.g.
  /apis/* = commercial, /pricing* = commercial, /blog/* = informational
Press Enter to skip — I'll infer types from SERP signals and slugs (and can auto-draft a
map from your top pages).
```

**Q6 — Output folder:**
```
Where to save the report and CSV? Press Enter for the current project folder,
or type a path:
```

---

## Step 2 — Validate & Normalize

| Field | Rule |
|-------|------|
| Domain | Strip `https://`, `www.`, trailing `/`. Lowercase. If it still has a path or spaces, stop and ask. |
| Keywords | Trim each; drop blanks and exact duplicates (case-insensitive). Report the deduped count. If a file was given, read it. If >200 keywords, warn about cost and confirm before proceeding. |
| Location | Convert to the DataForSEO `location_name` format (comma-separated, most-specific first). |
| Language | Map to a two-letter `language_code` (English→`en`, Ukrainian→`uk`, etc.). `search_intent` only supports a fixed language set — see `references/endpoints.md`; if unsupported, run intent in `en` and note it. |

---

## Step 3 — Confirm Scope (spend gate)

Show this scope block (it also becomes the report's scope label), then gate on
`AskUserQuestion`. API credits are not a constraint — this gate is about scope, not spend.

```
------------------------------------------------------
KEYWORD CANNIBALIZATION — review before running
------------------------------------------------------
Domain:     [domain]  (subdomains: [root-only / included])
Keywords:   [N] (after dedupe)
Location(s):[location_name(s)]        Language: [language_code]
Connector:  [V1 / V3]   (V3 preferred when both are connected)
Timestamp:  [ISO8601 run time]
Output:     [output_folder or "current project folder"]

PLAN  (live-first, over time; credits are not a constraint)
  Live SERP, depth 100:        every keyword ([N])   ← source of truth
  Historical SERPs:            keywords that rank     ← rotation / over-time signal
  Search intent (batched):     1
  Search volume + CPC (batched):1
  All SERP fetching + parsing runs in sub-agents; only (url, position) returns.
------------------------------------------------------
```

Use `AskUserQuestion`: "Proceed with the analysis?" → "Yes, run it" / "No, cancel".
Make **no** API calls until the user picks "Yes, run it". Support **one or more** target
locations (repeat detection per location); always label the output with location(s),
language, root-vs-subdomain scope, and the timestamp above.

---

## Step 4 — Live SERP for every keyword (fan out to sub-agents)

Ranking status comes **only** from the live SERP — never from a Labs database guess. Check
**every** input keyword; there is no triage step to skip any (credits aren't a constraint,
and the DB would be unreliable for "does it rank" anyway).

Split the keyword list into chunks and spawn a **sub-agent per chunk**. Give each sub-agent
this job (verbatim intent):

> For each keyword, call the live organic SERP endpoint **on the connector I chose (V1/V3)**
> with `depth: 100`, the given `location_name` and `language_code` — V1:
> `serp_organic_live_advanced({...})`; V3:
> `api_request({method:"POST", path:"/v3/serp/google/organic/live/advanced", data:[{...}]})`.
> Pass the response `items[]` to
> `extract_domain_urls(items, domain, include_subdomains, url_map)` from
> `scripts/cannibalization.py`. Return **only** a compact JSON list:
> `[{ "keyword": ..., "urls": [{"url","position","type"}] }, ...]` — the target domain's
> organic results. Do **not** return the raw SERP, AI Overview, PAA, videos, or any other
> element. If a keyword's SERP errors (not 401), return it with `"urls": []` and an
> `"error"` note; a 401 aborts.

The large payloads stay inside the sub-agents; only the compact `(url, position)` lists
come back to you. `depth: 100` is used here (not a shallow confirm) so deep pages and any
stacked same-domain group are captured for the over-time union. Log any keyword the
sub-agent skipped or capped — never drop results silently.

A keyword whose live SERP shows the domain **at all** is *ranks-here*; carry it to Step 5.
A keyword where the domain is absent from the live top-100 is genuinely `not ranking`.

---

## Step 5 — Historical SERPs for the rotation signal (fan out too)

Because Google usually shows one URL per domain per SERP, a single live snapshot
under-detects multi-page competition. For each *ranks-here* keyword, pull historical SERPs
and union the domain's URLs over time. Fan this out to sub-agents the same way:

> For each keyword, call the historical SERPs endpoint **on the connector I chose (V1/V3)**
> — V1: `dataforseo_labs_google_historical_serps({...})`; V3:
> `api_request({method:"POST", path:"/v3/dataforseo_labs/google/historical_serps/live", data:[{...}]})`
> — with `date_from`/`date_to` spanning ~6–12 months, country-level `location_name`,
> `language_code`. The response is a list of dated snapshots; each snapshot has a
> `datetime` and its own nested `items[]`. **On V3** those items include `url` +
> `rank_group`, so pass each snapshot's `items[]` to `extract_domain_urls` and emit one
> observation per snapshot with the snapshot `datetime` as the date. **On V1** the items
> have **no `url`** (only `domain`/`title`/`rank_absolute`) — you can't resolve pages, so
> skip history on V1 and rely on the live observation. See `endpoints.md` §historical. Run
> `extract_domain_urls` and return **only**
> `[{ "keyword": ..., "observations": [{"date","urls":[{"url","position"}]}] }, ...]`.
> Discard everything else.

Merge each keyword's historical observations with its live observation (label the live one
`"date": "live"`). The result per keyword is a set of dated snapshots — exactly what the
engine unions to see whether the domain fields several pages and whether Google **rotates**
between them. If `historical_serps` returns nothing for a keyword, proceed with just the
live observation (the engine still works; rotation simply can't be confirmed).

---

## Step 6 — Enrich the ranking keywords (two batched calls)

For the *ranks-here* keywords, batch:

**6A — Intent:** `dataforseo_labs_search_intent` (`language_code`). Keep each keyword's
`keyword_intent.label` **and `probability`** — the engine needs the probability to decide
whether a commercial ranking page overrides a soft intent label.

**6B — Volume + CPC:** `kw_data_google_ads_search_volume` (`location_name`, `language_code`).
Keep `search_volume` **and `cpc`** — CPC floats high-value low-volume terms up the priority
order. (If volume/CPC already came back in a SERP/`keyword_info` field, reuse it.)

**Page types** need no extra call by default: the URL map (Step 1 Q5) plus slug patterns
cover most URLs. Only if a competing URL is still `ambiguous` may you spend one
`on_page_instant_pages` call on it. See `references/decision-matrix.md` §2.

---

## Step 7 — Run the engine

Assemble one `fetched.json` and let the core do all the diagnosis (verdicts, CTR/value math,
dedupe, priority, CSV). **Do not compute verdicts, gaps, or priorities yourself.**

`fetched.json` shape — each keyword carries its **observations** (the compact extracts
from Steps 4–5, live + historical):
```json
{
  "meta": {
    "domain": "acme.io", "date": "YYYY-MM-DD",
    "location": "[location_name]", "language": "[language_code]",
    "include_subdomains": false,
    "url_map": {"/apis/*": "commercial", "/blog/*": "informational"},
    "out_path": "[folder]/acme.io_cannibalization_YYYYMMDD.pdf",
    "csv_out":  "[folder]/acme.io_cannibalization_YYYYMMDD.csv"
  },
  "keywords": [
    {
      "keyword": "seo api",
      "observations": [
        {"date": "live",    "urls": [{"url": "https://acme.io/apis/seo", "position": 5}]},
        {"date": "2026-04", "urls": [{"url": "https://acme.io/blog/what-is-seo-api", "position": 8}]}
      ],
      "intent_label": "informational", "intent_probability": 0.60,
      "search_volume": 40, "cpc": 28.0
    }
  ]
}
```
(Each observation may instead carry raw `serp_items` and the engine will extract them, but
prefer passing the already-parsed `urls` so nothing large travels through your context.)
Then run:
```bash
python scripts/cannibalization.py analyze fetched.json data.json
```
It writes `data.json` (analysis) **and the CSV worklist** (`meta.csv_out`). Read `data.json`
for verdicts, `n_pages`, `rotating`, `best_pos`, `clicks_at_risk`, `value_at_risk`, priority
order, and per-case reasons.

The core emits solid, fact-anchored `reason` / `recommendation` strings. You may **refine
their wording** for the report (e.g. noting a brand SERP, or that a category+product pair
should differentiate rather than merge), but do **not** change the verdict or the numbers.

---

## Step 8 — CSV worklist (already written)

The CSV is produced by Step 7 at `meta.csv_out`. Columns: priority, keyword, intents,
volume, CPC, clicks/value at risk, verdict, n_pages, rotating, rotation_count, n_snapshots,
best_pos, both pages (url/pos/type), every domain URL seen over time, reason, recommended
action. No manual assembly — just confirm it exists.

---

## Step 9 — Build the PDF Report

```bash
python scripts/build_report.py data.json
```
Renders the PDF to `meta.out_path`: a summary block (checked; clean / strong / investigate /
harmless counts), a priority table ordered by **value at risk**, then one section per
flagged keyword (strong or investigate) listing every same-domain URL with position + page
type, the intent, clicks/value at risk, the verdict, the reason, and the fix. Footer:
"Data: DataForSEO". If `reportlab` is missing and can't be installed, write the
self-contained `.html` fallback with the same sections and tell the user.

---

## Step 10 — Deliver in Chat

Print:
```
─────────────────────────────────────────────────
KEYWORD CANNIBALIZATION — [domain]   [run_date]
─────────────────────────────────────────────────
CHECKED  (scope: [location] · [language] · [root-only/subdomains] · [timestamp])
  [N] keywords · [C] clean (≤1 page) · [X] with ≥2 competing pages over time

VERDICTS
  strong candidate: [s]   investigate: [i]   harmless overlap: [h]

TOP CONFLICTS (by value at risk)
  #  keyword                intent      best  pages       val/mo  verdict           fix
  ─────────────────────────────────────────────────────────────────────────────────────
  1. [keyword]              commercial  #4    3 rotating   $315   strong candidate  differentiate
  2. ...

TAKEAWAY
  [1–2 sentences: where the real money is being lost and what to do first]

Report: [pdf_path]
CSV:    [csv_path]

Data: DataForSEO
─────────────────────────────────────────────────
```
Pull these numbers from `data.json` (`summary`, `flagged[].value_at_risk`) — don't recompute.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| DataForSEO 401 on any call | Stop immediately. "Please connect/re-authenticate DataForSEO, then retry." |
| No keyword ranks the domain in the live top-100 | Finish cleanly: "None of the [N] keywords rank [domain] live — no cannibalization possible. Healthy sign." Still emit the clean-summary report/CSV. |
| A single live SERP errors (not 401) | Sub-agent returns that keyword with `urls: []` + an `error` note; log it, continue. Never truncate silently. |
| `historical_serps` empty for a keyword | Proceed with the live observation only; note rotation couldn't be confirmed. |
| No keyword has ≥2 competing pages over time | Finish cleanly: every ranking keyword fields one page. Emit the clean-summary report/CSV. |
| `search_intent` language unsupported | Run it in `en`, set `intent_lang_fallback: true` in `meta`. |
| `on_page_instant_pages` fails for a URL | Keep the heuristic's best guess; the core marks unresolved types `ambiguous`. |
| `reportlab` missing and pip blocked | Write the `.html` fallback report; tell the user. |

---

## Reference Files & Scripts

- `references/decision-matrix.md` — how the engine decides: page-type classification,
  the over-time union + rotation verdict model, verdict→recommendation, and the
  value-at-risk priority. **Read before interpreting results.**
- `references/endpoints.md` — the live-first, over-time endpoint plan, exact params/fields,
  the sub-agent parsing rule, and the `search_intent` language list.
- `scripts/cannibalization.py` — the deterministic engine (analysis + CSV). Source of
  truth for verdicts; behaviour locked by `scripts/test_core.py`.
- `scripts/build_report.py` — PDF renderer (see its DATA SHAPE docstring).
