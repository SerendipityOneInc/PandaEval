#!/usr/bin/env python3
"""
Generate an interactive HTML leaderboard from skill cards.

Usage:
    python scripts/generate_leaderboard.py \
        --cards-dir skill-cards \
        --output leaderboard/index.html

Reads all skill card markdown files, extracts metadata JSON blocks,
and generates a sortable HTML leaderboard.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime


def extract_metadata(card_path):
    """Extract eval metadata JSON from a skill card markdown file."""
    with open(card_path) as f:
        content = f.read()

    # Find the JSON block in Eval Metadata section
    pattern = r'## Eval Metadata\s*```json\s*(\{.*?\})\s*```'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def extract_summary_table(card_path):
    """Extract the summary comparison table values."""
    with open(card_path) as f:
        content = f.read()

    result = {}

    # Extract overall score
    score_match = re.search(r'## Overall Score: ([\d.]+)/10', content)
    if score_match:
        result['overall_score'] = float(score_match.group(1))

    # Extract recommendation
    rec_match = re.search(r'## Recommendation\s*\n\s*(.+)', content)
    if rec_match:
        result['recommendation'] = rec_match.group(1).strip()

    return result


def find_latest_cards(cards_dir):
    """Find the latest card for each skill (by eval_date)."""
    cards_by_skill = {}

    for fname in os.listdir(cards_dir):
        if not fname.endswith('.md') or fname == 'TEMPLATE.md':
            continue

        path = os.path.join(cards_dir, fname)
        meta = extract_metadata(path)
        if not meta:
            continue

        slug = meta.get('skill_slug', fname.replace('.md', ''))
        eval_date = meta.get('eval_date', '1970-01-01')

        if slug not in cards_by_skill or eval_date > cards_by_skill[slug]['eval_date']:
            cards_by_skill[slug] = {
                **meta,
                **extract_summary_table(path),
                'card_file': fname
            }

    return cards_by_skill


def generate_html(cards_by_skill, version_file=None):
    """Generate the leaderboard HTML."""
    skilleval_version = "unknown"
    if version_file and os.path.exists(version_file):
        with open(version_file) as f:
            skilleval_version = f.read().strip()

    # Sort by overall score descending
    sorted_skills = sorted(
        cards_by_skill.values(),
        key=lambda x: x.get('overall_score', 0),
        reverse=True
    )

    rows_html = ""
    for rank, skill in enumerate(sorted_skills, 1):
        score = skill.get('overall_score', 0)
        if score >= 7:
            score_class = "score-high"
            badge = "Recommended"
            badge_class = "badge-green"
        elif score >= 5:
            score_class = "score-mid"
            badge = "Conditional"
            badge_class = "badge-yellow"
        elif score >= 3:
            score_class = "score-low"
            badge = "Marginal"
            badge_class = "badge-orange"
        else:
            score_class = "score-bad"
            badge = "Not Recommended"
            badge_class = "badge-red"

        w_pr = skill.get('with_skill_pass_rate')
        wo_pr = skill.get('without_skill_pass_rate')
        w_pr_str = f"{w_pr * 100:.0f}%" if w_pr is not None else "N/A"
        wo_pr_str = f"{wo_pr * 100:.0f}%" if wo_pr is not None else "N/A"

        delta = ""
        if w_pr is not None and wo_pr is not None:
            d = (w_pr - wo_pr) * 100
            if d > 0:
                delta = f'<span class="delta-pos">+{d:.0f}%</span>'
            elif d < 0:
                delta = f'<span class="delta-neg">{d:.0f}%</span>'
            else:
                delta = '<span class="delta-zero">0%</span>'

        rows_html += f"""
        <tr>
            <td class="rank">#{rank}</td>
            <td class="skill-name">
                <a href="https://clawhub.com/skills/{skill.get('skill_slug', '')}" target="_blank">
                    {skill.get('skill_name', 'Unknown')}
                </a>
            </td>
            <td class="score {score_class}">{score}</td>
            <td><span class="badge {badge_class}">{badge}</span></td>
            <td>{w_pr_str}</td>
            <td>{wo_pr_str}</td>
            <td>{delta}</td>
            <td>{skill.get('eval_model', 'N/A')}</td>
            <td>{skill.get('eval_date', 'N/A')}</td>
            <td>{skill.get('evals_run', 'N/A')}</td>
        </tr>"""

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skill Eval Leaderboard</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #0d1117;
        color: #c9d1d9;
        padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    h1 {{
        font-size: 2rem;
        color: #f0f6fc;
        margin-bottom: 0.5rem;
    }}
    .subtitle {{
        color: #8b949e;
        margin-bottom: 2rem;
        font-size: 0.9rem;
    }}
    .meta-bar {{
        display: flex;
        gap: 2rem;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: #161b22;
        border-radius: 8px;
        border: 1px solid #30363d;
        font-size: 0.85rem;
    }}
    .meta-bar span {{ color: #8b949e; }}
    .meta-bar strong {{ color: #c9d1d9; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        background: #161b22;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #30363d;
    }}
    th {{
        background: #21262d;
        color: #f0f6fc;
        padding: 12px 16px;
        text-align: left;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        user-select: none;
        border-bottom: 1px solid #30363d;
    }}
    th:hover {{ background: #282e36; }}
    td {{
        padding: 12px 16px;
        border-bottom: 1px solid #21262d;
        font-size: 0.9rem;
    }}
    tr:hover {{ background: #1c2128; }}
    .rank {{ color: #8b949e; font-weight: 600; }}
    .skill-name a {{
        color: #58a6ff;
        text-decoration: none;
    }}
    .skill-name a:hover {{ text-decoration: underline; }}
    .score {{
        font-weight: 700;
        font-size: 1.1rem;
    }}
    .score-high {{ color: #3fb950; }}
    .score-mid {{ color: #d29922; }}
    .score-low {{ color: #db6d28; }}
    .score-bad {{ color: #f85149; }}
    .badge {{
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .badge-green {{ background: #238636; color: #fff; }}
    .badge-yellow {{ background: #9e6a03; color: #fff; }}
    .badge-orange {{ background: #bd561d; color: #fff; }}
    .badge-red {{ background: #da3633; color: #fff; }}
    .delta-pos {{ color: #3fb950; }}
    .delta-neg {{ color: #f85149; }}
    .delta-zero {{ color: #8b949e; }}
    .footer {{
        margin-top: 2rem;
        text-align: center;
        color: #484f58;
        font-size: 0.8rem;
    }}
</style>
</head>
<body>
<div class="container">
    <h1>Skill Eval Leaderboard</h1>
    <p class="subtitle">Automated evaluation of ClawHub skills — does the skill actually help?</p>

    <div class="meta-bar">
        <div><span>Engine:</span> <strong>skill-eval v{skilleval_version}</strong></div>
        <div><span>Skills Evaluated:</span> <strong>{len(sorted_skills)}</strong></div>
        <div><span>Generated:</span> <strong>{generated_at}</strong></div>
    </div>

    <table id="leaderboard">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Skill</th>
                <th onclick="sortTable(2)">Score</th>
                <th>Verdict</th>
                <th>With Skill</th>
                <th>Baseline</th>
                <th>Delta</th>
                <th>Model</th>
                <th onclick="sortTable(8)">Date</th>
                <th>Tests</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="footer">
        <p>Generated by skill-eval v{skilleval_version} | {generated_at}</p>
        <p>Scores: 7-10 Recommended | 5-6.9 Conditional | 3-4.9 Marginal | 0-2.9 Not Recommended</p>
    </div>
</div>

<script>
function sortTable(colIdx) {{
    const table = document.getElementById('leaderboard');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    const dir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
    table.dataset.sortDir = dir;

    rows.sort((a, b) => {{
        let aVal = a.cells[colIdx].textContent.trim();
        let bVal = b.cells[colIdx].textContent.trim();
        let aNum = parseFloat(aVal);
        let bNum = parseFloat(bVal);

        if (!isNaN(aNum) && !isNaN(bNum)) {{
            return dir === 'asc' ? aNum - bNum : bNum - aNum;
        }}
        return dir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }});

    rows.forEach(row => tbody.appendChild(row));
}}
</script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate skill eval leaderboard HTML")
    parser.add_argument("--cards-dir", required=True, help="Directory containing skill card .md files")
    parser.add_argument("--output", required=True, help="Output HTML file path")

    args = parser.parse_args()

    version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VERSION")
    cards = find_latest_cards(args.cards_dir)

    if not cards:
        print("No skill cards found. Run evaluations first.", file=sys.stderr)
        sys.exit(1)

    html = generate_html(cards, version_file)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(html)

    print(f"Leaderboard written to {args.output} ({len(cards)} skills)")


if __name__ == "__main__":
    main()
