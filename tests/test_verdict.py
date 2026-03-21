"""Tests for security.verdict module."""

from zooeval.security.verdict import determine_verdict, _compute_heuristic_score, _compute_intent_score


def _heuristic(score=10, findings=None, notes=None):
    return {
        "score": score,
        "findings": findings or [],
        "category_scores": {},
        "notes": notes or [],
    }


def _intent(status="ok", intent="safe", confidence=0.9, reasoning="", flags=None):
    d = {"status": status, "intent": intent, "confidence": confidence,
         "reasoning": reasoning, "flags": flags or []}
    if status == "skipped":
        d = {"status": "skipped", "reason": "no key"}
    return d


class TestComputeHeuristicScore:
    def test_normal(self):
        assert _compute_heuristic_score({"score": 7}) == 7

    def test_clamp_low(self):
        assert _compute_heuristic_score({"score": -3}) == 0

    def test_clamp_high(self):
        assert _compute_heuristic_score({"score": 15}) == 10

    def test_missing_key(self):
        assert _compute_heuristic_score({}) == 5


class TestComputeIntentScore:
    def test_safe_high_confidence(self):
        assert _compute_intent_score(_intent(intent="safe", confidence=1.0)) == 10

    def test_malicious_high_confidence(self):
        assert _compute_intent_score(_intent(intent="malicious", confidence=1.0)) == 1

    def test_safe_low_confidence(self):
        # base=10, conf=0.0 → 10*0 + 5*1 = 5
        assert _compute_intent_score(_intent(intent="safe", confidence=0.0)) == 5

    def test_skipped(self):
        assert _compute_intent_score({"status": "skipped"}) == 5

    def test_educational(self):
        score = _compute_intent_score(_intent(intent="educational", confidence=1.0))
        assert score == 8

    def test_suspicious_mid_confidence(self):
        # base=4, conf=0.5 → 4*0.5 + 5*0.5 = 2+2.5 = 4.5 → 4
        score = _compute_intent_score(_intent(intent="suspicious", confidence=0.5))
        assert score == 4


class TestDetermineVerdict:
    def test_rule1_hard_reject_malicious_high_conf(self):
        """Intent=malicious + confidence>=0.7 → unsafe, score=1."""
        result = determine_verdict(
            _heuristic(score=10),
            _intent(intent="malicious", confidence=0.9)
        )
        assert result["verdict"] == "unsafe"
        assert result["security_score"] == 1
        assert any("HARD REJECT" in n for n in result["notes"])

    def test_rule2_hard_reject_low_heuristic(self):
        """Heuristic score < 3 → unsafe."""
        result = determine_verdict(
            _heuristic(score=2, findings=[{"category": "destructive", "pattern": "rm -rf"}]),
            _intent(intent="safe", confidence=0.9)
        )
        assert result["verdict"] == "unsafe"
        assert result["security_score"] == 2

    def test_rule3_corroborated_threat(self):
        """Heuristic findings + intent suspicious → unsafe."""
        result = determine_verdict(
            _heuristic(score=6, findings=[{"category": "exfil", "pattern": "curl"}]),
            _intent(intent="suspicious", confidence=0.7)
        )
        assert result["verdict"] == "unsafe"
        assert 1 <= result["security_score"] <= 4

    def test_rule4_findings_with_safe_intent(self):
        """Heuristic findings + intent safe → caution (not override to safe)."""
        result = determine_verdict(
            _heuristic(score=6, findings=[{"category": "exfil", "pattern": "curl"}]),
            _intent(intent="safe", confidence=0.9)
        )
        assert result["verdict"] == "caution"
        assert 6 <= result["security_score"] <= 8
        assert any("human review" in n for n in result["notes"])

    def test_rule5_suspicious_no_findings(self):
        """No findings + intent suspicious → caution."""
        result = determine_verdict(
            _heuristic(score=10),
            _intent(intent="suspicious", confidence=0.6)
        )
        assert result["verdict"] == "caution"
        assert result["security_score"] == 6

    def test_rule6_malicious_low_conf_no_findings(self):
        """No findings + intent malicious low confidence → caution."""
        result = determine_verdict(
            _heuristic(score=10),
            _intent(intent="malicious", confidence=0.5)
        )
        assert result["verdict"] == "caution"
        assert result["security_score"] == 5

    def test_rule7_skipped_safe(self):
        """Intent skipped + high heuristic → safe."""
        result = determine_verdict(
            _heuristic(score=9),
            _intent(status="skipped")
        )
        assert result["verdict"] == "safe"

    def test_rule7_skipped_caution(self):
        """Intent skipped + mid heuristic → caution."""
        result = determine_verdict(
            _heuristic(score=6),
            _intent(status="skipped")
        )
        assert result["verdict"] == "caution"

    def test_rule7_skipped_unsafe(self):
        """Intent skipped + low heuristic → unsafe."""
        result = determine_verdict(
            _heuristic(score=3, findings=[{"category": "x", "pattern": "y"}]),
            _intent(status="skipped")
        )
        assert result["verdict"] == "unsafe"

    def test_rule8_both_clean(self):
        """High heuristic + safe intent → safe, score=10."""
        result = determine_verdict(
            _heuristic(score=10),
            _intent(intent="safe", confidence=0.9)
        )
        assert result["verdict"] == "safe"
        assert result["security_score"] == 10

    def test_rule8_educational(self):
        """High heuristic + educational intent → safe."""
        result = determine_verdict(
            _heuristic(score=9),
            _intent(intent="educational", confidence=0.8)
        )
        assert result["verdict"] == "safe"

    def test_result_structure(self):
        result = determine_verdict(_heuristic(), _intent())
        assert "verdict" in result
        assert "security_score" in result
        assert "heuristic" in result
        assert "intent" in result
        assert "notes" in result
        assert 0 <= result["security_score"] <= 10

    def test_score_clamped(self):
        """Score should always be 0-10."""
        result = determine_verdict(
            _heuristic(score=0, findings=[{"category": "x", "pattern": "y"}]),
            _intent(intent="malicious", confidence=0.99)
        )
        assert 0 <= result["security_score"] <= 10
