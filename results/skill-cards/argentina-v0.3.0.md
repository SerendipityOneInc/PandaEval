# Skill Card: Argentina Travel Guide

> Plan Argentina trips with region-specific routing, money strategy, seasonal timing, and practical travel logistics.

| Field | Value |
|-------|-------|
| **Skill** | Argentina Travel Guide |
| **Source** | [ClawHub](https://clawhub.com/skills/argentina) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | argentina-2026-03-09-v0.3.0 |

---

## Overall Score: 7.5/10

**Verdict:** Recommended

**Flags:** `phantom-tooling` (25+ reference files missing)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 100% | 62.5% | +37.5% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 5.0 | 5 | Perfect pass rate |
| Value-add | 1.0 | 3 | Moderate delta — baseline already knows Argentina well |
| Efficiency | 1.5 | 2 | 126 lines, well-structured core rules |
| **Total** | **7.5** | **10** | |

## Test Cases

### Test 1: Buenos Aires + Patagonia 10-Day
- **With Skill:** 4/4 — feasibility check via Rule 1, dual transport models via Rule 5, entry docs via Rule 2, March weather via Rule 3
- **Without Skill:** 2/4 — notes feasibility and entry requirements, but no dual transport models or month-specific Patagonia conditions

### Test 2: Money Strategy
- **With Skill:** 4/4 — blue dollar discussion, card/cash strategy, tipping/VAT, outdated-blog-advice trap warning
- **Without Skill:** 3/4 — knows exchange rate complexity and tipping, but doesn't specifically warn about common money traps

## Strengths

- 7 core rules enforce Argentina-specific planning discipline
- "Route by Macro-Region" prevents common tourist overreach
- Dual transport model mandate (flight vs bus/road) with explicit tradeoffs
- Common Traps section captures real mistakes (blog-based exchange rates, casual Patagonia merging)

## Weaknesses

- 25+ phantom reference files — no deep regional content exists
- Baseline model already knows Argentina geography, entry rules, and exchange rates well
- Same template as Chile and Greece — diminishing marginal novelty
- No actual pricing data, booking platform recommendations, or live references

## Recommendation

**Recommended.** The 7 core rules add genuine planning structure that the baseline lacks, particularly the dual transport mandate and common traps section. Same score as Chile (7.5) — the travel guide template is a reliable mid-tier performer.

---

## Eval Metadata

```json
{
  "eval_id": "argentina-2026-03-09-v0.3.0",
  "skill_name": "Argentina Travel Guide",
  "skill_slug": "argentina",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 7.5,
  "with_skill_pass_rate": 1.0,
  "without_skill_pass_rate": 0.625,
  "delta": 0.375,
  "verdict": "Recommended",
  "flags": ["phantom-tooling"]
}
```
