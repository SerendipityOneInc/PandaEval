# Skill Card: Adam Daily Life Manager

> A personal assistant for managing everyday life — schedules, tasks, family coordination, and planning.

| Field | Value |
|-------|-------|
| **Skill** | Adam Daily Life Manager |
| **Source** | [ClawHub](https://clawhub.com/skills/adam-skill) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | adam-skill-2026-03-09-v0.3.0 |

---

## Overall Score: 4.9/10

**Verdict:** Marginal

**Flags:** `zero-delta`, `rtf-format`, `no-behavioral-instructions`

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 87.5% | 87.5% | +0% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 4.4 | 5 | 87.5% pass rate |
| Value-add | 0.0 | 3 | Zero delta — baseline identical |
| Efficiency | 0.5 | 2 | Overhead without any value gain |
| **Total** | **4.9** | **10** | |

## Test Cases

### Test 1: Weekly Planning
- **With Skill:** 4/4 — day-by-day schedule, conflict resolution, prioritization, time slots
- **Without Skill:** 4/4 — identical quality. Baseline excels at personal scheduling tasks.

### Test 2: Family Meal Planning
- **With Skill:** 3/4 — meals, dietary constraints, shopping list. Misses specific cost estimates.
- **Without Skill:** 3/4 — identical results. Same strengths and weaknesses.

## Strengths

- None measurable. The skill adds zero value over baseline.

## Weaknesses

- **RTF format:** SKILL.md is RTF-encoded, not proper markdown. May cause parsing issues.
- **Zero behavioral instructions:** 36 lines of generic feature bullets with no workflow, no output format, no constraints
- **Redundant to baseline:** Schedule management, task organization, meal planning are core LLM capabilities
- **No output schema:** Nothing enforceable that would change model behavior
- **No prioritization framework:** Lists "prioritize tasks by urgency and importance" but doesn't define how

## Recommendation

**Not recommended.** This is the quintessential "skill that describes what an LLM already does." The baseline model produces identical results without it. The RTF formatting is an additional red flag suggesting the SKILL.md wasn't designed for agent consumption.

---

## Eval Metadata

```json
{
  "eval_id": "adam-skill-2026-03-09-v0.3.0",
  "skill_name": "Adam Daily Life Manager",
  "skill_slug": "adam-skill",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 4.9,
  "with_skill_pass_rate": 0.875,
  "without_skill_pass_rate": 0.875,
  "delta": 0.0,
  "verdict": "Marginal",
  "flags": ["zero-delta", "rtf-format", "no-behavioral-instructions"]
}
```
