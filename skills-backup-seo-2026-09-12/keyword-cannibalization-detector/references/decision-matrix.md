# Detection Engine — How It Works (over-time model)

The engine is **implemented in code** (`scripts/cannibalization.py`); this file explains
*why* it decides as it does. The code is the source of truth and `scripts/test_core.py`
locks the behaviour with the calibration cases below.

## Contents
1. Mental model — split vs. cost, over time
2. Page-type classification
3. Which pages get judged
4. Verdict — pages, best position, rotation
5. Verdict → recommendation
6. Priority — value at risk
7. Calibration cases

---

## 1. Mental model

Cannibalization is **the domain fielding more than one of its own pages for one query.**
Modern Google host-crowds — usually one URL per domain per SERP — so two of your pages
rarely appear *together* in a single scrape. The real tell is over time: Google **rotates**
which of your pages it ranks across searches and dates, never letting one consolidate.

So detection unions the domain's organic URLs for a keyword across **all snapshots** (the
live SERP + several historical dates). Two separate questions, kept apart:

- **Is authority being SPLIT?** (structural, volume-free) — are there ≥2 distinct domain
  pages competing, and does Google *rotate* which one ranks? Rotation across dates is the
  strongest signal a single snapshot cannot see. The best position any page reaches gates
  whether it matters at all.
- **How much does it COST?** (economic, sets priority) — `value_at_risk = leaked_clicks ×
  CPC`, `leaked_clicks = CTR(best_pos) × volume × fragmentation`, where fragmentation
  `= (n_pages−1)/n_pages` reflects how much potential is spread across competing pages.

The CTR curve lives in `cannibalization.py` → `CTR_TABLE` / `ctr()`; tune per market.

---

## 2. Page-type classification

Each ranking URL is **commercial** (product/category/service/pricing/API) or
**informational** (blog/guide/news/docs). Evidence in order of confidence:

1. **Per-domain URL map** (highest) — `{"/apis/*": "commercial", "/blog/*": "informational"}`.
   Ask the user or auto-draft it. Fixes brittle slug guessing on house-specific paths.
2. **SERP-item signals** (free) — `price`/`rating`/shop flag → commercial; `breadcrumb`
   containing shop/products/category → commercial, blog/news/guide → informational.
3. **Slug heuristic** — `COMMERCIAL_SLUGS` / `INFO_SLUGS`; root path `/` behaves commercially.

Inconclusive → **ambiguous**; only then spend one `on_page_instant_pages` call. **Page type
overrides a *soft* intent label:** a commercial page ranking for a term whose intent-label
probability is below `SOFT_INTENT` (0.80) makes the term commercial regardless of the label
(fixes DataForSEO mislabelling money terms like "seo api" as informational).

---

## 3. Which pages get judged

Union all snapshots into `pages = {url: {best_pos, dates, positions, type}}` and record
`top_by_date` (which URL held the domain's best slot each date). Then:
- **primary** = the page with the best (min) position across time; **secondary** = the next.
  Recommendation and page-type reasoning use these two; the report/CSV list *every* page.
- **rotation_count** = number of distinct URLs that ever held the top domain slot across
  dates. `rotating = rotation_count ≥ 2`.

Extraction hygiene (bundled `extract_domain_urls`, applied per snapshot before union):
dedupe by URL keep best position; **organic only** (a `featured_snippet` collapses onto its
organic twin; PAA/video/related are ignored); subdomain scope per the user's choice.

---

## 4. Verdict — pages, best position, rotation

For the union (`cannibalization.py` → `_verdict`). `band = 30` for commercial, `20` for
informational; `DEEP_POS = 40`.

```
if n_pages < 2:            verdict = harmless overlap   # only one page → not a conflict
elif best_pos > 40:        verdict = harmless overlap   # never ranks high enough to matter
elif best_pos <= band:     verdict = strong candidate if rotating else investigate
else (band < best_pos ≤40):verdict = investigate if (rotating or COMMERCIAL) else harmless
# informational query whose two competing pages are different types (commercial + info)
# = different needs → soften a strong to investigate
```

Why:
- **Rotation is the severity lever.** Two pages that Google actively swaps at a high
  position are splitting authority now; two pages co-listed once but with a stable winner
  are milder (investigate).
- **Best position gates relevance.** If the best any page reaches is past ~40, there are no
  clicks to fight over → harmless, regardless of how many pages or how much rotation.
- **Commercial terms are tighter** (deeper band, and rotation-or-commercial still
  investigates in the 30–40 zone) — money queries matter even a bit deeper.
- **Different intents ≠ a fight** — a product page and a blog on a non-commercial query
  serve different needs.

---

## 5. Verdict → recommendation

Function of verdict + the two page types + which page is stronger (`_recommendation`).
Always names the specific pages; never generic.

| Case | Fix |
|------|-----|
| harmless overlap | **No action** — one page holds its position without rotation, or all pages sit too deep. |
| two **commercial** pages | **Consolidate: merge the weaker into the stronger + 301** — one authoritative page outranks rotating ones. |
| two **informational** pages | **Differentiate the articles**, or consolidate into one guide + 301 the weaker. |
| **commercial + informational** (different intents) | **Keep both — do NOT merge.** Canonicalize / de-optimize the informational page for this term and point internal links + canonical at the commercial page, which should own the money term. |
| ambiguous types | **Clarify page roles first**, then differentiate or consolidate. |

The key correction vs. naive tools: **don't default to merge+301.** Two pages serving
different intents (a feature page vs. its pricing page; a category vs. a specific product)
should be *differentiated / canonicalized*, keeping both. Merge is only for two genuinely
equivalent pages competing for the same intent.

---

## 6. Priority — value at risk

```
value_at_risk = clicks_at_risk × CPC
clicks_at_risk = CTR(best_pos) × volume × (n_pages−1)/n_pages
economic = max-normalized value across THIS list  (0.75 value + 0.25 clicks; clicks-only if no CPC anywhere)
priority_score = round(100 × severity × (0.15 + 0.85 × economic), 1)
severity: strong 1.0 · investigate 0.55 · harmless 0.10
```

Blending CPC (traffic *value*, not raw volume) and max-normalizing against the actual list
floats high-value low-volume terms up; a floor keeps niche terms off the bottom. The
reported "~N clicks/mo ≈ $X/mo at risk" is what makes the report land with executives.

---

## 7. Calibration cases (the unit tests)

| # | Setup | Verdict | Why |
|---|-------|---------|-----|
| 1 | commercial, 2 product pages, Google rotates top across 3 dates, best #8 | **strong** | rotation at a high position = active split |
| 2 | one page only across snapshots | **clean** | not a conflict |
| 3 | 2 pages both buried (best #55) | **harmless** | nothing to win that deep |
| 4 | 2 pages high but stable top (no rotation) | **investigate** | competing but Google isn't swapping |
| 5 | informational, 2 blogs, rotating, best #9 | **strong** | same-type rotation |
| 6 | commercial, best #35, rotating | **investigate** | 30–40 zone, commercial |
| 7 | informational, mixed types (product+blog), rotating, best #10 | **investigate** | different needs soften it |
| 8 | "seo api", soft info label + /apis/ page, rotating #6 | **strong**, effective **commercial** | page type overrides soft label; CPC gives real value |
| 9 | 3 pages rotating, best #7 | **strong** | multi-page fragmentation |
| 10 | commercial, 2 pages high, stable top | **investigate** | co-listed, no rotation |

Plus: the priority test asserts a $28-CPC / 40-search term outranks an equal-traffic
$0.15 term and isn't floored; and the mixed-intent case asserts the recommendation says
**"Do NOT merge."**
