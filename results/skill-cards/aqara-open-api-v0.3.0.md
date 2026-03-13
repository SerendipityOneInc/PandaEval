# Skill Card: Aqara Open API

> Query and control Aqara/Lumi smart home devices via the Aqara Open Platform API with cache-first data model and safety-first design.

| Field | Value |
|-------|-------|
| **Skill** | Aqara Open API |
| **Source** | [ClawHub](https://clawhub.com/skills/aqara-open-api) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | aqara-open-api-2026-03-09-v0.3.0 |

---

## Overall Score: 9.0/10

**Verdict:** Recommended

**Flags:** `phantom-tooling` (script + data + reference files missing), `dependency-gated` (AQARA_OPEN_API_TOKEN, AQARA_ENDPOINT_URL)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 100% | 0% | +100% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 5.0 | 5 | Perfect pass rate |
| Value-add | 3.0 | 3 | Maximum delta — novel proprietary API |
| Efficiency | 1.0 | 2 | 472 lines is substantial, but justified by API complexity and safety rules |
| **Total** | **9.0** | **10** | |

## Test Cases

### Test 1: Device Control
- **With Skill:** 4/4 — cache-first pattern, 4-field envelope with v1, ExecuteTraitRequest, IDs-from-cache mandate
- **Without Skill:** 0/4 — baseline has zero knowledge of Aqara's proprietary API

### Test 2: Space Management
- **With Skill:** 4/4 — exact GetSpacesRequest (no guessed variants), CreateSpaceRequest, AssociateDevicesToSpaceRequest, spaceId-from-API mandate
- **Without Skill:** 0/4 — baseline would guess wrong request type names

## Strengths

- **Best-in-class API skill design** — cache-first data model, forbidden behavior table, decision trees, SOPs
- Safety-first: never guess IDs, never invent request types — critical for device control
- Comprehensive whitelist approach to request types prevents API errors
- Clear execution model: script for bulk fetch, curl for everything else
- Decision trees and SOPs make the skill usable as an operational runbook

## Weaknesses

- 472 lines is the longest skill in batch 4 — though every section is justified
- Phantom tooling: fetch_all_devices.sh, data/devices.json, reference files missing
- Dependency-gated: two environment variables required
- Heavy token overhead (87%) — acceptable given safety requirements

## Recommendation

**Recommended.** This is arguably the best-designed API skill in the entire 100-skill expansion. The cache-first pattern, forbidden behavior table, and type-whitelist approach set a gold standard for smart home API skills. The 472-line length is justified by the complexity and safety requirements.

---

## Eval Metadata

```json
{
  "eval_id": "aqara-open-api-2026-03-09-v0.3.0",
  "skill_name": "Aqara Open API",
  "skill_slug": "aqara-open-api",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 9.0,
  "with_skill_pass_rate": 1.0,
  "without_skill_pass_rate": 0.0,
  "delta": 1.0,
  "verdict": "Recommended",
  "flags": ["phantom-tooling", "dependency-gated"]
}
```
