"""Cross-validation verdict engine.

Combines heuristic scan results with LLM intent analysis to produce
a final security verdict. Key principle: neither layer alone determines
the outcome — they must corroborate each other.

Verdict matrix:
  heuristic clean + intent safe       → safe (score 10)
  heuristic flags + intent safe       → caution (needs human review, score 6-8)
  heuristic clean + intent suspicious → caution (score 6)
  heuristic flags + intent suspicious → unsafe (corroborated threat)
  any + intent malicious (high conf)  → unsafe (hard reject)
  heuristic score < 3                 → unsafe (overwhelming pattern evidence)
"""

_HIGH_RISK_CATEGORIES = {"credential", "exfiltration", "destructive", "ast_dangerous_call"}


def _compute_heuristic_score(heuristic_result):
    """Normalize heuristic score to 0-10."""
    return max(0, min(10, heuristic_result.get("score", 5)))


def _compute_intent_score(intent_result):
    """Convert intent classification to a numeric score."""
    if intent_result.get("status") == "skipped":
        return 5  # unknown = neutral

    intent = intent_result.get("intent", "suspicious")
    confidence = intent_result.get("confidence", 0.5)

    scores = {
        "safe": 10,
        "educational": 8,
        "suspicious": 4,
        "malicious": 1,
    }
    base = scores.get(intent, 4)
    # Scale toward neutral (5) when confidence is low
    return round(base * confidence + 5 * (1 - confidence))


def determine_verdict(heuristic_result, intent_result):
    """Determine final security verdict from heuristic + intent signals.

    Args:
        heuristic_result: dict from heuristic_scan()
        intent_result: dict from analyze_intent()

    Returns:
        dict with keys:
            verdict: "safe" | "caution" | "unsafe"
            security_score: int 0-10
            heuristic: the input heuristic_result
            intent: the input intent_result
            notes: list of human-readable explanation notes
    """
    h_score = _compute_heuristic_score(heuristic_result)
    findings = heuristic_result.get("findings", [])
    h_notes = heuristic_result.get("notes", [])

    intent_status = intent_result.get("status", "skipped")
    intent_label = intent_result.get("intent", "suspicious") if intent_status == "ok" else "unknown"
    intent_conf = intent_result.get("confidence", 0.5) if intent_status == "ok" else 0.0
    intent_flags = intent_result.get("flags", [])

    notes = list(h_notes)
    if intent_status == "ok":
        notes.append(f"[intent] {intent_label} (confidence: {intent_conf})")
        if intent_result.get("reasoning"):
            notes.append(f"[intent:reasoning] {intent_result['reasoning']}")
    else:
        notes.append(f"[intent] skipped: {intent_result.get('reason', 'unknown')}")

    # --- Verdict logic: cross-validation ---

    # 1. Hard reject: LLM says malicious with high confidence
    if intent_label == "malicious" and intent_conf >= 0.7:
        return _result("unsafe", 1, heuristic_result, intent_result,
                        notes + ["HARD REJECT: LLM classified as malicious with high confidence"])

    # 2. Hard reject: overwhelming heuristic evidence
    if h_score < 3:
        return _result("unsafe", h_score, heuristic_result, intent_result,
                        notes + [f"HARD REJECT: heuristic score {h_score} < 3 (too many threat patterns)"])

    # 3. Corroborated threat: heuristic flags + intent confirms danger
    if findings and intent_label in ("malicious", "suspicious"):
        score = max(1, min(4, h_score))
        return _result("unsafe", score, heuristic_result, intent_result,
                        notes + ["Corroborated: heuristic findings + intent confirms threat"])

    # 4. Heuristic flags but intent says safe → downgrade to caution, not override
    #    Heuristic evidence should not be dismissed by LLM alone; requires human review.
    if findings and intent_label == "safe":
        score = max(6, min(8, h_score))
        return _result("caution", score, heuristic_result, intent_result,
                        notes + ["Heuristic flags detected; intent=safe may be false negative — needs human review"])

    # 5. No heuristic flags but intent is suspicious
    if not findings and intent_label == "suspicious":
        return _result("caution", 6, heuristic_result, intent_result,
                        notes + ["No heuristic flags but LLM flagged as suspicious"])

    # 6. No heuristic flags but intent is malicious (low confidence)
    if not findings and intent_label == "malicious" and intent_conf < 0.7:
        return _result("caution", 5, heuristic_result, intent_result,
                        notes + ["No heuristic flags but LLM flagged malicious (low confidence)"])

    # 7. Intent analysis was skipped — rely on heuristic only
    #    With no LLM corroboration, any high-risk finding caps verdict at caution.
    if intent_status == "skipped":
        has_high_risk = any(
            f.get("category") in _HIGH_RISK_CATEGORIES for f in findings
        )
        if has_high_risk:
            # Cannot confirm safe without LLM — cap at caution
            verdict = "caution"
            capped_score = min(h_score, 7)
            return _result(verdict, capped_score, heuristic_result, intent_result,
                            notes + [f"Intent analysis skipped; high-risk findings present — capped at caution (score={capped_score})"])
        if h_score >= 8:
            verdict = "safe"
        elif h_score >= 5:
            verdict = "caution"
        else:
            verdict = "unsafe"
        return _result(verdict, h_score, heuristic_result, intent_result,
                        notes + [f"Intent analysis skipped; verdict based on heuristic only (score={h_score})"])

    # 8. Default: both clean
    if h_score >= 8 and intent_label in ("safe", "educational"):
        return _result("safe", 10, heuristic_result, intent_result, notes)

    # 9. Fallback
    combined = round((h_score + _compute_intent_score(intent_result)) / 2)
    if combined >= 7:
        verdict = "safe"
    elif combined >= 5:
        verdict = "caution"
    else:
        verdict = "unsafe"
    return _result(verdict, combined, heuristic_result, intent_result, notes)


def _result(verdict, score, heuristic, intent, notes):
    return {
        "verdict": verdict,
        "security_score": max(0, min(10, score)),
        "heuristic": heuristic,
        "intent": intent,
        "notes": notes,
    }
