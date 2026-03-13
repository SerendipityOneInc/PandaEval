# Skill Card: Xiaohongshu Comment Assistant

> 小红书视频评论助手 — Auto-analyze xiaohongshu video content and generate/post contextual comments via browser automation.

| Field | Value |
|-------|-------|
| **Skill** | Xiaohongshu Comment Assistant |
| **Source** | [ClawHub](https://clawhub.com/skills/xiaohongshu-comment) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | xiaohongshu-comment-2026-03-09-v0.3.0 |

---

## Overall Score: 9.0/10

**Verdict:** Recommended

**Flags:** `dependency-gated` (Chrome Browser Relay + xiaohongshu login)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 100% | 12.5% | +87.5% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 5.0 | 5 | Perfect pass rate |
| Value-add | 2.5 | 3 | 87.5% delta — very high |
| Efficiency | 1.5 | 2 | 128 lines, compact and focused |
| **Total** | **9.0** | **10** | |

## Test Cases

### Test 1: Auto-Comment Chinese Video
- **With Skill:** 4/4 — browser profile=chrome, #detail-title/#detail-desc selectors, Chinese comments, posting sequence
- **Without Skill:** 1/4 — can generate Chinese comments but doesn't know DOM selectors or browser profile

### Test 2: Cooking Video Analysis
- **With Skill:** 4/4 — browser snapshot, cooking-themed comments, Browser Relay requirement, HTML selectors
- **Without Skill:** 0/4 — can't access xiaohongshu content without browser automation knowledge

## Strengths

- No phantom tooling — the skill is self-contained browser automation instructions
- Precise HTML selector table for all interaction points
- Complete workflow: extract -> analyze -> generate -> post
- Compact at 128 lines with clear step-by-step instructions

## Weaknesses

- Dependency-gated: requires Chrome Browser Relay extension and logged-in session
- Social media automation raises ethical/ToS considerations
- Hardcoded selectors may break if xiaohongshu updates their DOM
- No rate limiting guidance beyond "avoid frequent posting"

## Recommendation

**Recommended.** Clean, focused browser automation skill with precise DOM selectors and a complete workflow. The 87.5% delta confirms the baseline can't replicate this without the skill's platform-specific knowledge. Note: users should consider xiaohongshu's ToS before automated commenting.

---

## Eval Metadata

```json
{
  "eval_id": "xiaohongshu-comment-2026-03-09-v0.3.0",
  "skill_name": "Xiaohongshu Comment Assistant",
  "skill_slug": "xiaohongshu-comment",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 9.0,
  "with_skill_pass_rate": 1.0,
  "without_skill_pass_rate": 0.125,
  "delta": 0.875,
  "verdict": "Recommended",
  "flags": ["dependency-gated"]
}
```
