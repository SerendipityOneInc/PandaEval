# Skill Improvement Engine -- Failure Modes

Cases where improvement was attempted but didn't produce meaningful gains. Learn from these to avoid wasting compute.

---

## Known Failure Mode: Assertion-Skill Mismatch

**Symptom:** Improved skill produces visibly better output, but score doesn't change.
**Root Cause:** Assertions test baseline capabilities (correctness), not skill-specific value (format/methodology).
**Resolution:** Always update assertions when improving a skill. If you only rewrite the SKILL.md but keep the old assertions, you're measuring the wrong thing.
**Frequency:** Hit on all 3 initial improvements (before we learned to update assertions alongside)

## Known Dead End: Improving Dependency-Gated Skills

**Symptom:** Skill fails because API key / paid service is missing, not because skill is bad.
**Root Cause:** Environment problem, not skill quality problem.
**Resolution:** Do not attempt improvement. Mark as `dependency-gated` and move on. Re-evaluate after credentials are provisioned.
**Examples:** bio-generator-pay, hashtag-generator-pay, finance-lite

## Known Dead End: Skills Where Baseline is Strictly Better

**Symptom:** Baseline pass rate > with-skill pass rate. Skill actively hurts.
**Root Cause:** The skill's instructions conflict with the model's better judgment, or inject confusion.
**Resolution:** Some skills are just bad ideas. Document why and don't waste improvement cycles.
**Examples:** Candidates -- any skill with negative delta AND no dependency issues

---

*Updated after each improvement cycle. Add failed improvement attempts with root cause analysis.*
