# Evaluation Patterns

Reusable assertion templates and test case strategies by skill category.

## Categories

### CLI Wrapper Skills
- Check: does the skill actually invoke the CLI tool?
- Check: does it handle missing dependencies gracefully?
- Check: does the output differ meaningfully from what Claude does natively?
- Assertions: tool_called, output_quality_delta, error_handling

### Code Generation Skills
- Check: does generated code run without errors?
- Check: does it follow the skill's claimed patterns/frameworks?
- Assertions: code_executes, follows_pattern, test_passes

### Search/Retrieval Skills
- Check: does it find relevant results?
- Check: does it cite sources?
- Assertions: relevance, source_citation, no_hallucination

### Writing/Transform Skills
- Check: does output match requested format/style?
- Check: is quality measurably different from baseline?
- Assertions: format_compliance, style_match, quality_delta

### Workflow/Deploy Skills
- Check: does it produce the claimed artifacts?
- Check: does it follow the documented steps?
- Assertions: artifact_exists, steps_followed, config_valid

---

*This file grows as we learn which patterns work for which skill types.*

### Business Ops Skills (Sales / Marketing / Proposal)
- Check: does output include operating cadence (weekly actions, owners, next steps)?
- Check: are metrics/forecasts computed and tied to recommended actions?
- Assertions: cadence_present, metric_math_valid, actionability_score

### Dependency-Gated Paid Skills
- Check: can skill run without hidden billing/auth blockers?
- Check: does it fail gracefully with setup guidance?
- Assertions: dependency_preflight, graceful_degradation, baseline_fallback_delta

### UX/Design Review Skills
- Check: are findings mapped to a named heuristic framework?
- Check: does each issue include severity and remediation?
- Assertions: heuristic_mapping, severity_tagging, remediation_specificity

### Style/Writing Skills (Opinionated Format)
- Check: does output follow the specific structural convention (numbered modules, golden sentences, etc.)?
- Check: are banned words absent from the output?
- Check: does ending match prescribed style (e.g. "launch" vs "landing")?
- Assertions: structure_compliance, keyword_absent(banned_words), ending_style, quotable_sentences

### Technical Analysis Skills (SQL, Debug, Code Review)
- Check: does output follow a systematic methodology (checklist, JSON schema, step-by-step)?
- Check: is format consistent across different inputs?
- NOTE: do NOT assert on correctness -- base model already handles this. Assert on process/format only.
- Assertions: methodology_structure, format_consistency, actionability

### Novel Tool Skills (keychains, niche CLIs)
- Check: does output reference the correct tool syntax and workflow?
- Check: does it include approval/auth flow handling?
- Check: would the output actually work if the tool were installed?
- NOTE: high delta is expected since model has no prior knowledge. Flag as dependency-gated if tool unavailable.
- Assertions: correct_syntax, workflow_completeness, dependency_preflight

### Style/Writing Convention Skills (e.g. article-writer)
- Check: does output comply with banned-word lists? (keyword_absent assertion — most discriminating)
- Check: does output follow specific structural conventions? (numbered sections, module format)
- Check: are "golden sentences" / quotable phrases present?
- Check: does opening/ending follow prescribed patterns? (hook vs bland, launch vs landing)
- Assertions: banned_word_compliance, structural_format, quotable_content, opening_hook, ending_style
- **Key insight:** Banned-word assertions are deterministic, easy to verify, and achieve maximum discrimination. Always use them when available.

### Technical Analysis Skills (SQL, Debugging, Code Review)
- Check: does output use a systematic methodology? (checklist, categorized analysis)
- Check: does output include structured output format? (JSON, tables with severity)
- Check: does output cover ALL categories, not just obvious issues?
- Assertions: systematic_methodology, structured_output_format, comprehensive_coverage
- **Key insight:** Base model correctness is already high. Focus assertions on methodology and format, not on whether it finds the right answer.

### Overhead-Sensitive Skills (Reference Manual Pattern)
- Check: is the SKILL.md mostly reference content the model already knows?
- Check: does skill overhead exceed 50% with zero quality delta?
- Check: can the skill be reduced to <100 lines of behavioral mandates?
- Assertions: mandatory_section_present, behavioral_compliance, format_template_match
- **Key insight:** Skills that are reference manuals (SQL templates, framework guides, code patterns) add zero value over baseline but massive overhead. Convert to behavioral contracts: MUST/ALWAYS/NEVER rules with specific output format requirements. Assert on mandatory output sections, not correctness.

### Product Research / Review Framework Skills
- Check: does output include quantitative data? (sentiment scores, frequency counts, percentages)
- Check: does output follow a specific template structure? (Overview → Insights → Sentiment → Recommendation)
- Check: does output attribute data to specific platforms/sources?
- Assertions: quantitative_data_present, template_compliance, source_attribution
- **Key insight:** Framework skills with phantom tooling (non-existent scripts) should be flagged but can still add structural value.
