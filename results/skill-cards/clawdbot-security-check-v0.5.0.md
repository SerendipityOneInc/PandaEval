# Skill Card: Clawdbot Security Check

> Perform a comprehensive read-only security audit of Clawdbot's own configuration. This is a knowledge-based skill that teaches Clawdbot to identify hardening opportunities across the system. Use when user asks to "run security check", "audit clawdbot", "check security hardening", or "what vulnerabilities does my Clawdbot have". This skill uses Clawdbot's internal capabilities and file system access to inspect configuration, detect misconfigurations, and recommend remediations. It is designed to be extensible - new checks can be added by updating this skill's knowledge.

| Field | Value |
|-------|-------|
| **Skill** | Clawdbot Security Check |
| **Source** | [ClawHub](https://clawhub.ai/clawdbot-security-check) |
| **Domain** | git/github |
| **Type** | encoded_preference |
| **Eval Date** | 2026-03-13 |
| **Eval Engine** | skill-eval v0.5.0 |
| **Downloads** | 6957 |

---

## Overall Score: 8.0/10

**Verdict:** Recommended

**Flags:** `dependency-gated`

## Score Breakdown

| Component | Score | Max | Description |
|-----------|-------|-----|-------------|
| Structure | 1.5 | 2 | Clear sections, metadata, organization |
| Specificity | 2.0 | 2 | Concrete instructions, code examples |
| Examples | 1.0 | 2 | Usage examples, demos, samples |
| Scope | 1.5 | 2 | Appropriate size, well-bounded |
| Actionability | 2.0 | 2 | Agent can act immediately |
| **Total** | **8.0** | **10** | |

## Metrics

- **Word Count:** 2315
- **Line Count:** 647
- **Files in Package:** 5
- **Has Scripts:** No
- **Has References:** No

```json
{
  "slug": "clawdbot-security-check",
  "score": 8.0,
  "domain": "git/github",
  "type": "encoded_preference",
  "verdict": "Recommended",
  "flags": ["dependency-gated"],
  "downloads": 6957
}
```
