#!/usr/bin/env python3
"""
Generate a skill card (model-card style markdown) from eval results.

Usage:
    python scripts/generate_skill_card.py \
        --workspace workspaces/test-runner/iteration-1 \
        --skill-name "test-runner" \
        --skill-slug "test-runner" \
        --eval-model "claude-opus-4-6" \
        --output skill-cards/test-runner-v0.1.0.md

Reads benchmark.json + grading.json files from the workspace and produces
a HuggingFace model-card style markdown evaluation report.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def load_json(path):
    with open(path) as f:
        return json.load(f)


def find_eval_dirs(workspace):
    """Find all eval directories in a workspace."""
    dirs = []
    for entry in sorted(os.listdir(workspace)):
        full = os.path.join(workspace, entry)
        if os.path.isdir(full) and os.path.exists(os.path.join(full, "eval_metadata.json")):
            dirs.append(full)
    return dirs


def format_pass_rate(rate):
    if rate is None:
        return "N/A"
    return f"{rate * 100:.0f}%"


def format_time(seconds):
    if seconds is None:
        return "N/A"
    return f"{seconds:.1f}s"


def format_tokens(tokens):
    if tokens is None:
        return "N/A"
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k"
    return str(tokens)


def compute_overall_score(benchmark):
    """Compute a 0-10 overall score from benchmark data."""
    summary = benchmark.get("run_summary", {})
    with_skill = summary.get("with_skill", {})
    without_skill = summary.get("without_skill", {})

    # Base score from pass rate (0-5 points)
    w_pr = with_skill.get("pass_rate", {}).get("mean", 0)
    wo_pr = without_skill.get("pass_rate", {}).get("mean", 0)
    pass_rate_score = w_pr * 5  # 0-5

    # Delta score: does skill improve over baseline? (0-3 points)
    delta_pr = w_pr - wo_pr
    if delta_pr > 0.2:
        delta_score = 3.0
    elif delta_pr > 0.1:
        delta_score = 2.0
    elif delta_pr > 0:
        delta_score = 1.0
    elif delta_pr == 0:
        delta_score = 0.5  # no improvement
    else:
        delta_score = 0.0  # skill makes things worse

    # Efficiency score: is the skill efficient? (0-2 points)
    w_time = with_skill.get("time_seconds", {}).get("mean", 999)
    wo_time = without_skill.get("time_seconds", {}).get("mean", 999)
    if wo_time > 0:
        time_ratio = w_time / wo_time
        if time_ratio <= 1.0:
            efficiency_score = 2.0  # faster or same
        elif time_ratio <= 1.5:
            efficiency_score = 1.5
        elif time_ratio <= 2.0:
            efficiency_score = 1.0
        elif time_ratio <= 3.0:
            efficiency_score = 0.5
        else:
            efficiency_score = 0.0
    else:
        efficiency_score = 1.0

    total = pass_rate_score + delta_score + efficiency_score
    return round(min(10, total), 1)


def generate_test_cases_detail(eval_dirs, workspace):
    """Generate detailed test case sections."""
    sections = []
    for eval_dir in eval_dirs:
        meta = load_json(os.path.join(eval_dir, "eval_metadata.json"))
        eval_name = meta.get("eval_name", os.path.basename(eval_dir))
        prompt = meta.get("prompt", "N/A")

        section = f"### {eval_name}\n\n"
        section += f"**Prompt:** {prompt}\n\n"

        # With skill grading
        with_grading_path = os.path.join(eval_dir, "with_skill", "grading.json")
        without_grading_path = os.path.join(eval_dir, "without_skill", "grading.json")

        for config, path in [("With Skill", with_grading_path), ("Without Skill", without_grading_path)]:
            if os.path.exists(path):
                grading = load_json(path)
                summary = grading.get("summary", {})
                section += f"**{config}:** {summary.get('passed', 0)}/{summary.get('total', 0)} assertions passed\n\n"

                expectations = grading.get("expectations", [])
                if expectations:
                    for exp in expectations:
                        status = "PASS" if exp.get("passed") else "FAIL"
                        section += f"- [{status}] {exp.get('text', 'N/A')}\n"
                    section += "\n"

        # Timing
        for config, dirname in [("With Skill", "with_skill"), ("Without Skill", "without_skill")]:
            timing_path = os.path.join(eval_dir, dirname, "timing.json")
            if os.path.exists(timing_path):
                timing = load_json(timing_path)
                section += f"**{config} timing:** {format_time(timing.get('total_duration_seconds'))} | {format_tokens(timing.get('total_tokens'))} tokens\n\n"

        sections.append(section)

    return "\n".join(sections) if sections else "No test cases found."


def generate_card(args):
    workspace = args.workspace
    benchmark_path = os.path.join(workspace, "benchmark.json")

    if not os.path.exists(benchmark_path):
        print(f"Error: benchmark.json not found at {benchmark_path}", file=sys.stderr)
        sys.exit(1)

    benchmark = load_json(benchmark_path)
    eval_dirs = find_eval_dirs(workspace)
    summary = benchmark.get("run_summary", {})
    with_skill = summary.get("with_skill", {})
    without_skill = summary.get("without_skill", {})
    delta = summary.get("delta", {})
    metadata = benchmark.get("metadata", {})
    notes = benchmark.get("notes", [])

    # Compute score
    overall_score = compute_overall_score(benchmark)

    # Read skill-eval version
    version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VERSION")
    skilleval_version = "unknown"
    if os.path.exists(version_file):
        with open(version_file) as f:
            skilleval_version = f.read().strip()

    eval_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    eval_model = args.eval_model or metadata.get("executor_model", "unknown")
    skill_name = args.skill_name or metadata.get("skill_name", "unknown")
    skill_slug = args.skill_slug or skill_name
    eval_id = f"{skill_slug}-{eval_date}-v{skilleval_version}"

    # Build strengths/weaknesses from notes and scores
    strengths = []
    weaknesses = []

    w_pr = with_skill.get("pass_rate", {}).get("mean", 0)
    wo_pr = without_skill.get("pass_rate", {}).get("mean", 0)

    if w_pr > wo_pr:
        strengths.append(f"Improves pass rate by {(w_pr - wo_pr) * 100:.0f}% over baseline")
    elif w_pr == wo_pr and w_pr > 0.8:
        weaknesses.append("No measurable improvement over baseline (same pass rate)")

    w_time = with_skill.get("time_seconds", {}).get("mean", 0)
    wo_time = without_skill.get("time_seconds", {}).get("mean", 0)
    if w_time and wo_time and w_time < wo_time:
        strengths.append(f"Faster than baseline ({format_time(w_time)} vs {format_time(wo_time)})")
    elif w_time and wo_time and w_time > wo_time * 2:
        weaknesses.append(f"Significantly slower than baseline ({format_time(w_time)} vs {format_time(wo_time)})")
    elif w_time and wo_time and w_time > wo_time:
        weaknesses.append(f"Slower than baseline ({format_time(w_time)} vs {format_time(wo_time)})")

    w_tokens = with_skill.get("tokens", {}).get("mean", 0)
    wo_tokens = without_skill.get("tokens", {}).get("mean", 0)
    if w_tokens and wo_tokens and w_tokens > wo_tokens * 1.5:
        weaknesses.append(f"Uses {w_tokens / wo_tokens:.1f}x more tokens than baseline")

    for note in notes:
        if any(w in note.lower() for w in ["value", "benefit", "better", "strength"]):
            strengths.append(note)
        elif any(w in note.lower() for w in ["slow", "overhead", "worse", "fail", "issue"]):
            weaknesses.append(note)

    strengths_text = "\n".join(f"- {s}" for s in strengths) if strengths else "- No clear strengths identified over baseline"
    weaknesses_text = "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "- No significant weaknesses found"

    # Recommendation
    if overall_score >= 7:
        recommendation = "Recommended. This skill provides clear value over the baseline."
    elif overall_score >= 5:
        recommendation = "Conditional. This skill shows some value but with trade-offs. Consider your use case."
    elif overall_score >= 3:
        recommendation = "Marginal. The skill adds overhead without proportional improvement. May need updates."
    else:
        recommendation = "Not recommended in current form. Baseline performance is comparable or better."

    # Test cases detail
    test_cases_detail = generate_test_cases_detail(eval_dirs, workspace)

    # Eval metadata JSON
    eval_meta = {
        "eval_id": eval_id,
        "skill_name": skill_name,
        "skill_slug": skill_slug,
        "eval_date": eval_date,
        "eval_model": eval_model,
        "skilleval_version": skilleval_version,
        "overall_score": overall_score,
        "with_skill_pass_rate": with_skill.get("pass_rate", {}).get("mean"),
        "without_skill_pass_rate": without_skill.get("pass_rate", {}).get("mean"),
        "evals_run": len(eval_dirs),
        "notes": notes
    }

    # Generate card
    card = f"""# Skill Card: {skill_name}

> Evaluated on ClawHub skill `{skill_slug}`

| Field | Value |
|-------|-------|
| **Skill** | {skill_name} |
| **Source** | [ClawHub](https://clawhub.com/skills/{skill_slug}) |
| **Eval Date** | {eval_date} |
| **Eval Model** | {eval_model} |
| **Eval Engine** | skill-eval v{skilleval_version} |
| **Eval ID** | {eval_id} |

---

## Overall Score: {overall_score}/10

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | {format_pass_rate(with_skill.get("pass_rate", {}).get("mean"))} | {format_pass_rate(without_skill.get("pass_rate", {}).get("mean"))} | {delta.get("pass_rate", "N/A")} |
| **Avg Time** | {format_time(with_skill.get("time_seconds", {}).get("mean"))} | {format_time(without_skill.get("time_seconds", {}).get("mean"))} | {delta.get("time_seconds", "N/A")} |
| **Avg Tokens** | {format_tokens(with_skill.get("tokens", {}).get("mean"))} | {format_tokens(without_skill.get("tokens", {}).get("mean"))} | {delta.get("tokens", "N/A")} |

## Test Cases

{test_cases_detail}

## Strengths

{strengths_text}

## Weaknesses

{weaknesses_text}

## Recommendation

{recommendation}

---

## Eval Metadata

```json
{json.dumps(eval_meta, indent=2)}
```

---

*Generated by skill-eval v{skilleval_version} | Model: {eval_model} | {eval_date}*
"""
    return card


def main():
    parser = argparse.ArgumentParser(description="Generate a skill evaluation card")
    parser.add_argument("--workspace", required=True, help="Path to iteration workspace")
    parser.add_argument("--skill-name", required=True, help="Skill display name")
    parser.add_argument("--skill-slug", help="Skill slug (defaults to skill-name)")
    parser.add_argument("--eval-model", default="claude-opus-4-6", help="Model used for evaluation")
    parser.add_argument("--output", required=True, help="Output markdown file path")

    args = parser.parse_args()
    if not args.skill_slug:
        args.skill_slug = args.skill_name

    card = generate_card(args)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(card)

    print(f"Skill card written to {args.output}")


if __name__ == "__main__":
    main()
