# DataForSEO Endpoints — Live-first, over-time

Call whatever DataForSEO tools are connected. There may be two connectors — an older **V1**
and a newer **V3**; **if both are connected use V3, otherwise use whichever one is** (see
SKILL.md → "Choosing the connector"). Never hardcode a server prefix and never mix
connectors in a run. DataForSEO is the **only** data source. **API credits are not a
constraint** — optimize for memory and speed, not calls.

## Two calling conventions (verified)

The two connectors expose the **same DataForSEO endpoints** but are called differently.
**The response is the same either way** — a flattened top-level `items[]`; organic items
carry `type`, `url`, `rank_group` (+ `rank_absolute`, `domain`, `breadcrumb`) — so
`extract_domain_urls()` consumes both identically. Only the call differs:

- **V1** — one named tool per endpoint. Example (live SERP):
  `serp_organic_live_advanced({ keyword, location_name, language_code, depth })`.
- **V3** — a single generic tool `api_request`. Example (live SERP):
  `api_request({ method: "POST", path: "/v3/serp/google/organic/live/advanced",
  data: [{ keyword, location_name, language_code, depth }] })`. Note `data` is an
  **array of task objects**. V3 also exposes `docs_search` / `docs_index` to look up any
  path, supports the lighter `/regular` SERP variant, and defaults to an AI-optimized
  (smaller) response (`noAiMode:false`).

**Endpoint → V3 path map** (V1 tool name ⇄ V3 `path`):

| Function | V1 tool | V3 path (POST, `data:[ {…} ]`) |
|----------|---------|--------------------------------|
| Live organic SERP (source of truth) | `serp_organic_live_advanced` | `/v3/serp/google/organic/live/advanced` (or `/regular`) |
| Historical SERPs (rotation) | `dataforseo_labs_google_historical_serps` | `/v3/dataforseo_labs/google/historical_serps/live` |
| Search intent | `dataforseo_labs_search_intent` | `/v3/dataforseo_labs/google/search_intent/live` |
| Search volume + CPC | `kw_data_google_ads_search_volume` | `/v3/keywords_data/google_ads/search_volume/live` |
| On-page (page type) | `on_page_instant_pages` | `/v3/on_page/instant_pages` |

If unsure of a V3 path, confirm it with `docs_search({ url: "serp/google/organic/live/advanced" })`.
The request body fields (keyword, location_name, language_code, depth, date_from/date_to,
keywords[]) are the same as documented per endpoint below — only the envelope differs.

**Core principle: live SERP is the source of truth, unioned over time.** The Labs
database is a periodic snapshot: it can miss keywords the domain really ranks for and
fail to record a second competing page. So ranking status ("ranks / doesn't rank /
conflict") is decided **only** from live + historical SERPs, never from the Labs DB.

**Memory rule (non-negotiable):** raw SERP payloads must **never** enter the
orchestrator's context. Fetch + parse each SERP **inside a sub-agent** (its context
absorbs the large payload) and return only the compact slice
`keyword → [(url, position)]` for the target domain's **organic** results. Use the
bundled `extract_domain_urls()` so this is one standardized step. Peak memory then stays
roughly constant no matter how many keywords are in the list.

---

## 1. `serp_organic_live_advanced` — primary detector (per keyword, depth 100)

**Purpose:** decide whether and where the domain ranks, live. Run it for **every input
keyword** — no database pre-filter, no triage.

**Request:**
```json
{ "keyword": "seo api", "location_name": "San Francisco,California,United States",
  "language_code": "en", "depth": 100 }
```
- `depth: 100` — deep enough to catch lower pages and any same-SERP host group.
- `location_name` may be country / region / city.
- MCP exposes only the `advanced` variant — use it here. In standalone code, prefer
  `serp/google/organic/live/regular` (same organic `domain`/`url`/position, smaller
  payload); fall back to `advanced` only if `regular` is unavailable.

**Parse (in the sub-agent):** from `items[]`, keep `type == "organic"` (featured_snippet
collapses onto its organic twin), the target domain's rows only, and return
`(url, rank_group)` (`rank_absolute` fallback). Drop AI Overview, PAA, videos, related
searches, and all per-element metadata — that bulk is the memory cost and the report
never uses it. Page-type signals (`breadcrumb`/`price`/`rating`) may be kept **only** if
you also do page typing in the worker; otherwise page type is inferred later from
URL/slug + the optional URL map.

---

## 2. `dataforseo_labs_historical_serps` — rotation signal (per flagged keyword)

**Purpose:** reconstruct the over-time view. Host-crowding means a single live SERP
usually shows only one URL per domain, so it under-detects true multi-page competition.
Pull the keyword's SERP across several past dates and **union all of the domain's URLs
seen over time.** If Google keeps swapping which page ranks across dates, that
instability is a strong cannibalization signal one snapshot can't see.

**Request:**
```json
{ "keyword": "seo api", "location_name": "United States", "language_code": "en",
  "date_from": "2025-08-01", "date_to": "2026-08-01" }
```
- `location_name` is country-level here.
- Keep `date_to − date_from` within ~12 months — a wider window returns
  `Invalid Field: 'date_from'` (40501).

**VERIFIED response shape — and it differs sharply between V3 and V1:**

Both return a **list of dated snapshots**; the date is `datetime` at the **snapshot**
level, and each snapshot has its own nested `items[]` (the SERP results for that date).

- **V3 (`api_request` → `/v3/dataforseo_labs/google/historical_serps/live`) — FULL items,
  with URL.** Top level `{ ..., "items": [ snapshots ] }`; each snapshot
  `{ "datetime", "items": [ … ] }`; each organic item has `type`, `rank_group`,
  `rank_absolute`, `domain`, **`url`**, `relative_url`, `main_domain`, `title`, `etv`, …
  This is exactly what the over-time model needs — real per-URL rotation.
  ```json
  { "items": [
    { "datetime": "2025-12-03 …",
      "items": [ { "type":"organic","rank_group":4,"domain":"microsoft.com",
                   "url":"https://www.microsoft.com/…/planner/project-management" } ] } ] }
  ```
- **V1 (`dataforseo_labs_google_historical_serps`) — TRIMMED items, NO URL.** Each organic
  item has only `type`, `title`, `domain`, `rank_absolute` — **no `url`, no `rank_group`**.
  The V1 MCP wrapper drops them.

**Parse (in the sub-agent), per connector:**
- **V3:** for each snapshot, take `datetime` as the date and pass the snapshot's nested
  `items[]` straight to `extract_domain_urls()` (it has `url` + `rank_group`, so it works
  exactly like the live SERP). Emit one observation per snapshot:
  `{date, urls:[{url,position}]}`. **Verified live:** on "project management software",
  V3 history showed microsoft.com rotating `/planner/project-management` ↔
  `/planner/simple-project-management`, and reddit.com rotating two threads — real
  cannibalization the engine flags as *strong*.
- **V1:** `extract_domain_urls()` would drop every item (no `url`). You cannot recover the
  exact page. Fall back to a coarse signal (domain-level position/title change across
  dates) or skip history on V1 and rely on the live observation.

**Both connectors:**
- Coverage is per-keyword and **spotty** — only tracked keywords have history; others
  return `[]` (e.g. "womens sneakers" returned nothing for a 4-month window). When empty,
  proceed with the live observation only.
- Keep `date_to − date_from` within ~12 months (a wider window → `Invalid Field:
  'date_from'`, 40501). Snapshots are irregular (~every 1–2 months).

This is a historical *snapshot* source (not "ground truth" for a single moment — the live
SERP is), used for the rotation/over-time signal. Run it for keywords where the live SERP
already showed the domain ranking. **Prefer V3** — only V3 makes the per-URL rotation model
work.

---

## 3. `dataforseo_labs_search_intent` — intent (1 batched call)

For all candidate keywords at once (≤1000). No location; `language_code` required.
Supported: `ar, zh-TW, cs, da, nl, en, fi, fr, de, he, hi, it, ja, ko, ms, nb, pl, pt,
ro, ru, es, sv, th, uk, bg, hr, sr, sl, bs`. Unsupported → run in `en`, note it. Extract
`keyword_intent.label` + `probability` (probability drives the soft-label page-type override).

---

## 4. `kw_data_google_ads_search_volume` — volume + CPC (1 batched call)

Returns `search_volume` **and `cpc`** — both feed `value_at_risk`. CPC is what lifts
high-value low-volume B2B terms up the priority order. (Volume/CPC also appear in
`keyword_info` on some SERP/Labs responses — reuse if already fetched.)

---

## 5. `on_page_instant_pages` — page-type check (optional, last resort)

Only for a URL whose type is still `ambiguous` after the URL map + slug heuristic, and
only for a live candidate. `Product`/`Offer` + price → commercial; `Article`/`BlogPosting`
+ author/date → informational. Cache per URL.

---

## Removed from the pipeline (do not use for detection)

| Endpoint | Why removed |
|----------|-------------|
| `ranked_keywords` | DB snapshot; unreliable for "does it rank." Every input keyword is now live-checked, so it's a large response fetched, parsed, and discarded for no benefit. (Only needed to *seed* a keyword universe in a future "whole-domain, no list" mode.) |
| `page_intersection` | Inherits the DB gap **and** the host-crowding blind spot — the over-time union from live + historical replaces it. |
| `relevant_pages` | Detection reads the domain's URLs from the live SERP; page type comes from URL/slug + SERP signals + the optional URL map. |

**Net pipeline:** `serp_organic_live_advanced` (every keyword, depth 100) ·
`historical_serps` (rotation, flagged keywords) · `search_intent` +
`google_ads_search_volume` (enrichment). Fewer endpoints, all live/over-time, all parsed
in workers → faster and flat on memory.
