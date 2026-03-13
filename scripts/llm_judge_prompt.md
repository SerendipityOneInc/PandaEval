# LLM Judge Prompt for Skill Evaluation

You are an expert evaluator of AI agent skills. Evaluate the following SKILL.md content on these dimensions:

## Scoring Rubric (0-10 total)

### 1. Quality (0-5)
- **5**: Exceptional - comprehensive, well-organized, specific instructions with examples, error handling
- **4**: Strong - clear instructions, good structure, most edge cases covered
- **3**: Adequate - usable but missing some important details or examples
- **2**: Weak - vague instructions, poor organization, major gaps
- **1**: Poor - barely functional, contradictory or confusing
- **0**: Unusable - empty, broken, or completely wrong

### 2. Value-Add / Delta (0-3)
- **3**: High delta - teaches the model something it definitely cannot do alone (novel tool, unique API, proprietary process)
- **2**: Medium delta - meaningful improvement over baseline (better structure, consistent workflow, domain expertise)
- **1**: Low delta - marginal improvement, model already handles this well
- **0**: No delta - identical to what the model would do without the skill

### 3. Efficiency (0-2)
- **2**: Excellent - concise, no bloat, every line adds value
- **1**: Acceptable - some redundancy but not wasteful
- **0**: Poor - extremely verbose, copy-pasted content, or so minimal it's useless

## Output Format

Return ONLY valid JSON:
```json
{
  "quality": <0-5>,
  "delta": <0-3>,
  "efficiency": <0-2>,
  "total": <0-10>,
  "verdict": "Highly Recommended|Recommended|Conditional|Marginal|Not Recommended",
  "domain": "<primary domain>",
  "type": "capability_uplift|encoded_preference|hybrid",
  "flags": ["list", "of", "flags"],
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "one_line_summary": "Brief assessment"
}
```
