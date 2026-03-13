#!/usr/bin/env python3
"""Parse skill-card markdown files and generate a static dashboard site."""

import json
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


def build_card_html(skill: dict) -> str:
    slug = generate_detail_slug(skill)
    score = skill.get("score", 0)
    sc = score_color_class(score)
    name = skill["name"]
    domain = skill.get("domain", "")
    eval_engine = skill.get("eval_engine", "")
    eval_model = skill.get("eval_model", "")
    domain_display = domain if domain else eval_engine
    verdict = skill.get("verdict", "")
    vc = verdict_badge_class(verdict)
    downloads = skill.get("downloads", 0)
    if isinstance(downloads, str):
        downloads = int(downloads.replace(",", ""))
    dl_str = f"{downloads:,} downloads" if downloads else eval_model

    # Top 3 breakdown scores for the card
    breakdown = skill.get("breakdown", {})
    sorted_bd = sorted(breakdown.items(), key=lambda x: x[1]["score"], reverse=True)[:3]
    bars_html = ""
    for comp, bd in sorted_bd:
        pct = bd["score"] / bd["max"] * 100 if bd["max"] else 0
        score_display = f"{bd['score']:g}/{bd['max']:g}"
        bars_html += f"""
            <div class="bar-row">
                <span class="bar-label">{comp}</span>
                <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
                <span class="bar-val">{score_display}</span>
            </div>"""

    flags_html = ""
    for f in skill.get("flags", []):
        flags_html += f'<span class="tag">{f}</span>'

    return f"""
    <div class="card" data-domain="{domain_display}" data-verdict="{vc}" data-score="{score}" data-name="{name.lower()}" data-downloads="{downloads}" onclick="location.href='detail/{slug}.html'">
        <div class="card-header">
            <div>
                <h3 class="card-title">{name}</h3>
                <span class="card-meta">{domain_display} · {dl_str}</span>
            </div>
            <div class="score-circle score-{sc}">
                <span class="score-num">{score}</span>
                <span class="score-den">/10</span>
            </div>
        </div>
        <div class="card-bars">{bars_html}</div>
        <div class="card-footer">
            <div class="tags">{flags_html}<span class="tag tag-{vc}">{verdict}</span></div>
        </div>
    </div>"""


def build_detail_html(skill: dict) -> str:
    slug = generate_detail_slug(skill)
    score = skill.get("score", 0)
    sc = score_color_class(score)
    name = skill["name"]
    domain = skill.get("domain", "unknown")
    verdict = skill.get("verdict", "")
    vc = verdict_badge_class(verdict)
    desc = skill.get("description", "")
    downloads = skill.get("downloads", 0)
    if isinstance(downloads, str):
        downloads = int(downloads.replace(",", ""))
    dl_str = f"{downloads:,}" if downloads else "—"
    eval_date = skill.get("eval_date", "")
    eval_engine = skill.get("eval_engine", "")
    source_url = skill.get("source_url", "#")

    flags_html = ""
    for f in skill.get("flags", []):
        flags_html += f'<span class="tag">{f}</span>'
    flags_html += f'<span class="tag tag-{vc}">{verdict}</span>'

    # Full breakdown
    breakdown = skill.get("breakdown", {})
    bd_html = ""
    for comp, bd in sorted(breakdown.items()):
        pct = bd["score"] / bd["max"] * 100 if bd["max"] else 0
        score_display = f"{bd['score']:g}/{bd['max']:g}"
        bd_html += f"""
        <div class="detail-score-item">
            <span class="ds-label">{comp}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
            <span class="ds-val">{score_display}</span>
        </div>"""

    # Metrics
    metrics = skill.get("metrics", {})
    metrics_html = ""
    for k, v in metrics.items():
        label = k.replace("_", " ").title()
        if isinstance(v, bool):
            v = "Yes" if v else "No"
        metrics_html += f"""
        <div class="metric-item">
            <span class="metric-label">{label}</span>
            <span class="metric-val">{v}</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — PandaEval</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="container detail-page">
    <a href="../index.html" class="back-btn">← Back to list</a>
    <div class="detail-header-card">
        <div class="detail-info">
            <h1>{name}</h1>
            <p class="detail-sub">{domain} · {eval_date} · {dl_str} downloads</p>
            <p class="detail-desc">{desc}</p>
            <div class="tags">{flags_html}</div>
        </div>
        <div class="score-circle score-circle-lg score-{sc}">
            <span class="score-num">{score}</span>
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
</html>"""


def build_index_html(skills: list[dict], domains: list[str], verdicts: list[str]) -> str:
    total = len(skills)
    avg_score = sum(s["score"] for s in skills) / total if total else 0
    domain_count = len(domains)
    total_downloads = sum(s.get("downloads", 0) if isinstance(s.get("downloads", 0), int) else int(str(s.get("downloads", 0)).replace(",", "")) for s in skills)

    # Count verdicts
    verdict_counts = Counter(verdict_badge_class(s.get("verdict", "")) for s in skills)
    recommended = verdict_counts.get("green", 0) + verdict_counts.get("blue", 0)
    caution = verdict_counts.get("yellow", 0)
    not_rec = verdict_counts.get("red", 0)

    cards_html = "\n".join(build_card_html(s) for s in skills)

    domain_btns = '<button class="filter-btn active" data-filter="all" data-group="domain">All Domains</button>'
    for d in sorted(domains):
        domain_btns += f'<button class="filter-btn" data-filter="{d}" data-group="domain">{d}</button>'

    verdict_btns = '<button class="filter-btn active" data-filter="all" data-group="verdict">All</button>'
    for label, vc in [("Highly Rec.", "green"), ("Recommended", "blue"), ("Caution", "yellow"), ("Not Rec.", "red")]:
        verdict_btns += f'<button class="filter-btn" data-filter="{vc}" data-group="verdict">{label}</button>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PandaEval — Skill Evaluation Dashboard</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
    <header class="hero">
        <div class="logo">🐼 PandaEval</div>
        <p class="tagline">Automated Skill Evaluation for AI Agents</p>
    </header>

    <div class="stats-bar">
        <div class="stat"><span class="stat-num">{total}</span><span class="stat-label">Skills</span></div>
        <div class="stat"><span class="stat-num">{recommended}</span><span class="stat-label">Recommended</span></div>
        <div class="stat"><span class="stat-num">{caution}</span><span class="stat-label">Caution</span></div>
        <div class="stat"><span class="stat-num">{not_rec}</span><span class="stat-label">Not Rec.</span></div>
        <div class="stat"><span class="stat-num">{domain_count}</span><span class="stat-label">Domains</span></div>
        <div class="stat"><span class="stat-num">{avg_score:.1f}</span><span class="stat-label">Avg Score</span></div>
    </div>

    <div class="toolbar">
        <div class="search-box">
            <span class="search-icon">🔍</span>
            <input type="text" id="search" placeholder="Search skills, domains, flags...">
        </div>
        <div class="filter-group">
            {verdict_btns}
        </div>
        <div class="filter-group">
            {domain_btns}
        </div>
        <div class="sort-group">
            <select id="sort-select">
                <option value="score-desc">Score ↓</option>
                <option value="score-asc">Score ↑</option>
                <option value="name-asc">Name A-Z</option>
                <option value="name-desc">Name Z-A</option>
                <option value="downloads-desc">Downloads ↓</option>
            </select>
        </div>
        <div class="view-toggle">
            <button class="view-btn active" data-view="grid" title="Grid view">▦</button>
            <button class="view-btn" data-view="list" title="List view">☰</button>
        </div>
    </div>

    <div class="cards-grid" id="cards-container">
        {cards_html}
    </div>

    <footer class="footer">
        PandaEval — Generated from {total} skill evaluations
    </footer>
</div>
<script src="app.js"></script>
</body>
</html>"""


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
