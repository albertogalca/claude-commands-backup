# Keyword Cannibalization Detector

Detects **true** keyword cannibalization — one site fielding more than one of its own
pages for a query — from **live** Google SERPs unioned over time (host-crowding means the
pages rarely appear together in one scrape; the tell is Google *rotating* which page it
ranks). Reads the split through keyword intent and page type, prices it by value at risk,
and recommends a specific fix per case. Built for SEO agencies and in-house SEO teams.

## Why it exists

Teams flag "cannibalization" off raw position overlap and waste hours consolidating pages
that were never competing — while the real conflicts (the domain rotating several of its
own pages for one commercial term) go unnoticed because they never co-appear in a single
SERP. This skill decides ranking status only from **live** SERPs (never a stale database),
unions the domain's URLs across live + historical snapshots to see over-time rotation, and
keeps memory flat by fetching/parsing inside sub-agents — so it scales to large lists.

## Inputs

Domain · keyword list (or a file) · location + language · output folder.

## Outputs

- `[domain]_cannibalization_[YYYYMMDD].pdf` — diagnostic report (summary counts,
  conflicts ordered by value at risk, a section per flagged keyword with verdict +
  reason + fix).
- `[domain]_cannibalization_[YYYYMMDD].csv` — actionable worklist, one row per candidate
  keyword, sorted so the costliest conflicts (leaked clicks × CPC) come first.

## Data

All data via **DataForSEO**, live-first and over-time. Ranking status comes only from live
Google SERPs, never a database snapshot. Endpoints: `serp_organic_live_advanced` (every
keyword, depth 100 — source of truth), `dataforseo_labs_historical_serps` (rotation / over-
time union), `dataforseo_labs_search_intent`, `kw_data_google_ads_search_volume` (volume +
CPC), `on_page_instant_pages` (last-resort page-type check). All SERP fetching + parsing
runs in sub-agents so raw payloads never reach the orchestrator's context — memory stays
flat regardless of list size.

## Connectors (V1 / V3)

Works with **either** DataForSEO MCP connector, and picks the right one automatically:

- If **both a V1 and a V3 connector are connected → it uses V3**; if only one is
  connected, it uses that one. Server prefixes are never hardcoded.
- The two call the same endpoints differently but return the **same** structure, so the
  engine is unchanged either way:
  - **V1** — one named tool per endpoint, e.g. `serp_organic_live_advanced({…})`.
  - **V3** — a single generic `api_request({method, path, data:[{…}]})`, e.g.
    `path:"/v3/serp/google/organic/live/advanced"`; also exposes `docs_search` and the
    lighter `/regular` SERP.
- **Historical rotation needs V3.** The V1 historical-SERP wrapper omits `url`, so per-URL
  over-time rotation only works on V3 (V1 falls back to the live snapshot). All four V3
  paths are verified in `references/endpoints.md` → "Two calling conventions".

## Layout

```
keyword-cannibalization-detector/
├── SKILL.md                     # workflow, step by step
├── references/
│   ├── decision-matrix.md       # how the engine decides (CTR split + value at risk)
│   └── endpoints.md             # live-first endpoints, V1/V3 calling conventions, fields
├── scripts/
│   ├── cannibalization.py       # deterministic engine: analysis + CSV
│   ├── test_core.py             # calibration unit tests (12 cases + B2B + hygiene)
│   ├── build_report.py          # PDF generator (reportlab; Helvetica fallback)
│   └── fonts/                   # DejaVu TTFs for full Unicode
└── evals/evals.json             # test prompts + assertions
```

## Requirements

- DataForSEO connected and authenticated.
- Python with `reportlab` (`pip install reportlab`) for the PDF. The engine and CSV use
  only the standard library. Run `python scripts/test_core.py` to verify the engine.
