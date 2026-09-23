"""
Keyword Cannibalization -- PDF report generator.

Usage:
    python build_report.py <path_to_data.json>

Writes <domain>_cannibalization_<date>.pdf next to the JSON (or to data["meta"]["out_path"]
if provided). See the DATA SHAPE block below for the exact JSON the skill must assemble.

DATA SHAPE
----------
{
  "meta": {
    "domain": "acme.com",
    "date": "2026-07-03",
    "location": "United States",
    "language": "en",
    "out_path": "reports/acme.com_cannibalization_20260703.pdf",   # optional
    "intent_lang_fallback": false                                    # optional
  },
  "summary": {
    "checked": 40, "clean": 30, "candidates": 10,
    "strong": 3, "investigate": 4, "harmless": 3
  },
  "flagged": [                       # ALL candidates (>=2 same-domain URLs), priority-sorted
    {
      "priority_rank": 1,
      "priority_score": 88.4,
      "keyword": "trail running shoes",
      "intent": "commercial",        # commercial | transactional | informational | navigational
      "intent_probability": 0.91,
      "search_volume": 3400,         # int or null
      "clicks_at_risk": 58,          # int or null  (CTR(best) × volume × fragmentation)
      "value_at_risk": 210.0,        # float or null (clicks_at_risk × CPC) — drives ordering
      "verdict": "strong candidate", # strong candidate | investigate | harmless overlap
      "n_pages": 2,                  # distinct domain pages competing over time
      "rotating": true,              # Google swaps which page ranks across snapshots
      "best_pos": 8,                 # best position any competing page reached
      "n_snapshots": 4,              # SERP snapshots unioned (live + historical)
      "urls": [                      # EVERY same-domain URL seen (union over time)
        {"url": "https://acme.com/shop/trail", "position": 8,  "type": "commercial"},
        {"url": "https://acme.com/products/x", "position": 12, "type": "commercial"}
      ],
      "reason": "Both in the top 15 (#8 and #12) on a commercial query -- two product pages splitting authority.",
      "recommendation": "Consolidate: merge /products/x (#12) into /shop/trail (#8) and 301-redirect it."
    }
  ]
}
"""

import sys, os, json

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonts ─────────────────────────────────────────────────────────────────────
# Prefer the bundled DejaVu TTFs (full Unicode — needed for non-Latin SERPs). If they
# are missing for any reason, fall back to built-in Helvetica registered under the same
# names so the report still renders (Latin only) instead of crashing.
_FONTS = os.path.join(os.path.dirname(__file__), "fonts")

def _register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("DejaVu",         os.path.join(_FONTS, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold",    os.path.join(_FONTS, "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Oblique", os.path.join(_FONTS, "DejaVuSans-Oblique.ttf")))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique")
    except Exception as e:
        from reportlab.pdfbase.pdfmetrics import Font
        pdfmetrics.registerFont(Font("DejaVu",         "Helvetica",         "WinAnsiEncoding"))
        pdfmetrics.registerFont(Font("DejaVu-Bold",    "Helvetica-Bold",    "WinAnsiEncoding"))
        pdfmetrics.registerFont(Font("DejaVu-Oblique", "Helvetica-Oblique", "WinAnsiEncoding"))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique")
        sys.stderr.write(f"[build_report] DejaVu fonts unavailable ({e}); using Helvetica fallback.\n")

_register_fonts()

PW, PH = A4
MARGIN = 18 * mm
CONTENT_W = PW - 2 * MARGIN

T = {
    "primary": HexColor("#1F2937"),
    "accent":  HexColor("#2563EB"),
    "danger":  HexColor("#DC2626"),   # strong candidate
    "warn":    HexColor("#D97706"),   # investigate
    "success": HexColor("#16A34A"),   # harmless / clean
    "bg":      HexColor("#F3F4F6"),
    "muted":   HexColor("#6B7280"),
    "grid":    HexColor("#E5E7EB"),
}

VERDICT_COLOR = {
    "strong candidate": T["danger"],
    "investigate":      T["warn"],
    "harmless overlap": T["success"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_vol(v):
    if v is None:
        return "n/a"
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return str(v)

def fmt_money(v):
    if v is None:
        return "n/a"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if v >= 1:
        return f"${v:,.0f}"
    return f"${v:,.2f}"

def short_url(u, maxlen=58):
    """Strip scheme+host for compact display, keep the path (where page identity lives)."""
    s = u or ""
    for pre in ("https://", "http://"):
        if s.startswith(pre):
            s = s[len(pre):]
    if len(s) > maxlen:
        s = s[:maxlen - 1] + "…"
    return s

def cell(val, bold=False, color=None, size=8, align="LEFT", italic=False):
    if isinstance(val, Paragraph):
        return val
    txt = str(val) if val is not None else "n/a"
    font = "DejaVu-Bold" if bold else ("DejaVu-Oblique" if italic else "DejaVu")
    amap = {"LEFT": 0, "CENTER": 1, "RIGHT": 2}
    return Paragraph(txt, ParagraphStyle(
        "tc", fontName=font, fontSize=size, textColor=color or T["primary"],
        leading=size * 1.35, alignment=amap.get(align, 0), wordWrap="LTR",
    ))

def hcell(val, size=8):
    return cell(val, bold=True, color=colors.white, size=size, align="CENTER")

def styles():
    return {
        "h2":   ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=13,
                               textColor=T["primary"], spaceAfter=3*mm, leading=16),
        "h3":   ParagraphStyle("h3", fontName="DejaVu-Bold", fontSize=10.5,
                               textColor=T["accent"], spaceAfter=2*mm, leading=13),
        "body": ParagraphStyle("body", fontName="DejaVu", fontSize=9,
                               textColor=T["primary"], leading=13, spaceAfter=2*mm),
        "muted":ParagraphStyle("muted", fontName="DejaVu", fontSize=8,
                               textColor=T["muted"], leading=11),
    }

def std_table(headers, rows, ratios, header_bg=None):
    cw = [CONTENT_W * r for r in ratios]
    data = [[hcell(h) for h in headers]] + rows
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  header_bg or T["primary"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, T["bg"]]),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("GRID",           (0, 0), (-1, -1), 0.3, T["grid"]),
        ("TOPPADDING",     (0, 0), (-1, -1), 1.8*mm),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 1.8*mm),
        ("LEFTPADDING",    (0, 0), (-1, -1), 1.8*mm),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 1.8*mm),
    ]))
    return t

def kpi_row(items):
    """items: list of (label, value, color). Renders a row of stat cards."""
    cells = []
    for label, value, color in items:
        inner = Table(
            [[cell(str(value), bold=True, color=color, size=18, align="CENTER")],
             [cell(label.upper(), color=T["muted"], size=7, align="CENTER")]],
            colWidths=[CONTENT_W / len(items) - 3*mm])
        inner.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), T["bg"]),
            ("TOPPADDING",   (0, 0), (-1, 0), 3*mm),
            ("BOTTOMPADDING",(0, 1), (-1, 1), 3*mm),
            ("LINEBEFORE",   (0, 0), (0, -1), 2.5, color),
        ]))
        cells.append(inner)
    wrap = Table([cells], colWidths=[CONTENT_W / len(items)] * len(items))
    wrap.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 1.5*mm),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 1.5*mm)]))
    return wrap


# ── Page furniture (header band + footer) ──────────────────────────────────────

def make_chrome(meta):
    title = f"{meta.get('domain', '')}".upper()
    subtitle = f"{meta.get('location','')} · {meta.get('language','')} · {meta.get('date','')}"

    def draw(canvas, doc):
        canvas.saveState()
        # top band
        canvas.setFillColor(T["primary"])
        canvas.rect(0, PH - 13*mm, PW, 13*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("DejaVu-Bold", 9)
        canvas.drawString(MARGIN, PH - 8.5*mm, "KEYWORD CANNIBALIZATION")
        canvas.setFont("DejaVu", 8)
        canvas.drawRightString(PW - MARGIN, PH - 8.5*mm, title)
        # footer
        canvas.setFillColor(T["muted"])
        canvas.setFont("DejaVu", 7.5)
        canvas.drawString(MARGIN, 8*mm, "Data: DataForSEO")
        canvas.drawCentredString(PW / 2, 8*mm, subtitle)
        canvas.drawRightString(PW - MARGIN, 8*mm, f"Page {doc.page}")
        canvas.setStrokeColor(T["grid"])
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 11*mm, PW - MARGIN, 11*mm)
        canvas.restoreState()

    return draw


# ── Sections ───────────────────────────────────────────────────────────────────

def build_summary(story, s, summary, meta):
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Summary", s["h2"]))
    story.append(kpi_row([
        ("Keywords checked", summary.get("checked", 0), T["accent"]),
        ("Clean (1 page)",   summary.get("clean", 0),   T["success"]),
        ("Had 2+ URLs",      summary.get("candidates", 0), T["primary"]),
    ]))
    story.append(Spacer(1, 3*mm))
    story.append(kpi_row([
        ("Strong candidate", summary.get("strong", 0),      T["danger"]),
        ("Investigate",      summary.get("investigate", 0), T["warn"]),
        ("Harmless overlap", summary.get("harmless", 0),    T["success"]),
    ]))
    story.append(Spacer(1, 4*mm))
    if meta.get("intent_lang_fallback"):
        story.append(Paragraph(
            "Note: search-intent data was computed in English (the run language is not "
            "supported by the intent endpoint).", s["muted"]))
        story.append(Spacer(1, 2*mm))


def build_priority_table(story, s, flagged):
    story.append(Paragraph("Conflicts by priority", s["h3"]))
    story.append(Paragraph(
        "Costliest conflicts first — ranked by estimated value at risk (leaked clicks × CPC), "
        "not raw volume. Full detail for each flagged keyword follows.", s["muted"]))
    story.append(Spacer(1, 2*mm))
    rows = []
    for f in flagged:
        urls = sorted(f.get("urls", []), key=lambda u: u.get("position", 999))
        pos_txt = " / ".join(f"#{u['position']}" for u in urls[:3])
        if len(urls) > 3:
            pos_txt += " …"
        vc = VERDICT_COLOR.get(f.get("verdict", ""), T["primary"])
        rows.append([
            cell(f.get("priority_rank", ""), align="CENTER", size=8),
            cell(f.get("keyword", ""), size=8),
            cell(f.get("intent", ""), align="CENTER", size=7.5),
            cell(fmt_vol(f.get("search_volume")), align="RIGHT", size=8),
            cell(fmt_money(f.get("value_at_risk")), align="RIGHT", size=8),
            cell(pos_txt, align="CENTER", size=8),
            cell(f.get("verdict", ""), bold=True, color=vc, align="CENTER", size=7.5),
        ])
    story.append(std_table(
        ["#", "Keyword", "Intent", "Vol", "Val/mo", "Positions", "Verdict"],
        rows, [0.05, 0.28, 0.12, 0.09, 0.11, 0.16, 0.19]))
    story.append(Spacer(1, 4*mm))


def build_detail(story, s, f):
    vc = VERDICT_COLOR.get(f.get("verdict", ""), T["primary"])
    blocks = []
    # heading
    blocks.append(Paragraph(
        f'#{f.get("priority_rank","")} &nbsp; {f.get("keyword","")}', s["h3"]))
    rot = "rotating" if f.get("rotating") else "co-listed"
    meta_line = (f'Intent: <b>{f.get("intent","")}</b> '
                 f'({int(round((f.get("intent_probability") or 0)*100))}% prob) · '
                 f'Volume: <b>{fmt_vol(f.get("search_volume"))}</b> · '
                 f'Pages: <b>{f.get("n_pages","")}</b> ({rot}, {f.get("n_snapshots","")} snapshots) · '
                 f'Best: <b>#{f.get("best_pos","")}</b> · '
                 f'Clicks at risk: <b>{fmt_vol(f.get("clicks_at_risk"))}/mo</b> · '
                 f'Value: <b>{fmt_money(f.get("value_at_risk"))}/mo</b> · '
                 f'Priority: <b>{f.get("priority_score","")}</b>')
    blocks.append(Paragraph(meta_line, s["muted"]))
    blocks.append(Spacer(1, 2*mm))
    # every same-domain URL
    urls = sorted(f.get("urls", []), key=lambda u: u.get("position", 999))
    url_rows = []
    for u in urls:
        tcolor = T["accent"] if str(u.get("type", "")).startswith("commercial") else T["muted"]
        url_rows.append([
            cell(f"#{u.get('position','')}", align="CENTER", bold=True, size=8),
            cell(short_url(u.get("url", "")), size=7.5),
            cell(u.get("type", ""), align="CENTER", color=tcolor, size=7.5),
        ])
    blocks.append(std_table(
        ["Pos", "Same-domain URL", "Page type"], url_rows,
        [0.10, 0.68, 0.22], header_bg=T["accent"]))
    blocks.append(Spacer(1, 2*mm))
    # verdict + reason + fix box
    verdict_para = Paragraph(
        f'<b>Verdict:</b> <font color="#{vc.hexval()[2:]}">'
        f'{f.get("verdict","").upper()}</font>', s["body"])
    reason_para = Paragraph(f'<b>Why:</b> {f.get("reason","")}', s["body"])
    fix_para = Paragraph(f'<b>Recommended fix:</b> {f.get("recommendation","")}', s["body"])
    box = Table([[verdict_para], [reason_para], [fix_para]], colWidths=[CONTENT_W])
    box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), HexColor("#F9FAFB")),
        ("LINEBEFORE",   (0, 0), (0, -1), 3, vc),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4*mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3*mm),
        ("TOPPADDING",   (0, 0), (-1, -1), 1*mm),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 1*mm),
    ]))
    blocks.append(box)
    blocks.append(Spacer(1, 5*mm))
    story.append(KeepTogether(blocks))


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_report.py <path_to_data.json>")
        sys.exit(1)
    data_path = sys.argv[1]
    with open(data_path, "r", encoding="utf-8-sig") as fh:  # utf-8-sig tolerates a BOM
        data = json.load(fh)

    meta = data.get("meta", {})
    summary = data.get("summary", {})
    flagged = data.get("flagged", [])

    out_path = meta.get("out_path")
    if not out_path:
        domain = meta.get("domain", "report").replace("/", "_")
        date = meta.get("date", "").replace("-", "")
        out_path = os.path.join(os.path.dirname(os.path.abspath(data_path)),
                                f"{domain}_cannibalization_{date}.pdf")

    s = styles()
    story = []
    build_summary(story, s, summary, meta)

    detailed = [f for f in flagged if f.get("verdict") != "harmless overlap"]
    if flagged:
        build_priority_table(story, s, flagged)
    if detailed:
        story.append(PageBreak())
        story.append(Paragraph("Flagged keywords — detail", s["h2"]))
        story.append(Paragraph(
            "One section per keyword that warrants action (strong candidate or "
            "investigate). Harmless co-ranking is excluded here and counted in the "
            "summary above.", s["muted"]))
        story.append(Spacer(1, 3*mm))
        for f in detailed:
            build_detail(story, s, f)
    elif not flagged:
        story.append(Paragraph(
            "No keyword returned 2 or more URLs from this domain in the top 100 — no "
            "cannibalization candidates. That is a healthy sign.", s["body"]))

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=18*mm, bottomMargin=15*mm,
        title=f"Keyword Cannibalization — {meta.get('domain','')}",
    )
    chrome = make_chrome(meta)
    doc.build(story, onFirstPage=chrome, onLaterPages=chrome)
    print(out_path)


if __name__ == "__main__":
    main()
