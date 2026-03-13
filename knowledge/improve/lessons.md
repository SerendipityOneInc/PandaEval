# Skill Improvement Engine -- Lessons Learned

Accumulated wisdom from skill improvement attempts. Read before every improvement to avoid repeating mistakes.

---

## Batch 1 Improvements (v0.3.0, 2026-03-09)

### Remove > Add is the primary lever
- All 3 improved skills (data-analyst, data-model-designer, test-runner) gained score primarily through content REMOVAL, not addition.
- Deleting 60-80% of reference content reduced overhead dramatically (e.g., +155% -> +45% time).
- Adding behavioral mandates was secondary but important for quality signal.
- **Lesson:** Always start improvement by asking "what can I delete?" not "what can I add?"

### Behavioral mandates change model behavior; reference content does not
- MUST/ALWAYS/NEVER rules produce measurable output differences.
- Educational content (SQL templates, framework guides, API docs) produces zero behavior change -- the model already knows this.
- **Lesson:** Replace every paragraph of education with one line of instruction.

### Overhead is the silent killer
- Skills with massive overhead (83-155% time, 44-113% tokens) and zero delta get punished hard in scoring.
- After improvement (slimming by 60-80%), overhead dropped to 6-45% while behavioral quality improved.
- **Lesson:** Skill file size directly correlates with overhead. Smaller = better.

### Assertion updates are required for improvement to register
- All 3 improved skills initially showed 0% delta on original assertions despite visibly better output.
- Original assertions tested correctness (baseline capability), not format/methodology (skill value).
- **Lesson:** When improving a skill, ALWAYS update assertions to test the new behavioral mandates.

### Python libraries are not skills
- data-model-designer contained a Python class definition. Model tried to instantiate it, burned 113% extra tokens.
- **Lesson:** SKILL.md should never contain library code. Instructions only.

---

*Updated after each improvement cycle. This file drives Phase 10 strategy selection.*
