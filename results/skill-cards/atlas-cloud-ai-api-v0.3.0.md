# Skill Card: Atlas Cloud AI API

> One API key for AI image generation, video generation, and LLM chat — covering Nano Banana 2, Seedream, Kling, Seedance, Qwen, DeepSeek and more.

| Field | Value |
|-------|-------|
| **Skill** | Atlas Cloud AI API |
| **Source** | [ClawHub](https://clawhub.com/skills/atlas-cloud-ai-api) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | atlas-cloud-ai-api-2026-03-09-v0.3.0 |

---

## Overall Score: 9.0/10

**Verdict:** Recommended

**Flags:** `phantom-tooling` (4 reference files missing), `dependency-gated` (ATLASCLOUD_API_KEY), `reference-manual`

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 100% | 0% | +100% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 5.0 | 5 | Perfect pass rate |
| Value-add | 3.0 | 3 | Maximum delta — novel API |
| Efficiency | 1.0 | 2 | 201 lines with heavy pricing tables; reference-manual pattern |
| **Total** | **9.0** | **10** | |

## Test Cases

### Test 1: Image Generation
- **With Skill:** 4/4 — correct endpoint, async polling pattern, concrete model ID, Bearer auth
- **Without Skill:** 0/4 — baseline has zero knowledge of Atlas Cloud's API

### Test 2: LLM Chat Integration
- **With Skill:** 4/4 — correct base_url, model pricing comparison, working OpenAI SDK code, SDK compatibility
- **Without Skill:** 0/4 — baseline can't produce Atlas Cloud-specific integration code

## Strengths

- Comprehensive API coverage: image, video, and LLM in one skill
- Clear async polling pattern documentation
- OpenAI SDK compatibility is well-documented and practically useful
- Model pricing tables enable informed model selection

## Weaknesses

- Reference-manual pattern: pricing tables dominate the skill content
- Unsubstantiated savings claims (e.g., "28% cheaper", "15% cheaper") — no independent verification
- 4 phantom reference files for implementation details
- Dependency-gated: requires paid API key

## Recommendation

**Recommended.** Essential for Atlas Cloud integration — 100% delta confirms the model has zero prior knowledge. The reference-manual overhead is the only penalty; the API documentation itself is solid and actionable.

---

## Eval Metadata

```json
{
  "eval_id": "atlas-cloud-ai-api-2026-03-09-v0.3.0",
  "skill_name": "Atlas Cloud AI API",
  "skill_slug": "atlas-cloud-ai-api",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 9.0,
  "with_skill_pass_rate": 1.0,
  "without_skill_pass_rate": 0.0,
  "delta": 1.0,
  "verdict": "Recommended",
  "flags": ["phantom-tooling", "dependency-gated", "reference-manual", "unsubstantiated-claims"]
}
```
