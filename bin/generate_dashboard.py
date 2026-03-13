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
        return None  # template

    # Try to extract JSON block first (most reliable)
    json_match = re.search(r"```json\s*\n({.*?})\s*\n```", text, re.DOTALL)
    data = {}
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Extract name from title (skip DEPENDENCY-GATED headers, use last real name)
    name_matches = re.findall(r"^# Skill Card: (.+)$", text, re.MULTILINE)
    for nm in name_matches:
        nm = nm.strip()
        if "DEPENDENCY-GATED" not in nm and "{skill_name}" not in nm:
            data.setdefault("name", nm)
            break

    # Extract description
    desc_match = re.search(r"^> (.+)$", text, re.MULTILINE)
    if desc_match:
        data["description"] = desc_match.group(1).strip()

    # Extract table fields
    for field, key in [
        ("Domain", "domain"),
        ("Type", "type"),
        ("Eval Date", "eval_date"),
        ("Eval Engine", "eval_engine"),
        ("Eval Model", "eval_model"),
        ("Downloads", "downloads"),
        ("Source", "source_url"),
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

    # Extract overall score
    score_match = re.search(r"Overall Score:\s*([\d.]+)/10", text)
    if score_match:
        data.setdefault("score", float(score_match.group(1)))

    # Extract verdict
    verdict_match = re.search(r"\*\*Verdict:\*\*\s*(.+)", text)
    if verdict_match:
        data["verdict"] = verdict_match.group(1).strip()

    # Extract flags
    flags_match = re.search(r"\*\*Flags:\*\*\s*(.+)", text)
    if flags_match:
        flags_raw = flags_match.group(1).strip()
        data.setdefault("flags", [f.strip().strip("`") for f in flags_raw.split(",") if f.strip()])

    # Extract score breakdown (score and max)
    breakdown = {}
    for row in re.finditer(
        r"\|\s*(\w[\w\s-]*?)\s*\|\s*([\d.]+)\s*\|\s*(\d+)\s*\|",
        text,
    ):
        component = row.group(1).strip()
        if component.lower() in ("total", "**total**", "component"):
            continue
        breakdown[component.lower()] = {
            "score": float(row.group(2)),
            "max": float(row.group(3)),
        }
    if breakdown:
        data["breakdown"] = breakdown

    # Extract metrics
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


def score_color_class(score: float) -> str:
    if score >= 8:
        return "high"
    elif score >= 6:
        return "mid"
    elif score >= 4:
        return "low"
    return "bad"


def verdict_badge_class(verdict: str) -> str:
    v = verdict.lower()
    if "highly" in v:
        return "green"
    elif "recommend" in v:
        return "blue"
    elif "caution" in v or "conditional" in v:
        return "yellow"
    elif "not" in v:
        return "red"
    return "gray"


def generate_detail_slug(skill: dict) -> str:
    return skill.get("slug", skill["name"].lower().replace(" ", "-").replace("/", "-"))


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# Pentagon radar chart dimensions
RADAR_DIMS = ["structure", "specificity", "examples", "scope", "actionability"]
RADAR_LABELS = ["Struct", "Spec", "Exam", "Scope", "Action"]
RADAR_CX, RADAR_CY, RADAR_R = 50, 50, 38
RADAR_LABEL_R = 46


def _pentagon_point(i: int, r: float, cx: float = RADAR_CX, cy: float = RADAR_CY) -> tuple[float, float]:
    angle = -math.pi / 2 + 2 * math.pi * i / 5
    return cx + r * math.cos(angle), cy + r * math.sin(angle)


def _pentagon_points_str(r: float) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (_pentagon_point(i, r) for i in range(5)))


def build_radar_svg(breakdown: dict) -> str:
    """Build a pentagon radar chart SVG for 5 evaluation dimensions."""
    # Grid rings at 50% and 100%
    grid = f'<polygon points="{_pentagon_points_str(RADAR_R)}" class="radar-grid"/>'
    grid += f'<polygon points="{_pentagon_points_str(RADAR_R * 0.5)}" class="radar-grid"/>'

    # Axes
    axes = ""
    for i in range(5):
        px, py = _pentagon_point(i, RADAR_R)
        axes += f'<line x1="{RADAR_CX}" y1="{RADAR_CY}" x2="{px:.1f}" y2="{py:.1f}" class="radar-axis"/>'

    # Data polygon
    data_points = []
    dots = ""
    for i, dim in enumerate(RADAR_DIMS):
        bd = breakdown.get(dim, {"score": 0, "max": 2})
        pct = bd["score"] / bd["max"] if bd["max"] else 0
        r = max(pct * RADAR_R, 2)
        px, py = _pentagon_point(i, r)
        data_points.append(f"{px:.1f},{py:.1f}")
        dots += f'<circle cx="{px:.1f}" cy="{py:.1f}" class="radar-dot"/>'

    fill = f'<polygon points="{" ".join(data_points)}" class="radar-fill"/>'

    # Labels
    labels = ""
    for i, label in enumerate(RADAR_LABELS):
        lx, ly = _pentagon_point(i, RADAR_LABEL_R)
        labels += f'<text x="{lx:.1f}" y="{ly:.1f}" class="radar-label">{label}</text>'

    return f'''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        {grid}{axes}{fill}{dots}{labels}
    </svg>'''


def build_card_html(skill: dict) -> str:
    slug = generate_detail_slug(skill)
    score = skill.get("score", 0)
    sc = score_color_class(score)
    name = html_escape(skill["name"])
    domain = skill.get("domain", "")
    eval_engine = skill.get("eval_engine", "")
    domain_display = domain if domain else eval_engine
    skill_type = skill.get("type", "")
    verdict = skill.get("verdict", "")
    vc = verdict_badge_class(verdict)
    desc = html_escape(skill.get("description", ""))
    downloads = skill.get("downloads", 0)
    if isinstance(downloads, str):
        downloads = int(downloads.replace(",", ""))
    dl_str = f"{downloads:,}" if downloads else ""

    breakdown = skill.get("breakdown", {})

    # Bars for all dimensions
    sorted_bd = sorted(breakdown.items(), key=lambda x: x[1]["score"], reverse=True)
    bars_html = ""
    for comp, bd in sorted_bd:
        pct = bd["score"] / bd["max"] * 100 if bd["max"] else 0
        score_display = f"{bd['score']:g}/{bd['max']:g}"
        bars_html += f'''<div class="bar-row">
                <span class="bar-label">{comp}</span>
                <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
                <span class="bar-val">{score_display}</span>
            </div>'''

    # Radar chart
    radar_svg = build_radar_svg(breakdown)

    flags_html = ""
    for f in skill.get("flags", []):
        flags_html += f'<span class="tag">{html_escape(f)}</span>'
    flags_html += f'<span class="tag tag-verdict tag-{vc}">{html_escape(verdict)}</span>'

    meta_parts = []
    if domain_display:
        meta_parts.append(f'<span class="domain-chip">{html_escape(domain_display)}</span>')
    if dl_str:
        meta_parts.append(f'{dl_str} dl')
    meta_html = '<span class="meta-sep">&middot;</span>'.join(meta_parts)

    type_display = skill_type.replace("_", " ") if skill_type else ""

    return f'''
    <div class="card" data-sc="{sc}" data-domain="{html_escape(domain_display)}" data-verdict="{vc}" data-score="{score}" data-name="{name.lower()}" data-downloads="{downloads}" onclick="location.href='detail/{slug}.html'">
        <div class="card-header">
            <div class="card-title-group">
                <h3 class="card-title">{name}</h3>
                <div class="card-meta">{meta_html}</div>
            </div>
            <div class="score-block" data-sc="{sc}">
                <span class="score-num sc-{sc}">{score}</span>
                <span class="score-den">/10</span>
            </div>
        </div>
        <p class="card-desc">{desc}</p>
        <div class="card-body">
            <div class="radar-wrap">{radar_svg}</div>
            <div class="card-bars">{bars_html}</div>
        </div>
        <div class="card-footer">
            <div class="tags">{flags_html}</div>
            <span class="card-type">{type_display}</span>
        </div>
    </div>'''


def build_detail_html(skill: dict) -> str:
    slug = generate_detail_slug(skill)
    score = skill.get("score", 0)
    sc = score_color_class(score)
    name = html_escape(skill["name"])
    domain = html_escape(skill.get("domain", "unknown"))
    skill_type = skill.get("type", "")
    verdict = skill.get("verdict", "")
    vc = verdict_badge_class(verdict)
    desc = html_escape(skill.get("description", ""))
    downloads = skill.get("downloads", 0)
    if isinstance(downloads, str):
        downloads = int(downloads.replace(",", ""))
    dl_str = f"{downloads:,}" if downloads else "—"
    eval_date = skill.get("eval_date", "")
    eval_engine = html_escape(skill.get("eval_engine", ""))
    source_url = html_escape(skill.get("source_url", "#"))

    flags_html = ""
    for f in skill.get("flags", []):
        flags_html += f'<span class="tag">{html_escape(f)}</span>'
    flags_html += f'<span class="tag tag-verdict tag-{vc}">{html_escape(verdict)}</span>'

    breakdown = skill.get("breakdown", {})
    bd_html = ""
    for comp, bd in sorted(breakdown.items()):
        pct = bd["score"] / bd["max"] * 100 if bd["max"] else 0
        score_display = f"{bd['score']:g}/{bd['max']:g}"
        bd_html += f'''
        <div class="detail-score-item">
            <span class="ds-label">{comp}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
            <span class="ds-val">{score_display}</span>
        </div>'''

    metrics = skill.get("metrics", {})
    metrics_html = ""
    for k, v in metrics.items():
        label = k.replace("_", " ").title()
        if isinstance(v, bool):
            v = "Yes" if v else "No"
        metrics_html += f'''
        <div class="metric-item">
            <span class="metric-label">{label}</span>
            <span class="metric-val">{v}</span>
        </div>'''

    type_display = skill_type.replace("_", " ").title() if skill_type else ""

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
    <a href="../index.html" class="back-btn">&larr; Back</a>
    <div class="detail-header-card">
        <div class="detail-info">
            <h1>{name}</h1>
            <div class="detail-sub">
                <span class="detail-sub-item"><span class="domain-chip">{domain}</span></span>
                <span class="detail-sub-item">{eval_date}</span>
                <span class="detail-sub-item">{dl_str} downloads</span>
                <span class="detail-sub-item">{type_display}</span>
            </div>
            <p class="detail-desc">{desc}</p>
            <div class="tags">{flags_html}</div>
        </div>
        <div class="score-block-lg" data-sc="{sc}">
            <span class="score-num sc-{sc}">{score}</span>
            <span class="score-den">/10</span>
        </div>
    </div>

    <section class="detail-section">
        <h2 class="section-title">Evaluation Scores</h2>
        <div class="detail-scores-grid">{bd_html}</div>
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
</body>
</html>'''


def build_score_distribution(skills: list[dict]) -> str:
    """Build SVG bars for score distribution (4.0 to 10.0, step 0.5)."""
    from collections import defaultdict
    buckets = defaultdict(int)
    for s in skills:
        sc = s.get("score", 0)
        bucket = round(sc * 2) / 2  # snap to 0.5
        buckets[bucket] += 1
    max_count = max(buckets.values()) if buckets else 1
    bars = ""
    for i, v in enumerate(sorted(buckets.keys())):
        h = max(buckets[v] / max_count * 22, 1)
        sc = score_color_class(v)
        color_map = {"high": "var(--sc-high)", "mid": "var(--sc-mid)", "low": "var(--sc-low)", "bad": "var(--sc-bad)"}
        color = color_map.get(sc, "var(--sc-mid)")
        bars += f'<div class="distrib-bar" style="height:{h:.0f}px;background:{color}" title="{v}: {buckets[v]}"></div>'
    return bars


def build_index_html(skills: list[dict], domains: list[str], verdicts: list[str]) -> str:
    total = len(skills)
    avg_score = sum(s["score"] for s in skills) / total if total else 0
    domain_count = len(domains)

    verdict_counts = Counter(verdict_badge_class(s.get("verdict", "")) for s in skills)
    highly_rec = verdict_counts.get("green", 0)
    recommended = verdict_counts.get("blue", 0)
    conditional = verdict_counts.get("yellow", 0)
    marginal = verdict_counts.get("red", 0)

    cards_html = "\n".join(build_card_html(s) for s in skills)
    distrib_html = build_score_distribution(skills)

    domain_btns = '<button class="filter-btn active" data-filter="all" data-group="domain">All</button>'
    for d in sorted(domains):
        domain_btns += f'<button class="filter-btn" data-filter="{d}" data-group="domain">{d}</button>'

    verdict_btns = '<button class="filter-btn active" data-filter="all" data-group="verdict">All</button>'
    for label, vc in [("Highly Rec.", "green"), ("Recommended", "blue"), ("Conditional", "yellow"), ("Marginal", "red")]:
        verdict_btns += f'<button class="filter-btn" data-filter="{vc}" data-group="verdict">{label}</button>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PandaEval &mdash; Skill Evaluation Dashboard</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
    <header class="hero">
        <div class="logo"><span class="logo-panda">&#x1f43c;</span>Panda<span class="logo-accent">Eval</span></div>
        <p class="tagline">Automated Skill Evaluation for AI Agents</p>
    </header>

    <div class="stats-bar">
        <div class="stat">
            <span class="stat-num">{total}</span>
            <span class="stat-label">Skills</span>
        </div>
        <div class="stat">
            <span class="stat-dot stat-dot-green"></span>
            <span class="stat-num">{highly_rec}</span>
            <span class="stat-label">Highly Rec.</span>
        </div>
        <div class="stat">
            <span class="stat-dot stat-dot-blue"></span>
            <span class="stat-num">{recommended}</span>
            <span class="stat-label">Recommended</span>
        </div>
        <div class="stat">
            <span class="stat-dot stat-dot-yellow"></span>
            <span class="stat-num">{conditional}</span>
            <span class="stat-label">Conditional</span>
        </div>
        <div class="stat">
            <span class="stat-dot stat-dot-red"></span>
            <span class="stat-num">{marginal}</span>
            <span class="stat-label">Marginal</span>
        </div>
        <div class="stat">
            <span class="stat-num">{domain_count}</span>
            <span class="stat-label">Domains</span>
        </div>
        <div class="distrib-wrap">
            <div class="distrib-bars">{distrib_html}</div>
            <div>
                <span class="stat-num">{avg_score:.1f}</span>
                <span class="stat-label">Avg</span>
            </div>
        </div>
    </div>

    <div class="toolbar">
        <div class="search-box">
            <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            <input type="text" id="search" placeholder="Search skills...">
            <span class="results-count" id="results-count"></span>
            <span class="search-hint">/</span>
        </div>
        <div class="filter-group">
            {verdict_btns}
        </div>
        <div class="sort-group">
            <select id="sort-select">
                <option value="score-desc">Score &#x2193;</option>
                <option value="score-asc">Score &#x2191;</option>
                <option value="name-asc">Name A-Z</option>
                <option value="name-desc">Name Z-A</option>
                <option value="downloads-desc">Downloads &#x2193;</option>
            </select>
        </div>
        <div class="view-toggle">
            <button class="view-btn active" data-view="grid" title="Grid view">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
            </button>
            <button class="view-btn" data-view="list" title="List view">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="2" width="14" height="2.5" rx="1"/><rect x="1" y="6.75" width="14" height="2.5" rx="1"/><rect x="1" y="11.5" width="14" height="2.5" rx="1"/></svg>
            </button>
        </div>
    </div>

    <div class="domain-row">{domain_btns}</div>

    <div class="cards-grid" id="cards-container">
        {cards_html}
    </div>

    <footer class="footer">
        <div class="footer-line"></div>
        PandaEval v0.5.0 &middot; {total} skill evaluations &middot; {domain_count} domains
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

    # Disambiguate duplicate names by appending slug
    name_count = Counter(s.get("name", "") for s in skills)
    for s in skills:
        if name_count[s.get("name", "")] > 1 and s.get("slug"):
            s["name"] = f"{s['name']} ({s['slug']})"

    skills.sort(key=lambda x: x.get("score", 0), reverse=True)

    domains = sorted(set(s.get("domain", "unknown") for s in skills))
    verdicts = sorted(set(s.get("verdict", "") for s in skills))

    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "detail").mkdir(exist_ok=True)

    # Generate index
    index_html = build_index_html(skills, domains, verdicts)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Generate detail pages
    for s in skills:
        slug = generate_detail_slug(s)
        detail_html = build_detail_html(s)
        (DOCS_DIR / "detail" / f"{slug}.html").write_text(detail_html, encoding="utf-8")

    print(f"Generated dashboard: {len(skills)} skills, {skipped} skipped, {len(domains)} domains")
    print(f"Output: {DOCS_DIR}")


if __name__ == "__main__":
    main()
