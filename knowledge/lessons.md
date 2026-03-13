# Evaluation Lessons Learned

This file accumulates wisdom from each evaluation cycle. skill-eval reads this before generating test cases and assertions to avoid repeating mistakes and apply proven patterns.

## Lessons from Explain-Code Eval (v0.2.0, 2026-03-06)

- Skills that define a specific OUTPUT FORMAT (analogy + diagram + walkthrough + gotchas) are easy to evaluate and show clear differentiation.
- Claude CAN produce analogies and diagrams, but doesn't default to them — this is exactly where capability uplift skills shine.
- Assertions that target skill-specific structural elements (does it have an analogy? does it have a diagram?) are excellent discriminators.
- A 50% pass rate delta (100% vs 50%) with only ~30% overhead in time/tokens is a strong signal of skill value.
- The with-skill output was also qualitatively richer (restaurant analogy, thundering herd, return-await subtlety) — rubric-based grading would capture even more delta.

## Bootstrapped Lessons (v0.1.0)

- Assertions that pass in both with-skill and without-skill runs are non-discriminating. They prove the task is doable, not that the skill helps. Always include at least one assertion that targets skill-specific behavior.
- CLI-wrapper skills often need API keys to show their full value. Check for required env vars before running evals.
- Time and token overhead matters. A skill that passes the same assertions but takes 3x longer is arguably worse than no skill.
- Subjective quality (writing style, design taste) can't be graded with binary assertions. Use rubric-based scoring or flag for human review.
- Test prompts should be realistic — the kind of thing a real user would type, not sanitized lab prompts.

## Lessons from General-User Batch (v0.2.0, 2026-03-06)

- Structured workflow skills for business operations (sales pipeline, social calendar, proposal writing) showed the clearest pass-rate uplift versus baseline.
- "Framework-heavy" skills can justify 50-90% time overhead if they consistently improve actionability and formatting for stakeholder handoff.
- Paid/API-gated skills should be explicitly labeled during registry intake; otherwise they pollute rankings with environment failures rather than skill-quality failures.
- Finance/data-fetch skills require a dependency matrix in pre-flight (API key, freshness source, fallback behavior). Missing market-data keys caused partial regressions despite good template design.
- Baseline models are already strong at generic writing; career/profile/copy skills need sharper, skill-specific assertions (ATS constraints, section schema, audience tuning) to prove value.

## Lessons from Batch 3 (v0.2.0, 2026-03-09)

### Banned-word assertions are perfect discriminators for style skills
- The article-writer skill defines a banned-word list (非常, 我觉得, 也许, etc.). The base model uses these words freely; the skill eliminates them. This produced 100% delta — the highest in any eval so far. **Takeaway:** Any style/writing skill with a banned-word list should always have a keyword_absent assertion on those words. It's deterministic, easy to verify, and maximally discriminating.

### Encoded-preference skills with highly specific conventions dominate
- article-writer achieved 10/10 — the first perfect score. Its conventions (numbered modules, golden sentences, "launch" endings, banned words) are so specific and so different from baseline that every assertion discriminates. This confirms: the more opinionated a style skill is, the easier it is to evaluate and the higher it scores.

### Base model already excels at technical analysis
- sql-query-optimizer and debug-checklist both showed that Claude already handles SQL optimization and C/C++ debugging at a very high level. The skills' value-add was purely structural (JSON output format, systematic checklist methodology), not correctness. **Takeaway:** For technical analysis skills, focus assertions on methodology/format, not correctness — the base model will get the content right anyway.

### Non-existent scripts are a skill quality signal
- review-summarizer references Python scripts that don't exist (scrape_reviews.py, etc.). Despite this, the framework/template it defines still produced 50% delta. **Takeaway:** Skills with phantom tooling can still add framework value, but this should be flagged in skill cards as a trust issue. A "phantom tooling" flag should be added to pre-flight.

### Capability-uplift skills for novel tools show maximum delta
- secure-api-calls teaches keychains, a tool the model has no prior knowledge of. Delta: 87.5%. This is expected — the model literally cannot produce the right answer without the skill. **Takeaway:** Capability-uplift skills for genuinely novel tools will always show high delta, but need dependency validation to prove operational value.

### Chinese-language skills need Chinese-aware assertions
- Both sql-query-optimizer and article-writer handle Chinese prompts. Assertions need to include Chinese keyword variants (索引/index, 前导通配符/leading wildcard) to avoid false negatives.

## Lessons from Full Re-Eval + Skill Improve (v0.3.0, 2026-03-09)

### Reference manuals are anti-skills
- data-analyst, data-model-designer, and test-runner all scored poorly because their SKILL.md files were reference manuals — SQL templates, pandas patterns, framework selection tables. The model already knows all of this. Pasting a reference manual into the context just burns tokens without changing behavior. **Takeaway:** If the content of a SKILL.md is things the model already knows (programming patterns, framework APIs, statistical methods), it adds zero value. Skills must encode PREFERENCES or PROCESSES the model wouldn't follow by default.

### Behavioral mandates > educational content
- Improved skills replaced reference content with behavioral mandates: "MUST include methodology section", "ALWAYS run tests after writing", "NEVER use SELECT *". These mandates change model behavior in measurable ways. **Takeaway:** Effective skills are contracts, not textbooks. Use imperatives (MUST, ALWAYS, NEVER), not descriptions.

### Overhead is the silent killer of skill scores
- All three low-scoring skills had massive overhead (83-155% time, 44-113% tokens) with zero quality delta. After improvement (slimming the SKILL.md by 60-80%), overhead dropped to 6-45% while behavioral quality improved. **Takeaway:** Skill file size directly correlates with overhead. Smaller, more focused skills are better. If your SKILL.md is over 100 lines, question every line.

### Assertion design determines evaluation ceiling
- Even after improvement, all three skills showed 0% delta on existing assertions because the assertions test correctness (baseline capability), not format/methodology (skill value). The improved skills DO produce better output (methodology sections, structured plans, test execution) but the assertions don't capture it. **Takeaway:** When improving skills, also update assertions to test the new behavioral mandates. Otherwise you're measuring the wrong thing.

### The improvement formula: Remove > Add
- For all three improved skills, the primary improvement was REMOVING content (60-80% reduction), not adding new instructions. Less context = less overhead = better efficiency score. Adding behavioral mandates was secondary. **Takeaway:** Start skill improvement by asking "what can I delete?" not "what can I add?"

### Python libraries are not skills
- data-model-designer's original SKILL.md was literally a Python class definition. The model read it, tried to instantiate the classes, and burned 113% more tokens producing documentation artifacts nobody asked for. **Takeaway:** SKILL.md should never contain library code. It should contain instructions for the model to follow. Code belongs in scripts/ if needed at all.
