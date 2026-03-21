"""Security evaluation module for ZooEval.

Four-layer skill security assessment:
  1. Heuristic scan — regex pattern matching for known threat categories
  2. AST scan — Python abstract syntax tree analysis for obfuscated threats
  3. LLM intent analysis — semantic classification of skill purpose
  4. Verdict engine — cross-validates all signals

Usage:
    from zooeval.security import scan_skill
    result = scan_skill("/path/to/skill-dir")
    print(result["verdict"])       # "safe" | "caution" | "unsafe"
    print(result["security_score"])  # 0-10
"""

from .ast_scanner import ast_scan
from .heuristic import heuristic_scan
from .intent_analyzer import analyze_intent
from .verdict import determine_verdict


def scan_skill(skill_dir, llm_client=None, timeout=60):
    """Run full security evaluation on a skill directory.

    Args:
        skill_dir: Path to skill directory (must contain SKILL.md).
        llm_client: Optional LLMClient instance. If None, auto-creates from env.
        timeout: LLM request timeout in seconds.

    Returns:
        dict with keys:
            verdict: "safe" | "caution" | "unsafe"
            security_score: int 0-10
            heuristic: dict from heuristic_scan()
            ast: dict from ast_scan()
            intent: dict from analyze_intent()
            notes: list of human-readable notes
    """
    heuristic_result = heuristic_scan(skill_dir)

    # Merge AST findings into heuristic result so verdict engine sees them
    ast_result = ast_scan(skill_dir)
    if ast_result["findings"]:
        heuristic_result["findings"].extend(ast_result["findings"])
        heuristic_result["notes"].extend(ast_result["notes"])
        # Deduct from heuristic score: 2 points per AST finding, max 6
        ast_deduction = min(6, len(ast_result["findings"]) * 2)
        heuristic_result["score"] = max(0, heuristic_result["score"] - ast_deduction)
        heuristic_result["category_scores"]["ast"] = ast_deduction

    intent_result = analyze_intent(skill_dir, client=llm_client, timeout=timeout)
    verdict_result = determine_verdict(heuristic_result, intent_result)
    verdict_result["ast"] = ast_result
    return verdict_result
