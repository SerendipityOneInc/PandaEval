# Skill Card: EasyLink EasyDoc Parse

> Convert unstructured documents into structured JSON/markdown via EasyDoc REST API (China and global platforms).

| Field | Value |
|-------|-------|
| **Skill** | EasyLink EasyDoc Parse |
| **Source** | [ClawHub](https://clawhub.com/skills/easydoc-parse) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | easydoc-parse-2026-03-09-v0.3.0 |

---

## Overall Score: 9.5/10

**Verdict:** Recommended

**Flags:** `phantom-tooling` (script + reference file missing), `dependency-gated` (EASYLINK_API_KEY / EASYDOC_API_KEY)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 100% | 0% | +100% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 5.0 | 5 | Perfect pass rate |
| Value-add | 3.0 | 3 | Maximum delta — novel API |
| Efficiency | 1.5 | 2 | 134 lines, clean and well-organized |
| **Total** | **9.5** | **10** | |

## Test Cases

### Test 1: China Platform Parse
- **With Skill:** 4/4 — correct base URL, submit endpoint, polling pattern, parse mode
- **Without Skill:** 0/4 — baseline has zero knowledge of EasyLink/EasyDoc APIs

### Test 2: Platform Comparison
- **With Skill:** 4/4 — distinguishes cn vs global, different env vars, output contract, onboarding steps
- **Without Skill:** 0/4 — baseline can't distinguish platforms or provide any EasyDoc-specific guidance

## Strengths

- Excellent dual-platform documentation — clearly separates cn (easylink-ai.com) from global (easydoc.sh)
- Well-defined output contract (task_id, status, files with markdown/nodes)
- Concise at 134 lines — not bloated, every section serves a purpose
- Clear onboarding flow with platform-specific registration URLs

## Weaknesses

- Phantom tooling: scripts/easydoc_parse.py and references/easydoc-rest-api.md missing
- Dependency-gated: requires API key for either platform
- No error handling examples beyond generic retry suggestions

## Recommendation

**Recommended.** One of the cleanest API documentation skills evaluated. 134 lines covering two platforms with clear workflows, explicit output contracts, and practical onboarding. The dual-platform design is genuinely useful and well-executed.

---

## Eval Metadata

```json
{
  "eval_id": "easydoc-parse-2026-03-09-v0.3.0",
  "skill_name": "EasyLink EasyDoc Parse",
  "skill_slug": "easydoc-parse",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 9.5,
  "with_skill_pass_rate": 1.0,
  "without_skill_pass_rate": 0.0,
  "delta": 1.0,
  "verdict": "Recommended",
  "flags": ["phantom-tooling", "dependency-gated"]
}
```
