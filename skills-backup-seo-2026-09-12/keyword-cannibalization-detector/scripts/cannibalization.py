"""
Keyword Cannibalization — deterministic core (over-time model).

This module is the diagnostic engine. It takes already-parsed, compact observations
(the target domain's organic (url, position) per SERP snapshot, across one or more
dates) and returns verdicts, value-at-risk, priorities, reasons, and recommendations.
It performs NO network I/O and never sees raw API payloads — fetching + parsing happen
upstream (in a sub-agent/worker) and only the small extract reaches here. Behaviour is
locked by test_core.py.

WHY OVER-TIME
-------------
Modern Google applies host-crowding: usually only ONE URL per domain shows per SERP.
So "≥2 of my pages in a single snapshot" almost never fires, and a single scrape
under-detects real cannibalization. The true pattern is: **the domain has more than one
of its own pages competing for the query, and Google rotates which one it shows across
searches/dates.** We detect it by unioning the domain's URLs seen for a keyword across a
live SERP + several historical SERP snapshots.

TWO QUESTIONS, KEPT SEPARATE
----------------------------
1. Is authority being SPLIT? (structural, volume-free) — the domain has ≥2 distinct
   pages competing, and especially if Google *rotates* which page ranks across dates
   (instability = it can't consolidate). Best reached position gates whether it matters.
2. How much does it COST? (economic, sets priority) — value_at_risk = leaked_clicks ×
   CPC, leaked_clicks = CTR(best position) × volume × fragmentation. Blending CPC (not
   raw volume) floats high-value low-volume terms up.

Page type can override a *soft* intent label (a /pricing/ or product page ranking for a
term makes it commercial even if the classifier said informational at low confidence).
Page type also chooses the *fix*, not the severity.
"""

import sys, json, fnmatch, csv
from urllib.parse import urlsplit

# ── CTR curve (aggregate desktop organic) ─────────────────────────────────────────
CTR_TABLE = {
    1: 0.281, 2: 0.152, 3: 0.099, 4: 0.070, 5: 0.053,
    6: 0.041, 7: 0.033, 8: 0.028, 9: 0.024, 10: 0.021,
    11: 0.019, 12: 0.017, 13: 0.015, 14: 0.014, 15: 0.013,
    16: 0.012, 17: 0.011, 18: 0.0105, 19: 0.010, 20: 0.0095,
}

def ctr(pos):
    if pos is None or pos < 1:
        return 0.0
    pos = int(pos)
    if pos in CTR_TABLE:
        return CTR_TABLE[pos]
    if pos <= 30:
        return round(0.0095 - (pos - 20) * 0.00033, 5)
    if pos <= 50:
        return round(0.0062 - (pos - 30) * 0.00013, 5)
    if pos <= 100:
        return round(max(0.0035 - (pos - 50) * 0.00005, 0.0010), 5)
    return 0.0008

# ── Thresholds ────────────────────────────────────────────────────────────────────
DEEP_POS   = 40      # best page never reaches here → nothing worth splitting → harmless
SOFT_INTENT = 0.80   # intent-label probability below this can be overridden by page type
BAND = {"COMMERCIAL": 30, "INFORMATIONAL": 20}   # "ranks high enough to matter" cutoff

COMMERCIAL_SLUGS = (
    "/product", "/products", "/p/", "/pd/", "/item", "/shop", "/store", "/category",
    "/categories", "/collection", "/collections", "/c/", "/service", "/services",
    "/solutions", "/pricing", "/plans", "/buy", "/order", "/apis", "/api",
)
INFO_SLUGS = (
    "/blog", "/news", "/article", "/articles", "/post", "/posts", "/guide", "/guides",
    "/how-to", "/howto", "/learn", "/resources", "/tips", "/faq", "/help", "/docs",
    "/glossary", "/wiki", "/magazine", "/stories",
)


# ── URL handling ────────────────────────────────────────────────────────────────

def normalize_host(host):
    host = (host or "").lower().strip()
    return host[4:] if host.startswith("www.") else host

def url_key(url):
    try:
        parts = urlsplit(url if "//" in url else "http://" + url)
        host = normalize_host(parts.netloc)
        path = (parts.path or "/").rstrip("/") or "/"
        return f"{host}{path}"
    except Exception:
        return (url or "").lower().rstrip("/")

def host_of(url):
    try:
        return normalize_host(urlsplit(url if "//" in url else "http://" + url).netloc)
    except Exception:
        return ""

def domain_matches(url, domain, include_subdomains):
    host = normalize_host(host_of(url))
    dom = normalize_host(domain)
    return host == dom or (include_subdomains and host.endswith("." + dom))


# ── Page-type classification ──────────────────────────────────────────────────────

def classify_page_type(url, url_map=None, signals=None):
    """commercial | informational | ambiguous. URL map > SERP signals > slug heuristic."""
    path = "/" + (urlsplit(url if "//" in url else "http://" + url).path or "").lstrip("/")
    path_l = path.lower()
    if url_map:
        for pattern, ptype in url_map.items():
            pat = pattern.lower()
            if fnmatch.fnmatch(path_l, pat) or fnmatch.fnmatch(url.lower(), pat) or path_l.startswith(pat.rstrip("*")):
                return ptype
    signals = signals or {}
    if signals.get("price") or signals.get("rating") or signals.get("is_shop"):
        return "commercial"
    crumb = signals.get("breadcrumb")
    crumb = " ".join(map(str, crumb)).lower() if isinstance(crumb, list) else str(crumb or "").lower()
    if crumb:
        if any(s in crumb for s in ("shop", "products", "product", "category", "collections", "pricing")):
            return "commercial"
        if any(s in crumb for s in ("blog", "news", "guide", "articles", "resources")):
            return "informational"
    if path_l in ("/", ""):
        return "commercial"
    comm = any(s in path_l for s in COMMERCIAL_SLUGS)
    info = any(s in path_l for s in INFO_SLUGS)
    if comm and not info:
        return "commercial"
    if info and not comm:
        return "informational"
    return "ambiguous"


# ── Extraction: one SERP snapshot → the domain's organic (url, position) ──────────

def extract_domain_urls(serp_items, domain, include_subdomains=False, url_map=None):
    """
    Bundled extractor (rec 11). From one SERP's items, return the domain's genuine
    ranking pages as [{url, position, type, signals}], deduped by URL (best position).
    Organic only; featured_snippet collapses onto its organic twin; PAA/video/related
    ignored. This is the ONLY place raw-ish items are read — callers pass the small result.
    """
    best = {}
    for it in serp_items or []:
        if it.get("type") not in ("organic", "featured_snippet"):
            continue
        url = it.get("url") or ""
        if not url or not domain_matches(url, domain, include_subdomains):
            continue
        pos = it.get("rank_group")
        if pos is None:
            pos = it.get("rank_absolute")
        if pos is None:
            continue
        k = url_key(url)
        signals = {"price": it.get("price"), "rating": it.get("rating"),
                   "breadcrumb": it.get("breadcrumb"), "is_shop": it.get("is_shop") or it.get("shop")}
        rec = {"url": url, "position": int(pos), "signals": signals}
        if k not in best or rec["position"] < best[k]["position"]:
            if k in best and not any(signals.values()) and any(best[k]["signals"].values()):
                rec["signals"] = best[k]["signals"]
            best[k] = rec
    urls = sorted(best.values(), key=lambda r: r["position"])
    for r in urls:
        r["type"] = classify_page_type(r["url"], url_map=url_map, signals=r["signals"])
    return urls


# ── Intent bucketing + soft-label override ────────────────────────────────────────

def bucket_intent(label):
    return "COMMERCIAL" if (label or "").lower() in ("commercial", "transactional") else "INFORMATIONAL"

def effective_intent(label, probability, page_types):
    base = bucket_intent(label)
    if base == "COMMERCIAL":
        return base, False
    if any(t == "commercial" for t in page_types) and (probability is None or probability < SOFT_INTENT):
        return "COMMERCIAL", True
    return base, False


# ── Over-time union + analysis ────────────────────────────────────────────────────

def _union_observations(observations):
    """
    observations: [{date, urls:[{url,position,type?,signals?}]}, ...]  (each already extracted)
    Returns:
      pages: url_key -> {url, type, best_pos, positions:[(date,pos)], dates:set}
      top_by_date: date -> url_key of the domain's best-positioned page that date
    """
    pages, top_by_date = {}, {}
    for obs in observations:
        date = obs.get("date", "live")
        urls = sorted(obs.get("urls", []), key=lambda u: u["position"])
        if not urls:
            continue
        top_by_date[date] = url_key(urls[0]["url"])
        for u in urls:
            k = url_key(u["url"])
            p = pages.get(k)
            if p is None:
                pages[k] = {"url": u["url"], "type": u.get("type"), "best_pos": u["position"],
                            "positions": [(date, u["position"])], "dates": {date}}
            else:
                p["best_pos"] = min(p["best_pos"], u["position"])
                p["positions"].append((date, u["position"]))
                p["dates"].add(date)
                if not p["type"] and u.get("type"):
                    p["type"] = u["type"]
    return pages, top_by_date

SEVERITY = {"strong candidate": 1.0, "investigate": 0.55, "harmless overlap": 0.10}

def analyze_keyword(kw):
    """
    kw = {
      keyword,
      observations: [{date, urls|serp_items}, ...]   # ≥1; live SERP + historical dates
        (legacy: kw["urls"] or kw["serp_items"] is treated as a single "live" observation),
      intent_label, intent_probability, search_volume, cpc, url_map?, domain?, include_subdomains?
    }
    """
    url_map = kw.get("url_map")
    domain = kw.get("domain")
    inc_sub = kw.get("include_subdomains", False)

    # normalise to observations, each with extracted `urls`
    observations = kw.get("observations")
    if observations is None:
        if "urls" in kw:
            observations = [{"date": "live", "urls": kw["urls"]}]
        elif "serp_items" in kw:
            observations = [{"date": "live", "serp_items": kw["serp_items"]}]
        else:
            observations = []
    for obs in observations:
        if "urls" not in obs and "serp_items" in obs:
            obs["urls"] = extract_domain_urls(obs["serp_items"], domain, inc_sub, url_map)
        for u in obs.get("urls", []):
            if not u.get("type"):
                u["type"] = classify_page_type(u["url"], url_map=url_map, signals=u.get("signals"))

    pages, top_by_date = _union_observations(observations)
    n_dates = len({o.get("date", "live") for o in observations})

    if len(pages) < 2:
        return {"keyword": kw.get("keyword"), "status": "clean",
                "n_pages": len(pages), "n_snapshots": n_dates,
                "urls": [_page_out(p) for p in pages.values()],
                "reason": ("Only one page of the domain ranks for this query across all snapshots — "
                           "no competition." if pages else
                           "The domain does not rank in the top 100 for this query.")}

    ordered = sorted(pages.values(), key=lambda p: p["best_pos"])
    primary, secondary = ordered[0], ordered[1]
    best_pos = primary["best_pos"]
    n_pages = len(pages)
    rotation_count = len(set(top_by_date.values()))   # distinct URLs that held the top domain slot
    page_types = [primary.get("type"), secondary.get("type")]

    eint, overridden = effective_intent(kw.get("intent_label"), kw.get("intent_probability"), page_types)
    verdict = _verdict(eint, best_pos, n_pages, rotation_count, page_types)

    vol, cpc = kw.get("search_volume"), kw.get("cpc")
    frag = (n_pages - 1) / n_pages
    clicks_at_risk = round(ctr(best_pos) * vol * frag) if vol else (0 if vol == 0 else None)
    value_at_risk = round((clicks_at_risk or 0) * cpc, 2) if (clicks_at_risk and cpc) else \
        (0.0 if (clicks_at_risk is not None and cpc is not None) else None)

    rec = {
        "keyword": kw.get("keyword"), "status": "candidate",
        "intent": bucket_intent(kw.get("intent_label")).lower(),
        "intent_label": kw.get("intent_label"), "intent_probability": kw.get("intent_probability"),
        "intent_overridden_by_page_type": overridden, "effective_intent": eint.lower(),
        "search_volume": vol, "cpc": cpc,
        "n_pages": n_pages, "n_snapshots": n_dates,
        "rotation_count": rotation_count, "rotating": rotation_count >= 2,
        "best_pos": best_pos,
        "urls": [_page_out(p) for p in ordered],
        "pair": {"stronger": _page_out(primary), "weaker": _page_out(secondary)},
        "clicks_at_risk": clicks_at_risk, "value_at_risk": value_at_risk,
        "verdict": verdict,
    }
    rec["reason"] = _reason(rec)
    rec["recommendation"] = _recommendation(rec)
    return rec

def _page_out(p):
    return {"url": p["url"], "position": p["best_pos"], "type": p.get("type"),
            "dates": sorted(p["dates"]) if isinstance(p.get("dates"), set) else p.get("dates")}

def _verdict(eint, best_pos, n_pages, rotation_count, page_types):
    if n_pages < 2:
        return "harmless overlap"
    if best_pos > DEEP_POS:                      # never ranks high enough to matter
        return "harmless overlap"
    rotating = rotation_count >= 2
    band = BAND[eint]
    if best_pos <= band:
        v = "strong candidate" if rotating else "investigate"
    else:                                        # band < best_pos <= DEEP_POS
        v = "investigate" if (rotating or eint == "COMMERCIAL") else "harmless overlap"
    # informational query where the competing pages are different types = different needs
    if v == "strong candidate" and eint == "INFORMATIONAL" and _mixed_types(page_types):
        v = "investigate"
    return v

def _mixed_types(types):
    return ("commercial" in types) and ("informational" in types)


# ── Reason & recommendation ───────────────────────────────────────────────────────

def _pct(x): return f"{round(x * 100)}%"
def _money(v):
    if v is None:
        return None
    return f"${v:,.0f}/mo" if v >= 1 else f"${v:,.2f}/mo"
def _short(url):
    p = urlsplit(url if "//" in url else "http://" + url)
    return (host_of(url) + (p.path or "/")).rstrip("/") or host_of(url)

def _reason(r):
    n, best = r["n_pages"], r["best_pos"]
    val, car = _money(r["value_at_risk"]), r["clicks_at_risk"]
    ovr = " (re-classified commercial from the ranking page type)" if r["intent_overridden_by_page_type"] else ""
    if r["verdict"] == "harmless overlap":
        if best > DEEP_POS:
            return (f"The domain's best page only reaches #{best} for this query — too deep to earn "
                    f"meaningful clicks, so competing pages aren't costing anything.")
        return (f"The domain fields {n} pages here but Google keeps one at #{best} without swapping — "
                f"authority isn't being split.")
    rot = (f"Google rotates between {r['rotation_count']} of them across {r['n_snapshots']} snapshots"
           if r["rotating"] else f"they co-rank across {r['n_snapshots']} snapshots")
    valpart = f" ~{car} clicks/mo{(' ≈ ' + val) if val else ''} at risk." if car else "."
    return (f"{n} of the domain's own pages compete for this {r['effective_intent']} query{ovr}; "
            f"{rot}; best position #{best}.{valpart}")

def _recommendation(r):
    if r["verdict"] == "harmless overlap":
        return f"No action — one page holds #{r['best_pos']} without rotation, or all pages sit too deep."
    s, w = r["pair"]["stronger"], r["pair"]["weaker"]
    ts, tw = s.get("type"), w.get("type")
    su, wu = _short(s["url"]), _short(w["url"])
    if ts == "commercial" and tw == "commercial":
        return (f"Consolidate: merge the weaker page {wu} (#{w['position']}) into the stronger "
                f"{su} (#{s['position']}) and 301-redirect it — one authoritative page outranks rotating ones.")
    if ts == "informational" and tw == "informational":
        return (f"Differentiate the two articles so each owns a distinct query, or consolidate into one "
                f"guide and 301 the weaker {wu}.")
    if _mixed_types([ts, tw]):
        comm = su if ts == "commercial" else wu
        info = wu if ts == "commercial" else su
        return (f"Different intents — keep both: canonicalize / de-optimize the informational page {info} "
                f"for this term and point internal links + canonical at the commercial page {comm}. "
                f"Do NOT merge them.")
    return (f"Clarify page roles: decide which of {su} (#{s['position']}) and {wu} (#{w['position']}) "
            f"should own this term, then differentiate or consolidate accordingly.")


# ── Aggregate priority + summary ──────────────────────────────────────────────────

def aggregate(records):
    cands = [r for r in records if r.get("status") == "candidate"]
    max_val = max((r.get("value_at_risk") or 0) for r in cands) if cands else 0
    max_clk = max((r.get("clicks_at_risk") or 0) for r in cands) if cands else 0
    for r in cands:
        val, clk = r.get("value_at_risk") or 0, r.get("clicks_at_risk") or 0
        if max_val > 0:
            econ = 0.75 * (val / max_val) + 0.25 * (clk / max_clk if max_clk else 0)
        elif max_clk > 0:
            econ = clk / max_clk
        else:
            econ = 0.15
        r["priority_score"] = round(100 * SEVERITY[r["verdict"]] * (0.15 + 0.85 * econ), 1)
    cands.sort(key=lambda r: (r["priority_score"], r.get("best_pos", 999) * -1, r.get("value_at_risk") or 0), reverse=True)
    for i, r in enumerate(cands, 1):
        r["priority_rank"] = i
    return cands

def summarize(all_records, checked_count):
    cands = [r for r in all_records if r.get("status") == "candidate"]
    return {
        "checked": checked_count,
        "clean": sum(1 for r in all_records if r.get("status") == "clean"),
        "candidates": len(cands),
        "strong": sum(1 for r in cands if r["verdict"] == "strong candidate"),
        "investigate": sum(1 for r in cands if r["verdict"] == "investigate"),
        "harmless": sum(1 for r in cands if r["verdict"] == "harmless overlap"),
    }


# ── CSV worklist ──────────────────────────────────────────────────────────────────

CSV_HEADER = [
    "priority_rank", "priority_score", "keyword", "search_intent", "effective_intent",
    "intent_probability", "intent_overridden_by_page_type", "search_volume", "cpc",
    "clicks_at_risk", "value_at_risk", "verdict", "n_pages", "rotating", "rotation_count",
    "n_snapshots", "best_pos",
    "page_a_url", "page_a_position", "page_a_type",
    "page_b_url", "page_b_position", "page_b_type",
    "all_domain_urls", "reason", "recommended_action",
]

def write_csv(cands, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_HEADER)
        for r in cands:
            s, wk = r["pair"]["stronger"], r["pair"]["weaker"]
            all_urls = " | ".join(f"{u['url']}@{u['position']}" for u in r["urls"])
            w.writerow([
                r["priority_rank"], r["priority_score"], r["keyword"], r["intent"], r["effective_intent"],
                r.get("intent_probability"), r.get("intent_overridden_by_page_type"),
                r.get("search_volume"), r.get("cpc"), r.get("clicks_at_risk"), r.get("value_at_risk"),
                r["verdict"], r["n_pages"], r["rotating"], r["rotation_count"], r["n_snapshots"], r["best_pos"],
                s["url"], s["position"], s.get("type"), wk["url"], wk["position"], wk.get("type"),
                all_urls, r["reason"], r["recommendation"],
            ])


# ── CLI ───────────────────────────────────────────────────────────────────────────

def _flagged_for_report(cands):
    out = []
    for r in cands:
        out.append({
            "priority_rank": r["priority_rank"], "priority_score": r["priority_score"],
            "keyword": r["keyword"], "intent": r["effective_intent"],
            "intent_probability": r.get("intent_probability") or 0,
            "search_volume": r.get("search_volume"), "cpc": r.get("cpc"),
            "clicks_at_risk": r.get("clicks_at_risk"), "value_at_risk": r.get("value_at_risk"),
            "verdict": r["verdict"], "n_pages": r["n_pages"], "rotating": r["rotating"],
            "best_pos": r["best_pos"], "n_snapshots": r["n_snapshots"],
            "urls": [{"url": u["url"], "position": u["position"], "type": u.get("type")} for u in r["urls"]],
            "reason": r["reason"], "recommendation": r["recommendation"],
        })
    return out

def analyze_file(in_path, out_path=None):
    with open(in_path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    meta = data.get("meta", {})
    domain, inc_sub, url_map = meta.get("domain", ""), meta.get("include_subdomains", False), meta.get("url_map")
    records = []
    for kw in data.get("keywords", []):
        kw.setdefault("domain", domain)
        kw.setdefault("include_subdomains", inc_sub)
        kw.setdefault("url_map", url_map)
        records.append(analyze_keyword(kw))
    cands = aggregate(records)
    summary = summarize(records, checked_count=len(data.get("keywords", [])))
    payload = {"meta": meta, "summary": summary, "flagged": _flagged_for_report(cands), "records": records}
    out = json.dumps(payload, ensure_ascii=False, indent=2)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(out)
        csv_path = meta.get("csv_out") or (out_path.rsplit(".", 1)[0] + ".csv")
        write_csv(cands, csv_path)
        payload["csv_path"] = csv_path
        print(out_path); print(csv_path)
    else:
        print(out)
    return payload


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "analyze":
        analyze_file(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        print("Usage: python cannibalization.py analyze <fetched.json> [out.json]")
        sys.exit(1)
