# ZooEval: A Self-Evolving Framework for Evaluating and Improving AI Agent Skills

ZooEval is a self-evolving evaluation engine that blind-tests AI agent skills by running each task twice -- with and without the skill -- and grading outputs against deterministic assertions and LLM-as-judge rubrics. It maintains two closed feedback loops: one that sharpens its own evaluation methodology, and one that automatically rewrites underperforming skills. We evaluated **123 skills** from the ClawHub marketplace -- **76.4% measurably improve model output**, and the engine discovered that *removing* 60-80% of a skill's content outperforms adding to it.

<p align="center">
  <a href="#evaluate-your-own-skills">Quick Start</a> &bull;
  <a href="methodology/SKILL-EVAL.md">Methodology</a> &bull;
  <a href="https://zooclaw.ai/eval">Leaderboard</a> &bull;
  <a href="docs/security.md">Security Scan</a> &bull;
  <a href="paper/ZooEval.pdf">Paper</a> &bull;
  <a href="knowledge/">Knowledge Base</a>
</p>

[![Skills Evaluated](https://img.shields.io/badge/skills%20evaluated-123-blue)](results/skill-cards/)
[![Recommended](https://img.shields.io/badge/recommended-76.4%25-green)](results/leaderboard/)
[![Engine Version](https://img.shields.io/badge/engine-v0.4.0-orange)](methodology/SKILL-EVAL.md)

---

## Key Findings

- **76.4% of skills measurably improve model output** over the baseline (no skill)
- **Only 4% are actively harmful** -- causing worse results than the model alone
- **The #1 improvement strategy is Remove > Add** -- deleting 60-80% of a skill's content outperforms adding to it
- **The evaluation engine itself evolved** from 7 phases (v0.1.0) to 12 phases (v0.4.0), catching failure modes each prior version missed
- **8 failure modes discovered**, including phantom tooling (43% prevalence), reference manual bloat (21%), and template compliance drift

---

## Top 10 Skills

| Rank | Skill | Score | Delta |
|------|-------|-------|-------|
| 1 | Explain Code | 10.0 | +50% |
| 2 | BookNotes | 9.6 | +88% |
| 3 | Self-Improving with Reflection | 9.5 | +100% |
| 4 | EasyDoc Parse | 9.5 | +100% |
| 5 | BusAPI Agent Marketplace | 9.5 | +100% |
| 6 | Binance Web3 API | 9.5 | +100% |
| 7 | Article Writer (Chinese Viral) | 9.5 | +100% |
| 8 | KU Portal | 9.5 | +100% |
| 9 | Scan to Skill | 9.5 | +100% |
| 10 | GitVerse | 9.5 | +100% |

---

## Evaluate Your Own Skills

Clone the repo, then tell [OpenClaw](https://github.com/openclaw/openclaw) or any other AI agent what to evaluate. ZooEval is not a software tool -- it's a **methodology that any AI agent can follow**.



Just copy and paste the following prompts into your [OpenClaw](https://github.com/openclaw/openclaw):

### Case 1: Evaluate a skill from ClawHub

```
Clone https://github.com/SerendipityOneInc/ZooEval.git and read methodology/SKILL-EVAL.md,
then evaluate the ClawHub skill "explain-code".
Download it from ClawHub first, then run the full evaluation.
```

### Case 2: Evaluate a skill you already have installed

> Replace the skill path below with your actual skill location before copying.

```
Clone https://github.com/SerendipityOneInc/ZooEval.git and read methodology/SKILL-EVAL.md,
then evaluate the skill at ~/.agents/skills/my-skill/SKILL.md
```

### Case 3: Batch evaluate all skills in a directory

> Replace the directory path below with your actual skills folder before copying.

```
Clone https://github.com/SerendipityOneInc/ZooEval.git and read methodology/SKILL-EVAL.md,
then evaluate all skills under ~/.agents/skills/
Process them one by one, generate a score card for each, and build a leaderboard.
```

That's it. The agent reads the methodology, generates test cases, runs blind A/B tests, grades the outputs, and produces a score card.

---

## Browse Existing Results

### I want to pick good skills
Browse the [Leaderboard](results/leaderboard/index.html) or read individual [Skill Cards](results/skill-cards/). Each card includes score, strengths, weaknesses, and a recommendation.

### I want to improve my skill
Read the [Improvement Patterns](knowledge/improve/patterns.md) -- proven strategies that raised scores by 1.5-2.0 points. Also check the [Failure Modes](knowledge/failures.md) to avoid common anti-patterns.

**The core insight:** Skills should be behavioral contracts, not textbooks. Use MUST/ALWAYS/NEVER mandates. Delete reference content the model already knows.

---

## Key Discovery: The Remove > Add Principle

The most counterintuitive finding: **removing content from underperforming skills works better than adding content.**

Skills that scored poorly were typically 200+ lines of educational content the model already knows. The proven improvement formula:

1. **Delete 60-80%** of reference/tutorial content
2. **Add 5-10 behavioral mandates** (MUST/ALWAYS/NEVER rules)
3. **Keep output format specs** and trigger conditions
4. **Target < 100 lines**

This strategy successfully improved 3/3 tested skills by +1.5 to +2.0 points. See [Improvement Patterns](knowledge/improve/patterns.md) for the full playbook.

---

## Failure Mode Taxonomy

| # | Failure Mode | Prevalence | Example |
|---|-------------|-----------|---------|
| 1 | Dependency gate hard-fail | Common | Paid API skills crash without keys |
| 2 | Phantom tooling | 43% | SKILL.md references scripts that don't exist |
| 3 | Reference manual anti-pattern | 21% | 200+ lines of tutorials = pure overhead |
| 4 | Library-as-skill | Rare | Python classes in SKILL.md |
| 5 | Baseline already strong | Common | Model already excels at the domain |
| 6 | Template compliance drift | Medium | Error paths bypass required formatting |
| 7 | Marketing claims without evidence | Medium | "7.8x faster" with no data |
| 8 | Assertion-skill mismatch | Medium | Assertions test wrong things |

---

## Methodology

ZooEval uses **blind A/B testing**: every task runs twice on the same model -- once with the skill, once without. Outputs are graded against deterministic assertions (file checks, keyword matching) and LLM-as-judge rubrics.

The engine has **two self-evolving loops**:
- **Evaluation loop**: evaluate → learn → improve methodology → better evaluations
- **Improvement loop**: improve skill → re-evaluate → learn what worked → better improvements

See [SKILL-EVAL.md](methodology/SKILL-EVAL.md) for the full 12-phase specification.

---

## Repo Structure

```
ZooEval/
├── README.md                        # This file
├── zooeval/                       # Core Python package
│   └── security/                    # Security evaluation module (docs/security.md)
├── paper/
│   ├── ZooEval.pdf               # Research paper
│   └── ZooEval.tex               # LaTeX source
├── methodology/
│   ├── SKILL-EVAL.md                # Self-evolving eval engine spec
│   └── VERSION                      # Engine version
├── docs/
│   └── security.md                  # Security scan usage guide
├── knowledge/                       # Accumulated eval wisdom
│   ├── lessons.md                   # What worked, what didn't
│   ├── eval-patterns.md             # Reusable assertion templates
│   ├── failures.md                  # Failure mode catalog
│   └── improve/                     # Skill improvement engine knowledge
│       ├── patterns.md              # Proven improvement strategies
│       ├── lessons.md               # Improvement-specific lessons
│       └── failures.md              # What NOT to try
├── results/
│   ├── leaderboard/index.html       # Interactive HTML leaderboard
│   └── skill-cards/                 # 415 individual eval reports
├── tests/                           # Unit & integration tests
└── scripts/                         # Card & leaderboard generators
    ├── generate_skill_card.py
    ├── generate_leaderboard.py
    └── llm_judge_prompt.md
```

---

## Citation

```bibtex
@article{wang2026zooeval,
  title={ZooEval: A Self-Evolving Framework for Evaluating and Improving AI Agent Skills},
  author={Wang, Ji and Li, Xiaopu and Xu, Wenhao and Hu, Ning},
  year={2026},
  institution={Serendipity One Inc.}
}
```

---

## License

Apache License 2.0 -- see [LICENSE](LICENSE) for details.

---

*Built with [ZooEval](methodology/SKILL-EVAL.md) v0.4.0 | Evaluated on Claude Opus 4 | March 2026*
