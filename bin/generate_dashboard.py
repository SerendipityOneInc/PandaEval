#!/usr/bin/env python3
"""Parse skill-card markdown files and generate a static dashboard site."""

import json
import math
import os
import re
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT_DIR / "results" / "skill-cards"
DOCS_DIR = ROOT_DIR / "docs"


def parse_skill_card(filepath: str) -> dict | None:
    """Parse a single skill card markdown file into a dict."""
    text = Path(filepath).read_text(encoding="utf-8")

    if text.startswith("# Skill Card: {skill_name}"):
        return None

    json_match = re.search(r"```json\s*\n({.*?})\s*\n```", text, re.DOTALL)
    data = {}
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    name_matches = re.findall(r"^# Skill Card: (.+)$", text, re.MULTILINE)
    for nm in name_matches:
        nm = nm.strip()
        if "DEPENDENCY-GATED" not in nm and "{skill_name}" not in nm:
            data.setdefault("name", nm)
            break

    desc_match = re.search(r"^> (.+)$", text, re.MULTILINE)
    if desc_match:
        data["description"] = desc_match.group(1).strip()

    for field, key in [
        ("Domain", "domain"), ("Type", "type"), ("Eval Date", "eval_date"),
        ("Eval Engine", "eval_engine"), ("Eval Model", "eval_model"),
        ("Downloads", "downloads"), ("Source", "source_url"),
    ]:
        m = re.search(rf"\*\*{field}\*\*\s*\|\s*(.+)", text)
        if m:
            val = m.group(1).strip().rstrip("|").strip()
            if key == "source_url":
                link = re.search(r"\[.*?\]\((.*?)\)", val)
                if link:
                    val = link.group(1)
            elif key == "downloads":
                val = int(re.sub(r"[^\d]", "", val.split("|")[0]))
            data.setdefault(key, val)

    score_match = re.search(r"Overall Score:\s*([\d.]+)/10", text)
    if score_match:
        data.setdefault("score", float(score_match.group(1)))

    verdict_match = re.search(r"\*\*Verdict:\*\*\s*(.+)", text)
    if verdict_match:
        data["verdict"] = verdict_match.group(1).strip()

    flags_match = re.search(r"\*\*Flags:\*\*\s*(.+)", text)
    if flags_match:
        flags_raw = flags_match.group(1).strip()
        data.setdefault("flags", [f.strip().strip("`") for f in flags_raw.split(",") if f.strip()])

    breakdown = {}
    for row in re.finditer(
        r"\|\s*(\w[\w\s-]*?)\s*\|\s*([\d.]+)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|",
        text,
    ):
        component = row.group(1).strip()
        if component.lower() in ("total", "**total**", "component"):
            continue
        breakdown[component.lower()] = {
            "score": float(row.group(2)),
            "max": float(row.group(3)),
            "desc": row.group(4).strip(),
        }
    if breakdown:
        data["breakdown"] = breakdown

    metrics = {}
    for m in re.finditer(r"\*\*([\w\s]+):\*\*\s*(.+)", text):
        key = m.group(1).strip()
        val = m.group(2).strip()
        if key in ("Word Count", "Line Count", "Files in Package"):
            metrics[key.lower().replace(" ", "_")] = int(val)
        elif key in ("Has Scripts", "Has References"):
            metrics[key.lower().replace(" ", "_")] = val.lower() == "yes"
    if metrics:
        data["metrics"] = metrics

    data["filename"] = os.path.basename(filepath)

    if "score" not in data or "name" not in data:
        return None

    return data


# ─── Helpers ───

FLAG_LABELS = {
    "dependency-gated": "requires-credentials",
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def sc_class(score: float) -> str:
    if score >= 8: return "high"
    if score >= 6: return "mid"
    if score >= 4: return "low"
    return "bad"


def vc_class(verdict: str) -> str:
    v = verdict.lower()
    if "highly" in v: return "green"
    if "recommend" in v: return "blue"
    if "caution" in v or "conditional" in v: return "yellow"
    if "not" in v or "marginal" in v: return "red"
    return "blue"


def slug_for(skill: dict) -> str:
    return skill.get("slug", skill["name"].lower().replace(" ", "-").replace("/", "-"))


def fmt_downloads(n) -> str:
    if isinstance(n, str):
        n = int(n.replace(",", ""))
    if n >= 1000:
        return f"{n/1000:.1f}k".replace(".0k", "k")
    return str(n) if n else ""


# ─── Score Ring SVG (circular arc for cards) ───

def build_score_ring(score, max_val=10, size=48, sw=3.5):
    r = (size - sw * 2) / 2
    cx = cy = size / 2
    circ = 2 * math.pi * r
    pct = min(score / max_val, 1.0)
    dash = circ * pct
    gap = circ - dash
    sc = sc_class(score)
    colors = {"high": "var(--green)", "mid": "var(--yellow)", "low": "var(--red)", "bad": "var(--red)"}
    color = colors[sc]
    trail_color = "var(--ring-trail)"
    return (
        f'<div class="score-ring">'
        f'<svg class="score-ring-svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" stroke="{trail_color}" stroke-width="{sw}" fill="none"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" stroke="{color}" stroke-width="{sw}" fill="none" '
        f'stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-linecap="round" '
        f'transform="rotate(-90 {cx} {cy})"/>'
        f'</svg>'
        f'<span class="score-ring-val">{score}</span>'
        f'</div>'
    )


# ─── Radar SVG (detail page only) ───

RADAR_DIMS = ["structure", "specificity", "examples", "scope", "actionability"]
RADAR_LABELS_FULL = ["Structure", "Specificity", "Examples", "Scope", "Actionability"]
R_CX, R_CY, R_R = 50, 50, 38
R_LABEL_R = 46


def _pent_pt(i, r, cx=R_CX, cy=R_CY):
    a = -math.pi / 2 + 2 * math.pi * i / 5
    return cx + r * math.cos(a), cy + r * math.sin(a)


def _pent_str(r):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (_pent_pt(i, r) for i in range(5)))


def build_radar_svg(breakdown: dict) -> str:
    grid = f'<polygon points="{_pent_str(R_R)}" class="radar-grid"/>'
    grid += f'<polygon points="{_pent_str(R_R * 0.5)}" class="radar-grid"/>'
    axes = ""
    for i in range(5):
        px, py = _pent_pt(i, R_R)
        axes += f'<line x1="{R_CX}" y1="{R_CY}" x2="{px:.1f}" y2="{py:.1f}" class="radar-axis"/>'
    pts, dots = [], ""
    for i, dim in enumerate(RADAR_DIMS):
        bd = breakdown.get(dim, {"score": 0, "max": 2})
        pct = bd["score"] / bd["max"] if bd["max"] else 0
        r = max(pct * R_R, 2)
        px, py = _pent_pt(i, r)
        pts.append(f"{px:.1f},{py:.1f}")
        dots += f'<circle cx="{px:.1f}" cy="{py:.1f}" class="radar-dot"/>'
    fill = f'<polygon points="{" ".join(pts)}" class="radar-fill"/>'
    labels = ""
    for i, label in enumerate(RADAR_LABELS_FULL):
        lx, ly = _pent_pt(i, R_LABEL_R)
        labels += f'<text x="{lx:.1f}" y="{ly:.1f}" class="radar-label">{label}</text>'
    return f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">{grid}{axes}{fill}{dots}{labels}</svg>'


# ─── Compact score bar for cards (5 segments) ───

def build_card_bar_html(breakdown: dict) -> str:
    segs = ""
    for dim in RADAR_DIMS:
        bd = breakdown.get(dim, {"score": 0, "max": 2})
        pct = bd["score"] / bd["max"] if bd["max"] else 0
        if pct >= 0.9:
            cls = "full"
        elif pct >= 0.5:
            cls = "half"
        elif pct > 0:
            cls = "low"
        else:
            cls = "zero"
        mx = bd["max"]
        sc_v = bd["score"]
        segs += f'<div class="card-bar-seg {cls}" style="flex:{mx}" title="{dim}: {sc_v:g}/{mx:g}"></div>'
    return segs


# ─── Score Distribution Chart ───

def build_score_distribution(skills):
    bins = [0] * 5
    labels = ["0-2", "2-4", "4-6", "6-8", "8-10"]
    colors = ["#f87171", "#fb923c", "#fbbf24", "#60a5fa", "#34d399"]
    for s in skills:
        score = s.get("score", 0)
        idx = min(int(score / 2), 4)
        bins[idx] += 1
    max_bin = max(bins) or 1

    bars_html = ""
    for i, (count, label) in enumerate(zip(bins, labels)):
        h = count / max_bin * 100
        bars_html += (
            f'<div class="dist-bar-group">'
            f'<span class="dist-bar-count">{count}</span>'
            f'<div class="dist-bar-wrap"><div class="dist-bar" style="height:{h:.0f}%;background:{colors[i]}"></div></div>'
            f'<span class="dist-bar-label">{label}</span>'
            f'</div>'
        )
    return bars_html


# ─── Card HTML ───

def build_card_html(skill: dict) -> str:
    s = skill
    slug = slug_for(s)
    score = s.get("score", 0)
    name = esc(s["name"])
    domain = s.get("domain", "") or s.get("eval_engine", "")
    verdict = s.get("verdict", "")
    vc = vc_class(verdict)
    desc = esc(s.get("description", ""))
    dl = s.get("downloads", 0)
    if isinstance(dl, str): dl = int(dl.replace(",", ""))
    dl_str = fmt_downloads(dl)
    skill_type = s.get("type", "").replace("_", " ")
    breakdown = s.get("breakdown", {})

    flags_html = ""
    for f in s.get("flags", []):
        label = FLAG_LABELS.get(f, f)
        cls = f"flag-tag flag-tag--{label}" if label in FLAG_LABELS.values() else "flag-tag"
        flags_html += f'<span class="{cls}">{esc(label)}</span>'

    bar_html = build_card_bar_html(breakdown)
    ring_html = build_score_ring(score)

    meta_parts = f'<span class="card-domain">{esc(domain)}</span>'
    if dl_str:
        meta_parts += f'<span class="card-dl">{dl_str}</span>'

    return f'''<div class="card" data-domain="{esc(domain)}" data-verdict="{vc}" data-score="{score}" data-name="{name.lower()}" data-downloads="{dl}" onclick="location.href='detail/{slug}.html'">
    <div class="card-header">
        <div class="card-title-group">
            <div class="card-title">{name}</div>
            <div class="card-meta">{meta_parts}</div>
        </div>
        {ring_html}
    </div>
    <div class="card-desc">{desc}</div>
    <div class="card-bars">{bar_html}</div>
    <div class="card-footer">
        <div style="display:flex;gap:0.3rem;align-items:center">
            <span class="verdict-tag vt-{vc}">{esc(verdict)}</span>
            <div class="flag-tags">{flags_html}</div>
        </div>
        <span class="card-type-label">{esc(skill_type)}</span>
    </div>
</div>'''


# ─── Detail HTML ───

def build_detail_html(skill: dict) -> str:
    s = skill
    score = s.get("score", 0)
    sc = sc_class(score)
    name = esc(s["name"])
    domain = esc(s.get("domain", "unknown"))
    skill_type = s.get("type", "").replace("_", " ").title()
    verdict = s.get("verdict", "")
    vc = vc_class(verdict)
    desc = esc(s.get("description", ""))
    dl = s.get("downloads", 0)
    if isinstance(dl, str): dl = int(dl.replace(",", ""))
    dl_str = f"{dl:,}" if dl else "—"
    eval_date = s.get("eval_date", "")
    eval_engine = esc(s.get("eval_engine", ""))
    source_url = esc(s.get("source_url", "#"))

    tags_html = ""
    for f in s.get("flags", []):
        label = FLAG_LABELS.get(f, f)
        cls = f"flag-tag flag-tag--{label}" if label in FLAG_LABELS.values() else "flag-tag"
        tags_html += f'<span class="{cls}">{esc(label)}</span>'
    tags_html += f'<span class="verdict-tag vt-{vc}">{esc(verdict)}</span>'

    breakdown = s.get("breakdown", {})
    radar_svg = build_radar_svg(breakdown)

    bd_html = ""
    for comp, bd in sorted(breakdown.items()):
        pct = bd["score"] / bd["max"] * 100 if bd["max"] else 0
        desc_text = esc(bd.get("desc", ""))
        tooltip = f' data-tip="{desc_text}"' if desc_text else ""
        bd_html += f'''<div class="detail-score-item has-tip"{tooltip}>
            <span class="ds-label">{comp}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
            <span class="ds-val">{bd["score"]:g}/{bd["max"]:g}</span>
        </div>'''

    metrics = s.get("metrics", {})
    metrics_html = ""
    for k, v in metrics.items():
        label = k.replace("_", " ").title()
        if isinstance(v, bool): v = "Yes" if v else "No"
        metrics_html += f'''<div class="metric-item">
            <span class="metric-label">{label}</span>
            <span class="metric-val">{v}</span>
        </div>'''

    sc_colors = {"high": "var(--green)", "mid": "var(--yellow)", "low": "var(--red)", "bad": "var(--red)"}
    sc_bgs = {"high": "var(--green-dim)", "mid": "var(--yellow-dim)", "low": "var(--red-dim)", "bad": "var(--red-dim)"}

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — PandaEval</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="container detail-page">
    <button class="theme-toggle" id="theme-toggle" title="Toggle theme">
        <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
    <a href="../index.html" class="back-btn">&larr; Back</a>

    <div class="detail-header">
        <div class="detail-top">
            <div class="detail-info">
                <h1>{name}</h1>
                <div class="detail-meta">
                    <span class="detail-domain">{domain}</span>
                    <span class="detail-meta-item">{eval_date}</span>
                    <span class="detail-meta-item">{dl_str} downloads</span>
                    <span class="detail-meta-item">{skill_type}</span>
                </div>
                <p class="detail-desc">{desc}</p>
                <div class="detail-tags">{tags_html}</div>
            </div>
            <div class="detail-score" style="background:{sc_bgs[sc]};color:{sc_colors[sc]}">
                <span class="detail-score-num">{score}</span>
                <span class="detail-score-den">/10</span>
            </div>
        </div>
    </div>

    <section class="detail-section">
        <h2 class="section-title">Evaluation Breakdown</h2>
        <div class="detail-radar-section">
            <div class="detail-radar">{radar_svg}</div>
            <div class="detail-scores-list">{bd_html}</div>
        </div>
    </section>

    <section class="detail-section">
        <h2 class="section-title">Metrics</h2>
        <div class="metrics-grid">{metrics_html}</div>
    </section>

    <section class="detail-section">
        <h2 class="section-title">Source</h2>
        <a href="{source_url}" class="source-link" target="_blank">{source_url}</a>
        <p class="eval-engine">{eval_engine}</p>
    </section>
</div>
<script src="../app.js"></script>
</body>
</html>'''


# ─── Index HTML ───

def build_index_html(skills, domains, verdicts):
    total = len(skills)
    avg = sum(s["score"] for s in skills) / total if total else 0
    n_domains = len(domains)

    vc_counts = Counter(vc_class(s.get("verdict", "")) for s in skills)
    n_green = vc_counts.get("green", 0)
    n_blue = vc_counts.get("blue", 0)
    n_yellow = vc_counts.get("yellow", 0)
    n_red = vc_counts.get("red", 0)

    dist_html = build_score_distribution(skills)

    cards_html = "\n".join(build_card_html(s) for s in skills)

    domain_pills = '<button class="domain-pill active" data-filter="all" data-group="domain">All</button>'
    for d in sorted(domains):
        domain_pills += f'<button class="domain-pill" data-filter="{d}" data-group="domain">{d}</button>'

    verdict_pills = '<button class="pill active" data-filter="all" data-group="verdict">All</button>'
    for label, vc, color in [
        ("Highly Rec.", "green", "var(--green)"),
        ("Recommended", "blue", "var(--blue)"),
        ("Conditional", "yellow", "var(--yellow)"),
        ("Marginal", "red", "var(--red)"),
    ]:
        verdict_pills += f'<button class="pill" data-filter="{vc}" data-group="verdict"><span class="pill-dot" style="background:{color}"></span>{label}</button>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PandaEval — Skill Evaluation Dashboard</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">

    <div class="ambient-glow"></div>

    <button class="theme-toggle" id="theme-toggle" title="Toggle theme">
        <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>

    <div class="header">
        <div class="logo">
            <span class="logo-icon">&#x1f43c;</span>
            <span class="logo-text">PandaEval</span>
        </div>
        <span class="header-meta">skill-eval &middot; {total} skills &middot; {n_domains} domains</span>
    </div>

    <div class="hero-stats">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-card-label">Total Skills</div>
                <div class="stat-card-row">
                    <span class="stat-card-num">{total}</span>
                    <span class="stat-card-extra">evaluated</span>
                </div>
                <div class="stat-card-bar">
                    <div class="vb-green" style="flex:{n_green}"></div>
                    <div class="vb-blue" style="flex:{n_blue}"></div>
                    <div class="vb-yellow" style="flex:{n_yellow}"></div>
                    <div class="vb-red" style="flex:{max(n_red, 1)}"></div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">Avg Score</div>
                <div class="stat-card-row">
                    <span class="stat-card-num">{avg:.1f}</span>
                    <span class="stat-card-extra">out of 10</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">Recommended</div>
                <div class="stat-card-row">
                    <span class="stat-card-num">{n_green + n_blue}</span>
                    <span class="stat-card-extra">{(n_green + n_blue) * 100 // max(total, 1)}% pass rate</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">Domains</div>
                <div class="stat-card-row">
                    <span class="stat-card-num">{n_domains}</span>
                    <span class="stat-card-extra">categories</span>
                </div>
            </div>
        </div>
        <div class="dist-card">
            <div class="dist-card-label">Score Distribution</div>
            <div class="dist-chart">{dist_html}</div>
        </div>
    </div>

    <div class="toolbar">
        <div class="search-box">
            <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            <input type="text" id="search" placeholder="Search skills...">
            <span class="results-count" id="results-count"></span>
            <span class="search-kbd">/</span>
        </div>
        <div class="pill-group">{verdict_pills}</div>
        <select class="sort-select" id="sort-select">
            <option value="score-desc">Score &darr;</option>
            <option value="score-asc">Score &uarr;</option>
            <option value="name-asc">Name A-Z</option>
            <option value="name-desc">Name Z-A</option>
            <option value="downloads-desc">Downloads &darr;</option>
        </select>
        <div class="view-toggle">
            <button class="view-btn active" data-view="grid" title="Grid">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
            </button>
            <button class="view-btn" data-view="list" title="List">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="2" width="14" height="2.5" rx="1"/><rect x="1" y="6.75" width="14" height="2.5" rx="1"/><rect x="1" y="11.5" width="14" height="2.5" rx="1"/></svg>
            </button>
        </div>
    </div>

    <div class="domain-row">{domain_pills}</div>

    <div class="cards-grid" id="cards-container">
{cards_html}
    </div>

    <footer class="footer">
        PandaEval &middot; {total} skill evaluations &middot; {n_domains} domains
    </footer>
</div>
<script src="app.js"></script>
</body>
</html>'''


def main():
    cards_path = CARDS_DIR
    print(f"Cards dir: {cards_path} (exists: {cards_path.exists()})")
    md_files = sorted(cards_path.glob("*.md"))
    print(f"Found {len(md_files)} .md files")

    skills = []
    skipped = 0
    for f in md_files:
        if f.name == "TEMPLATE.md":
            continue
        if "-v0.3.0.md" in f.name:
            skipped += 1
            continue
        s = parse_skill_card(str(f))
        if s:
            skills.append(s)
        else:
            skipped += 1

    name_count = Counter(s.get("name", "") for s in skills)
    for s in skills:
        if name_count[s.get("name", "")] > 1 and s.get("slug"):
            s["name"] = f"{s['name']} ({s['slug']})"

    skills.sort(key=lambda x: x.get("score", 0), reverse=True)
    domains = sorted(set(s.get("domain", "unknown") for s in skills))
    verdicts = sorted(set(s.get("verdict", "") for s in skills))

    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "detail").mkdir(exist_ok=True)

    index_html = build_index_html(skills, domains, verdicts)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")

    for s in skills:
        slug = slug_for(s)
        detail_html = build_detail_html(s)
        (DOCS_DIR / "detail" / f"{slug}.html").write_text(detail_html, encoding="utf-8")

    print(f"Generated dashboard: {len(skills)} skills, {skipped} skipped, {len(domains)} domains")
    print(f"Output: {DOCS_DIR}")


if __name__ == "__main__":
    main()
