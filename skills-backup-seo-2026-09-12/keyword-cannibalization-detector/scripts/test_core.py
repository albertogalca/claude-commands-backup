"""
Calibration tests for the over-time cannibalization engine.  Run:  python test_core.py

Cannibalization is now "the domain has ≥2 of its own pages competing for the query over
time," detected by unioning the domain's URLs across a live SERP + historical snapshots.
Verdict is driven by: best position reached, number of competing pages, and whether
Google ROTATES which page it shows across snapshots (instability = real split).
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from cannibalization import (
    analyze_keyword, extract_domain_urls, aggregate, ctr, classify_page_type,
)

FAILS = []
def check(name, got, want):
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")
    if not ok:
        FAILS.append(name)

def kw(keyword, obs, intent_label, prob, vol=None, cpc=None):
    observations = [{"date": d, "urls": [{"url": u, "position": p, "type": t} for (u, p, t) in lst]}
                    for (d, lst) in obs]
    return {"keyword": keyword, "observations": observations,
            "intent_label": intent_label, "intent_probability": prob,
            "search_volume": vol, "cpc": cpc}

def verdict_of(k): return analyze_keyword(k)["verdict"]

A = "https://s.com/products/a"; B = "https://s.com/products/b"; C = "https://s.com/products/c"
BLOGA = "https://s.com/blog/a"; BLOGB = "https://s.com/blog/b"

print("── over-time calibration ──")

# 1. commercial, two product pages, Google rotates top across dates, best #8 → strong
check("C1 rotate two products #8", verdict_of(kw("x", [
    ("2026-05", [(A, 8, "commercial")]), ("2026-06", [(B, 10, "commercial")]),
    ("2026-07", [(A, 9, "commercial")])], "commercial", 0.9, 3400, 2.0)), "strong candidate")

# 2. only one page ever ranks → clean
check("C2 single page", analyze_keyword(kw("x", [
    ("2026-06", [(A, 5, "commercial")]), ("2026-07", [(A, 7, "commercial")])],
    "commercial", 0.9))["status"], "clean")

# 3. two pages but both buried (best #55) → harmless
check("C3 both buried #55", verdict_of(kw("x", [
    ("2026-06", [(A, 55, "commercial")]), ("2026-07", [(B, 60, "commercial")])],
    "commercial", 0.9, 700, 4.0)), "harmless overlap")

# 4. two pages high but NO rotation (one stable top, second co-listed once) → investigate
check("C4 two pages no rotation", verdict_of(kw("x", [
    ("2026-06", [(BLOGA, 9, "informational"), (BLOGB, 14, "informational")]),
    ("2026-07", [(BLOGA, 10, "informational")])], "informational", 0.9, 1100)), "investigate")

# 5. informational, two blogs, rotation, best #9 → strong
check("C5 rotate two blogs #9", verdict_of(kw("x", [
    ("2026-06", [(BLOGA, 9, "informational")]), ("2026-07", [(BLOGB, 12, "informational")])],
    "informational", 0.9, 1100)), "strong candidate")

# 6. commercial, best #35 (below top band 30 but < deep 40), rotating → investigate
check("C6 commercial #35 rotating", verdict_of(kw("x", [
    ("2026-06", [(A, 35, "commercial")]), ("2026-07", [(B, 38, "commercial")])],
    "commercial", 0.9, 900, 3.0)), "investigate")

# 7. informational query, mixed page types (product + blog), rotating, best #10 → investigate (different needs)
check("C7 info mixed types", verdict_of(kw("x", [
    ("2026-06", [(A, 10, "commercial")]), ("2026-07", [(BLOGB, 12, "informational")])],
    "informational", 0.9, 900)), "investigate")

# 8. B2B: soft informational label + /apis/ page → override commercial; rotating #6 → strong
b2b = analyze_keyword(kw("seo api", [
    ("2026-06", [("https://s.com/apis/seo", 6, "commercial")]),
    ("2026-07", [("https://s.com/blog/seo-api", 9, "informational")])],
    "informational", 0.60, 40, 28.0))
check("C8 B2B override verdict", b2b["verdict"], "strong candidate")
check("C8 B2B effective intent", b2b["effective_intent"], "commercial")
check("C8 B2B overridden flag", b2b["intent_overridden_by_page_type"], True)
check("C8 B2B has value", (b2b["value_at_risk"] or 0) > 0, True)

# 9. three pages rotating, best #7 → strong
check("C9 three pages rotating", verdict_of(kw("x", [
    ("2026-05", [(A, 7, "commercial")]), ("2026-06", [(B, 9, "commercial")]),
    ("2026-07", [(C, 12, "commercial")])], "commercial", 0.9, 4000, 2.0)), "strong candidate")

# 10. commercial, two pages high but stable top (no rotation) → investigate
check("C10 commercial stable co-list", verdict_of(kw("x", [
    ("2026-06", [(A, 4, "commercial"), (B, 8, "commercial")]),
    ("2026-07", [(A, 5, "commercial")])], "commercial", 0.9, 2600, 2.5)), "investigate")

print("── priority: value beats equal-traffic cheap term; niche not floored ──")
recs = [
    analyze_keyword(kw("seo api", [("2026-06", [("https://s.com/apis/seo", 4, "commercial")]),
                                    ("2026-07", [("https://s.com/blog/seo-api", 7, "informational")])],
                       "informational", 0.6, 40, 28.0)),
    analyze_keyword(kw("free seo tips", [("2026-06", [(BLOGA, 6, "informational")]),
                                         ("2026-07", [(BLOGB, 9, "informational")])],
                       "informational", 0.9, 80, 0.15)),
]
ranked = aggregate(recs)
check("money term ranked first", ranked[0]["keyword"], "seo api")
seo = next(r for r in ranked if r["keyword"] == "seo api")
check("niche high-CPC not floored (>40)", seo["priority_score"] > 40, True)

print("── rotation + fields ──")
r1 = analyze_keyword(kw("x", [("2026-05", [(A, 8, "commercial")]), ("2026-06", [(B, 10, "commercial")]),
                              ("2026-07", [(A, 9, "commercial")])], "commercial", 0.9, 3400, 2.0))
check("rotation_count", r1["rotation_count"], 2)
check("rotating flag", r1["rotating"], True)
check("n_pages", r1["n_pages"], 2)
check("n_snapshots", r1["n_snapshots"], 3)
check("best_pos", r1["best_pos"], 8)

print("── mixed-intent recommendation is NOT merge ──")
mix = analyze_keyword(kw("x", [("2026-06", [("https://s.com/pricing", 4, "commercial")]),
                               ("2026-07", [("https://s.com/blog/guide", 8, "informational")])],
                          "commercial", 0.9, 2000, 5.0))
check("mixed rec avoids merge", "Do NOT merge" in mix["recommendation"], True)

print("── extraction: dedupe / feature-collapse / subdomain scope ──")
items = [
    {"type": "organic", "url": "https://ex.com/p/a", "rank_group": 51},
    {"type": "organic", "url": "https://ex.com/p/a?utm=x", "rank_group": 59},
    {"type": "featured_snippet", "url": "https://ex.com/p/a", "rank_group": 1},
    {"type": "organic", "url": "https://www.ex.com/p/b", "rank_group": 12},
    {"type": "people_also_ask", "url": "https://ex.com/p/paa", "rank_group": 3},
    {"type": "organic", "url": "https://docs.ex.com/guide", "rank_group": 4},
]
root_only = extract_domain_urls(items, "ex.com", include_subdomains=False)
check("dedupe keeps best pos", min(u["position"] for u in root_only), 1)
check("PAA excluded", any("paa" in u["url"] for u in root_only), False)
check("docs excluded root-only", any("docs." in u["url"] for u in root_only), False)
check("root-only count", len(root_only), 2)
check("subdomain included when opted in",
      any("docs." in u["url"] for u in extract_domain_urls(items, "ex.com", include_subdomains=True)), True)

print("── CTR curve + classifier ──")
check("ctr monotone", ctr(1) > ctr(5) > ctr(10) > ctr(20) > ctr(50), True)
check("url map wins", classify_page_type("https://s.com/apis/seo", url_map={"/apis/*": "commercial"}), "commercial")
check("price signal", classify_page_type("https://s.com/x/y", signals={"price": "$29"}), "commercial")
check("blog slug", classify_page_type("https://s.com/blog/post"), "informational")
check("unknown ambiguous", classify_page_type("https://s.com/x/y"), "ambiguous")

print()
if FAILS:
    print(f"FAILED {len(FAILS)}: {', '.join(FAILS)}"); sys.exit(1)
print("ALL TESTS PASSED")
