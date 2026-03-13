# Skill Card: Speech Generation

> Generate spoken audio via OpenAI TTS with structured voice instruction augmentation and batch workflows.

| Field | Value |
|-------|-------|
| **Skill** | Speech Generation |
| **Source** | [ClawHub](https://clawhub.com/skills/speech) |
| **Eval Date** | 2026-03-09 |
| **Eval Model** | claude-opus-4-6 |
| **Eval Engine** | skill-eval v0.3.0 |
| **Eval ID** | speech-2026-03-09-v0.3.0 |

---

## Overall Score: 9.0/10

**Verdict:** Recommended

**Flags:** `phantom-tooling` (11 reference files + 1 script missing), `dependency-gated` (OPENAI_API_KEY)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| **Pass Rate** | 100% | 25% | +75% |

## Score Breakdown

| Component | Score | Max | Notes |
|-----------|-------|-----|-------|
| Quality | 5.0 | 5 | Perfect pass rate across both test cases |
| Value-add | 2.5 | 3 | 75% delta — instruction augmentation template is highly discriminating |
| Efficiency | 1.5 | 2 | 167 lines, well-structured. Moderate overhead from phantom refs |
| **Total** | **9.0** | **10** | |

## Test Cases

### Test 1: Product Demo Voiceover
- **With Skill:** 4/4 — structured instruction augmentation template, cedar voice default, CLI reference, API constraints
- **Without Skill:** 1/4 — only mentions 4096 char limit (known from OpenAI docs); no structured template, no specific voice, no CLI

### Test 2: IVR Batch Prompts
- **With Skill:** 4/4 — JSONL batch format, individual filenames, IVR-specific instructions, proper tmp/output directories
- **Without Skill:** 1/4 — generates individual filenames but uses Python loop, generic tone, generic output paths

## Strengths

- Voice instruction augmentation template (Voice Affect, Tone, Pacing, etc.) is the standout discriminator
- Explicit single vs batch decision tree with JSONL convention
- Opinionated defaults: cedar/marin voices, gpt-4o-mini-tts model, 50 RPM cap
- File organization conventions (tmp/speech/ vs output/speech/) add reproducibility

## Weaknesses

- Massive phantom tooling: 11 reference files and scripts/text_to_speech.py all missing
- Dependency-gated: requires OPENAI_API_KEY
- Without the bundled CLI, the batch workflow is aspirational
- Some reference files (narration.md, voiceover.md, ivr.md) would provide significant additional value

## Recommendation

**Recommended.** The instruction augmentation template alone justifies the skill — it produces a structured, reproducible voice specification format that the baseline never generates. Would be exceptional if the phantom tooling existed.

---

## Eval Metadata

```json
{
  "eval_id": "speech-2026-03-09-v0.3.0",
  "skill_name": "Speech Generation",
  "skill_slug": "speech",
  "eval_date": "2026-03-09",
  "eval_model": "claude-opus-4-6",
  "skilleval_version": "0.3.0",
  "overall_score": 9.0,
  "with_skill_pass_rate": 1.0,
  "without_skill_pass_rate": 0.25,
  "delta": 0.75,
  "verdict": "Recommended",
  "flags": ["phantom-tooling", "dependency-gated"]
}
```
