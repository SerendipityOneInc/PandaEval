# Common Failure Modes

Catalog of recurring issues found during evaluations. Reference this when designing assertions to catch known problems.

## Bootstrapped (v0.1.0)

### Non-discriminating assertions
- **Symptom:** 100% pass rate in both with-skill and without-skill
- **Cause:** Assertions test basic task completion, not skill-added value
- **Fix:** Add assertions that specifically target what the skill claims to improve

### Missing dependencies
- **Symptom:** Skill run errors out, baseline works fine
- **Cause:** CLI tool not installed or API key not set
- **Fix:** Pre-flight check for required binaries and env vars before eval

### Overhead without benefit
- **Symptom:** Same quality, 2-5x more tokens and time
- **Cause:** Skill adds complexity (extra tool calls, intermediate steps) without improving output
- **Fix:** Track efficiency metrics alongside quality. Flag skills where delta_quality ~0 but delta_cost >> 0

---

*Updated after each evaluation cycle.*

## General-User Batch Additions (v0.2.0)

### Dependency-gated hard fail (paid skill)
- **Symptom:** with-skill run returns setup/config error; baseline completes task normally.
- **Cause:** missing SkillPay/API credential and no local fallback path.
- **Fix:** mark as `dependency-gated` in benchmark notes; re-evaluate after credential provisioning.

### Template compliance drift under data outages
- **Symptom:** skill output omits required sections (source/freshness/disclaimer) when external data fetch fails.
- **Cause:** error path bypasses required output-floor formatter.
- **Fix:** enforce output-floor checks in failure branches; add deterministic assertion on mandatory sections.

### High-overhead framework inflation
- **Symptom:** output quality improves slightly but token/time costs double.
- **Cause:** skill injects broad framework context not needed for narrow tasks.
- **Fix:** add prompt routing guidance for "quick answer" mode vs "full framework" mode.

## Batch 3 Additions (v0.2.0, 2026-03-09)

### Phantom tooling (non-existent scripts)
- **Symptom:** Skill references CLI scripts or tools that don't exist (e.g., `scrape_reviews.py`, `compare_reviews.py`).
- **Cause:** Skill author created a framework skill but documented it as if the tooling exists.
- **Affect:** Users may try to run the scripts and fail. However, the framework/template itself can still add structural value.
- **Fix:** Add "phantom tooling" check to pre-flight. Flag in skill card. Separately evaluate framework value vs tool value.

### Low delta on technical correctness skills
- **Symptom:** With-skill and without-skill outputs have near-identical correctness, delta comes only from format/methodology.
- **Cause:** Base models (Claude, GPT-4) are already expert at SQL optimization, debugging, etc.
- **Affect:** Skills that teach well-known technical concepts show minimal value-add over baseline.
- **Fix:** For technical skills, design assertions targeting methodology/format rather than correctness. Accept that delta may be low and score accordingly. Consider if the skill is still useful as a "consistency enforcer" even with low delta.

### Marketing statistics in skill descriptions
- **Symptom:** Skill claims specific improvement numbers (7.8x faster, 85% reduction) without evidence.
- **Cause:** Skill authors include marketing claims as if they were validated metrics.
- **Fix:** Note unsubstantiated claims in skill cards. Do not use skill's self-reported metrics in scoring.

## v0.3.0 Additions (Full Re-Eval + Skill Improve, 2026-03-09)

### Reference manual anti-pattern
- **Symptom:** Skill has 200-400+ lines of SQL templates, code patterns, framework guides. Zero delta on assertions. Massive overhead.
- **Cause:** SKILL.md is educational content the model already knows, not behavioral guidance.
- **Affect:** Model reads the entire reference, burns tokens processing it, produces no better output.
- **Fix:** Replace reference content with behavioral mandates (MUST/ALWAYS/NEVER rules). Remove anything the base model already knows. Aim for <100 lines.

### Library-as-skill anti-pattern
- **Symptom:** SKILL.md contains a Python class definition or code library. Model tries to use the library, burns 100%+ more tokens producing unwanted artifacts.
- **Cause:** Skill author pasted their library code instead of writing usage instructions.
- **Affect:** Model generates documentation artifacts (JSON schemas, ER diagrams, validation reports) that nobody asked for.
- **Fix:** Replace code with instructions. Skills should describe WHAT to do, not provide code TO RUN.

### Assertion-skill mismatch after improvement
- **Symptom:** Improved skill produces visibly better output, but score doesn't change.
- **Cause:** Assertions test baseline capabilities (correctness), not skill-specific value (format, methodology).
- **Affect:** Improvement effort appears wasted even when skill genuinely improved.
- **Fix:** When improving a skill, also update assertions to test the new behavioral mandates.
