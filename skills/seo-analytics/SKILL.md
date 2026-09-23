---
name: seo-analytics
description: >
  Site analytics via the Seline MCP server: visits, unique visitors, page views,
  bounce rate, session duration, top/entry/exit pages, referrers, countries and
  custom events. This is the analytics source for every claude-seo skill and
  agent. Use when the user asks about traffic, visits, sessions, organic
  traffic, landing pages, referrers, conversions, or says "analytics",
  "Seline", "how many visitors", or "traffic trend".
user-invocable: true
argument-hint: "[command] [period]"
license: MIT
compatibility: "Requires the Seline MCP server (mcp__seline__* tools)."
metadata:
  category: seo
---

# Analytics (Seline)

Seline replaces Google Analytics everywhere in claude-seo. Never call GA4, never
ask for a GA4 property id, never suggest installing Google Analytics. Search
Console (`seo-google`) stays the source for queries, impressions, CTR and
indexation. Seline is the source for on-site behaviour.

## Prerequisites

Check the `mcp__seline__*` tools are available before any call. If they are
missing, say the Seline MCP server is not connected and stop; do not fall back
to another analytics provider.

Resolve the project first with `seline_list_projects`, then pass its
`projectId` to every later call. A single-project key can omit `projectId`.

## Routing

| Command | Tools |
|---|---|
| `/seo analytics traffic [period]` | `seline_get_data`, `seline_get_visit_metrics` |
| `/seo analytics pages [period]` | `seline_get_pages` with `type: "top"` |
| `/seo analytics landing [period]` | `seline_get_pages` with `type: "entry"` |
| `/seo analytics exits [period]` | `seline_get_pages` with `type: "exit"` |
| `/seo analytics organic [period]` | the same calls with the organic filter below |
| `/seo analytics events [period]` | `seline_get_events`, `seline_get_custom_events` |
| `/seo analytics revenue [period]` | `seline_get_charges` |

`period` accepts `today`, `24h`, `7d`, `30d`, `6m`, `12m`, `all_time`,
`month_to_date`, `week_to_date`, `year_to_date`, or a `range` of
`{from, to}` ISO timestamps. Default to `30d`. Use `interval: "1 day"` for a
trend, `"1 month"` for anything over 6 months.

## Organic traffic

Seline has no channel grouping. Approximate organic search with a referrer
filter:

```
filters: { referrer: "contains:google;contains:bing;contains:duckduckgo;contains:ecosia;contains:brave;contains:yahoo" }
```

Say in the output that this is a referrer approximation, not a modelled
channel. Two known undercounts, name them whenever you report an organic
number:

- AI assistants (ChatGPT, Perplexity, Claude, Copilot, Gemini) often send
  referrer-less sessions that land in direct. Filter
  `referrer: "contains:chatgpt;contains:perplexity;contains:claude;contains:copilot"`
  for the part that is visible, and call the rest unmeasurable.
- Search Console clicks and Seline visits never match. GSC counts clicks on the
  SERP, Seline counts sessions that loaded the page. Report both, never
  reconcile them into one number.

## Reading the numbers

- `seline_get_data` returns unique visitors and page views over time.
- `seline_get_visit_metrics` returns visits, page views, average session
  duration and bounce rate for the same filters.
- `seline_get_pages` ranks pages: `top` by page views, `entry` by session
  starts, `exit` from multi-page sessions only (bounces excluded).
- Pair a page's entry count with its GSC impressions before calling anything a
  content win. One number alone proves nothing.

## Cross-skill integration

- **seo-audit**: traffic and landing-page evidence for the audit come from here.
- **seo-google**: Search Console and CrUX only. It holds no traffic data.
- **seo-content**: rank pages for refresh by entry sessions here, by query
  demand in GSC.
- **seo-drift**: compare a period against the previous one with two `range`
  calls, never a single relative period.

## Error handling

| Scenario | Action |
|---|---|
| No `mcp__seline__*` tools | Report the Seline MCP server is not connected. Stop. |
| Multiple projects, none named | List them with `seline_list_projects` and ask which one. |
| Empty result for a period | Report zero explicitly. Never interpolate or estimate. |
| A number is needed that Seline does not hold | Say so and name the source that does (GSC, Stripe, DataForSEO). |
