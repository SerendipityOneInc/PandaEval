# Skill Card: Greece Travel Guide

> Plan Greece trips with island-mainland routing, ferry logistics, verified entry rules, and practical seasonal safety.

| Field | Value |
|-------|-------|
| **Skill** | Greece Travel Guide |
| **Source** | [ClawHub](https://clawhub.com/skills/greece) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | greece-2026-03-09-v0.3.0 |

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
| Value-add | 1.0 | 3 | Moderate delta — baseline already knows Greece well |
| Efficiency | 1.5 | 2 | 127 lines, well-structured core rules |
| **Total** | **7.5** | **10** | |

## Test Cases

### Test 1: Athens + Island Hopping July
- **With Skill:** 4/4 — cluster routing, dual transport models, Meltemi/heat warning, Schengen notes
- **Without Skill:** 2/4 — mentions heat and Schengen but no cluster discipline or dual transport models

### Test 2: Family October Trip
- **With Skill:** 4/4 — single macro-cluster, family ferry logistics, October seasonality, family budget math
- **Without Skill:** 3/4 — reasonable family advice but misses family-specific ferry booking guidance

## Strengths

- 7 core rules enforce Greece-specific planning discipline
- Cluster-based routing prevents over-ambitious island hopping
- Meltemi wind awareness is a genuine planning differentiator
- "Budget for Full Greece Math" captures hidden costs (ferry cabins, port transfers, beach fees)

## Weaknesses

- 25+ phantom reference files — no deep regional content exists
- Identical template to Chile and Argentina — same formula, same score range
- Baseline knows Greece geography, islands, and Schengen rules well
- No ferry schedule data, booking platform recommendations, or live references

## Recommendation

**Recommended.** Consistent with the travel guide template pattern — 7.5 score mirrors Chile and Argentina exactly. The cluster routing and Meltemi awareness are the strongest discriminators. Would benefit from actual reference content.

---

## Eval Metadata

```json
{
  "eval_id": "greece-2026-03-09-v0.3.0",
  "skill_name": "Greece Travel Guide",
  "skill_slug": "greece",
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
