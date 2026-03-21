# Security Evaluation Module

`zooeval.security` provides automated security assessment for AI agent skills. It scans skill directories for threats using a four-layer pipeline and produces a verdict with a 0-10 score.

## Architecture

```
Skill Directory
      │
      ├─► Layer 1: Heuristic Scan ── regex pattern matching (5 threat categories)
      ├─► Layer 2: AST Scan ──────── Python abstract syntax tree analysis
      ├─► Layer 3: LLM Intent ────── semantic classification via LLM API
      │
      └─► Layer 4: Verdict Engine ── cross-validates all signals → verdict + score
```

Neither layer alone determines the outcome — the verdict engine requires corroboration across layers.

## Quick Start

```python
from zooeval.security import scan_skill

result = scan_skill("/path/to/skill-dir")

print(result["verdict"])        # "safe" | "caution" | "unsafe"
print(result["security_score"]) # 0-10
print(result["notes"])          # human-readable explanation
```

## Configuration

The module uses **zero external dependencies** (stdlib only). LLM intent analysis requires an API key:

| Environment Variable | Provider | Notes |
|---------------------|----------|-------|
| `ANTHROPIC_API_KEY` | Anthropic (Claude) | Preferred, uses `claude-sonnet-4-20250514` by default |
| `OPENAI_API_KEY` | OpenAI / compatible | Uses `gpt-4o` by default |
| `OPENAI_BASE_URL` | Custom endpoint | For OpenAI-compatible APIs |
| `LLM_DEFAULT_MODEL` | Any | Override default model name |

If no API key is set, the module **gracefully degrades** — runs heuristic + AST scans only, skips LLM intent analysis.

## API

### `scan_skill(skill_dir, llm_client=None, timeout=60)`

Main entry point. Runs all four layers and returns a combined result.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `skill_dir` | `str \| Path` | required | Path to skill directory (should contain `SKILL.md`) |
| `llm_client` | `LLMClient` | `None` | Custom LLM client instance. If `None`, auto-creates from env |
| `timeout` | `int` | `60` | LLM request timeout in seconds |

**Returns:** `dict`

```python
{
    "verdict": "safe",           # "safe" | "caution" | "unsafe"
    "security_score": 10,        # 0 (dangerous) to 10 (clean)
    "heuristic": { ... },        # heuristic scan details
    "ast": { ... },              # AST scan details
    "intent": { ... },           # LLM intent analysis details
    "notes": [ ... ],            # list of human-readable explanation strings
}
```

## Verdict Logic

The verdict engine uses a priority-ordered rule chain:

| Priority | Condition | Verdict | Score |
|----------|-----------|---------|-------|
| 1 | LLM says malicious (confidence >= 0.7) | `unsafe` | 1 |
| 2 | Heuristic score < 3 | `unsafe` | heuristic score |
| 3 | Heuristic flags + LLM confirms threat | `unsafe` | 1-4 |
| 4 | Heuristic flags + LLM says safe | `caution` | 6-8 |
| 5 | No flags + LLM says suspicious | `caution` | 6 |
| 6 | No flags + LLM says malicious (low conf) | `caution` | 5 |
| 7 | LLM skipped, heuristic only | varies | capped by risk level |
| 8 | Both clean | `safe` | 10 |

## Threat Categories

The heuristic scanner detects patterns in 5 categories:

| Category | Examples | Weight |
|----------|----------|--------|
| `destructive` | `rm -rf /`, `DROP TABLE`, `dd if=`, fork bomb | 3 pts/hit, max 6 |
| `exfiltration` | `curl POST`, Discord/Slack webhooks, netcat | 2 pts/hit, max 4 |
| `credential` | SSH key read, AWS credentials access, `.env` read | 2 pts/hit, max 4 |
| `obfuscation` | `eval(base64...)`, `exec(decode...)`, hex+eval | 3 pts/hit, max 6 |
| `supply_chain` | `curl \| bash`, non-PyPI pip index, privileged docker | 2 pts/hit, max 4 |

The AST scanner additionally detects Python-specific threats:
- `eval()` / `exec()` / `compile()` with dynamic arguments
- `__import__()` calls
- `getattr()` on builtins
- `os.system()` / `subprocess.run()` with dynamic input
- Suspicious imports (`ctypes`, `code`, `codeop`)

## No-LLM Mode

When no API key is configured:

- Heuristic + AST scans run normally
- Intent analysis returns `{"status": "skipped"}`
- Verdict engine relies on heuristic score only
- High-risk findings (credential, exfiltration, destructive, AST dangerous calls) cap the verdict at `caution` — cannot reach `safe` without LLM corroboration

```python
import os
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)

result = scan_skill("/path/to/skill")
# result["intent"]["status"] == "skipped"
# verdict is heuristic-only
```

## Example Output

### Safe Skill

```python
>>> scan_skill("skills/hello-world/")
{
    "verdict": "safe",
    "security_score": 10,
    "notes": [
        "No heuristic threat patterns detected",
        "[intent] safe (confidence: 0.95)",
        "[intent:reasoning] Simple greeting skill with no security concerns"
    ],
    ...
}
```

### Unsafe Skill

```python
>>> scan_skill("skills/data-exfil/")
{
    "verdict": "unsafe",
    "security_score": 2,
    "notes": [
        "[destructive:1] rm -rf / at SKILL.md",
        "[exfiltration:1] curl POST to external URL at scripts/clean.sh",
        "[credential:1] AWS credentials read at scripts/clean.sh",
        "[intent] malicious (confidence: 0.92)",
        "[intent:reasoning] Skill exfiltrates credentials and destroys files",
        "HARD REJECT: LLM classified as malicious with high confidence"
    ],
    ...
}
```

## Using a Custom LLM Client

```python
from zooeval.security import scan_skill
from zooeval.security.client import LLMClient

client = LLMClient(
    provider="openai",
    model="gpt-4o",
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
)

result = scan_skill("skills/my-skill/", llm_client=client)
```
