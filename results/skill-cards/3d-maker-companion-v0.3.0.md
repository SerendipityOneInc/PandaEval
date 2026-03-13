# Skill Card: 3D Maker Companion

> Professional assistant for 3D printing, laser engraving, and 3D modeling workflows with Meshy AI integration.

| Field | Value |
|-------|-------|
| **Skill** | 3D Maker Companion |
| **Source** | [ClawHub](https://clawhub.com/skills/3d-maker-companion) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | 3d-maker-companion-2026-03-09-v0.3.0 |

---

## Overall Score: 8.0/10

**Verdict:** Recommended

**Flags:** `phantom-tooling` (scripts/meshy_client.py missing), `dependency-gated` (MESHY_API_KEY)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 100% | 50% | +50% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 5.0 | 5 | Perfect pass rate |
| Value-add | 1.5 | 3 | 50% delta — baseline knows 3D printing basics |
| Efficiency | 1.5 | 2 | 72 lines, very compact |
| **Total** | **8.0** | **10** | |

## Test Cases

### Test 1: Dragon Figurine 3D Print
- **With Skill:** 4/4 — 4-stage workflow, Meshy AI recommendation, FDM optimization, PLA settings
- **Without Skill:** 2/4 — knows FDM basics and PLA but lacks structured workflow and Meshy AI specifics

### Test 2: Image-to-3D + Laser Engraving
- **With Skill:** 4/4 — Meshy AI image-to-3D, 3-view reference method, laser safety, STL export
- **Without Skill:** 2/4 — knows laser basics and file formats but lacks Meshy AI and blueprint method

## Strengths

- Extremely compact at 72 lines — excellent information density
- 4-stage maker workflow (ideation -> modeling -> refinement -> slicing) is a genuine process contribution
- Meshy AI integration with DCC bridges and slicer export options
- Cross-domain coverage: 3D printing + laser engraving + AI generation in one skill

## Weaknesses

- scripts/meshy_client.py is phantom — the Python client is referenced but missing
- Baseline already knows 3D printing and laser engraving fundamentals well
- Limited depth on any single topic — trades breadth for brevity
- No troubleshooting guide for common print failures

## Recommendation

**Recommended.** Compact, cross-domain maker skill that bridges AI generation and physical fabrication. The 4-stage workflow and Meshy AI specifics are genuine differentiators. Would benefit from the actual Python client script.

---

## Eval Metadata

```json
{
  "eval_id": "3d-maker-companion-2026-03-09-v0.3.0",
  "skill_name": "3D Maker Companion",
  "skill_slug": "3d-maker-companion",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 8.0,
  "with_skill_pass_rate": 1.0,
  "without_skill_pass_rate": 0.5,
  "delta": 0.5,
  "verdict": "Recommended",
  "flags": ["phantom-tooling", "dependency-gated"]
}
```
