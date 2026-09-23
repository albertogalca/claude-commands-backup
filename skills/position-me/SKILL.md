---
name: position-me
description: Whole-site positioning review across SEO/AEO/GEO, UI/UX psychology and copywriting. Use when asked to review or evaluate a website's positioning, or why a site does not convert. Covers every key page in a live browser and produces a scored report with charts and fixes ordered by impact.
---

# Position-Me: Website Positioning Review

Review a whole website as three specialists at once: an SEO/AEO/GEO specialist, a UI/UX psychologist, and a direct-response copywriter. The reader is a founder who wants to know why the site does not convert and what to change first.

Cover the full site, not the homepage alone: header, hero, body and footer, plus the about, pricing and blog pages (or their equivalents), and at least one blog post or case study read in full. A review built from one page misses most of the positioning. Write in a professional, direct consulting tone, with no emojis.

## Lenses

1. **UI/UX psychology**: cognitive load with the LIFT model (value, relevance, clarity, anxiety, distraction, urgency) and Hick's law.
2. **Copy**: the hero through problem, agitation, solution. Rewrite weak copy on the spot.
3. **AI and search (AEO/GEO/SEO)**: `llms.txt`, `sitemap.xml`, JSON-LD (`FAQPage`, `SoftwareApplication`), semantic density, citation readiness.
4. **Visual and interaction**: look at the rendered pages, not only the code. Judge clutter, hierarchy and breathing room from screenshots.
5. **Content**: read the actual posts. Name generic fluff and give specific, lateral content ideas.

## Workflow

1. If there is no URL, ask for it.
2. Capture the site in a live browser with the Claude in Chrome tools: scroll each key page top to bottom and take screenshots, then read them into context. Use `scripts/extract_links.py` to list pages. If the browser tools are unavailable, say so and fall back to fetching the HTML.
3. Check `[URL]/llms.txt`, `[URL]/sitemap.xml` and the JSON-LD in the DOM.
4. Analyze with `references/EVALUATION_SOP.md`.
5. Report in the format of `references/REPORT_TEMPLATE.md`: 0-100 scores, Markdown charts, and a problem-to-solution matrix, ordered by impact.
