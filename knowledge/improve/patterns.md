# Skill Improvement Engine -- Proven Patterns

Reusable improvement strategies organized by root cause. Match the diagnosed problem to a pattern, apply the strategy.

---

## Pattern: Reference Manual Slim-Down

**Root Cause:** SKILL.md is 200+ lines of educational content the model already knows.
**Category:** Overhead-sensitive, Technical analysis, Code generation
**Strategy:**
1. Delete all reference content (code templates, API docs, framework guides, pattern libraries)
2. Keep only: trigger conditions, output format requirements, behavioral mandates
3. Add 5-10 MUST/ALWAYS/NEVER rules that encode the skill's unique value
4. Target: <100 lines total
**Expected Gain:** +1.5 to +2.0 points
**Success Rate:** 3/3 (100%)
**Examples:** data-analyst (5.0 -> 7.0), test-runner (5.5 -> 7.0)

## Pattern: Library-to-Instructions

**Root Cause:** SKILL.md contains Python/JS class definitions or library code.
**Category:** Code generation, Data modeling
**Strategy:**
1. Delete all code definitions (classes, functions, imports)
2. Write behavioral instructions: "When asked to do X, produce output in format Y"
3. Specify output schema as a template, not as code
4. Add explicit prohibitions for common model artifacts (don't generate ER diagrams unless asked, etc.)
**Expected Gain:** +1.5 points
**Success Rate:** 1/1 (100%)
**Examples:** data-model-designer (5.5 -> 7.0)

## Pattern: Phantom Tooling Replacement

**Root Cause:** SKILL.md references scripts/CLIs that don't exist.
**Category:** Any skill with phantom tooling flag
**Strategy:**
1. Replace script references with inline instructions
2. Convert "run scrape_reviews.py" to "gather review data from [sources] and structure as..."
3. Keep the framework/template value, remove the false tooling promises
4. Add honest capability disclosure
**Expected Gain:** TBD (not yet tested in improvement cycle)
**Success Rate:** Untested
**Examples:** Candidate: review-summarizer, tugou-monitor

## Pattern: Overhead Routing

**Root Cause:** Skill adds valuable structure but costs 2-3x more in tokens/time.
**Category:** Framework-heavy, Business ops
**Strategy:**
1. Add "quick mode" vs "full framework" routing in SKILL.md
2. Quick mode: answer directly with key structural elements only
3. Full mode: complete framework with all sections
4. Default to quick mode unless user explicitly asks for full analysis
**Expected Gain:** TBD (not yet tested)
**Success Rate:** Untested
**Examples:** Candidate: marketing-mode, ai-presentation-maker

## Pattern: Assertion-Aligned Rewrite

**Root Cause:** Skill has good ideas but doesn't express them as testable mandates.
**Category:** Any low-delta skill
**Strategy:**
1. Identify what the skill SHOULD add (from its description/intent)
2. Convert each intended behavior into a MUST rule
3. Add corresponding assertions to test each mandate
4. This ensures the improvement is measurable, not just vibes
**Expected Gain:** Depends on base quality
**Success Rate:** Implicit in all successful improvements
**Examples:** All improved skills used this as a secondary pattern

---

*Updated after each improvement cycle. Add new patterns when strategies succeed, update success rates, remove patterns that consistently fail.*
