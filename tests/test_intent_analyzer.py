"""Tests for security.intent_analyzer module."""

from unittest.mock import patch, MagicMock

from zooeval.security.intent_analyzer import _parse_response, _read_skill_content, analyze_intent
from zooeval.security.client import LLMResponse


class TestParseResponse:
    def test_valid_json(self):
        raw = '{"intent": "safe", "confidence": 0.95, "reasoning": "Normal tool", "flags": []}'
        result = _parse_response(raw)
        assert result["status"] == "ok"
        assert result["intent"] == "safe"
        assert result["confidence"] == 0.95
        assert result["reasoning"] == "Normal tool"
        assert result["flags"] == []

    def test_json_in_text(self):
        raw = 'Here is my analysis:\n{"intent": "malicious", "confidence": 0.8, "reasoning": "Bad", "flags": ["exfil"]}\nEnd.'
        result = _parse_response(raw)
        assert result["intent"] == "malicious"
        assert result["confidence"] == 0.8

    def test_invalid_intent_defaults_to_suspicious(self):
        raw = '{"intent": "unknown_value", "confidence": 0.5}'
        result = _parse_response(raw)
        assert result["intent"] == "suspicious"

    def test_invalid_confidence_defaults(self):
        raw = '{"intent": "safe", "confidence": 2.0}'
        result = _parse_response(raw)
        assert result["confidence"] == 0.5

    def test_negative_confidence_defaults(self):
        raw = '{"intent": "safe", "confidence": -0.5}'
        result = _parse_response(raw)
        assert result["confidence"] == 0.5

    def test_no_json_returns_suspicious(self):
        raw = "I think this skill looks fine but I can't format JSON."
        result = _parse_response(raw)
        assert result["intent"] == "suspicious"
        assert result["confidence"] == 0.3
        assert "parse_error" in result["flags"]

    def test_empty_string(self):
        result = _parse_response("")
        assert result["intent"] == "suspicious"
        assert "parse_error" in result["flags"]

    def test_missing_fields_use_defaults(self):
        raw = '{"intent": "educational"}'
        result = _parse_response(raw)
        assert result["intent"] == "educational"
        assert result["confidence"] == 0.5
        assert result["reasoning"] == ""
        assert result["flags"] == []


class TestReadSkillContent:
    def test_reads_skill_md(self, skill_dir):
        md, scripts = _read_skill_content(skill_dir)
        assert "Hello Skill" in md
        assert scripts == "(no scripts)"

    def test_reads_scripts_dir(self, malicious_skill_dir):
        md, scripts = _read_skill_content(malicious_skill_dir)
        assert "Cleanup Skill" in md
        assert "clean.sh" in scripts
        assert "dd if=/dev/zero" in scripts

    def test_empty_dir(self, empty_skill_dir):
        md, scripts = _read_skill_content(empty_skill_dir)
        assert md == ""
        assert scripts == "(no scripts)"

    def test_reads_toplevel_py(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("# Test")
        (tmp_path / "run.py").write_text("print('hi')")
        md, scripts = _read_skill_content(tmp_path)
        assert "run.py" in scripts
        assert "print('hi')" in scripts


class TestAnalyzeIntent:
    def test_no_api_key(self, skill_dir):
        with patch.dict("os.environ", {}, clear=True):
            result = analyze_intent(skill_dir)
        assert result["status"] == "skipped"
        assert "No LLM API key" in result["reason"]

    def test_empty_skill_md(self, empty_skill_dir):
        client = MagicMock()
        result = analyze_intent(empty_skill_dir, client=client)
        assert result["status"] == "skipped"
        assert "SKILL.md" in result["reason"]

    def test_successful_analysis(self, skill_dir):
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMResponse(
            text='{"intent": "safe", "confidence": 0.95, "reasoning": "Normal greeting skill", "flags": []}',
            model="test-model",
            provider="test",
            input_tokens=100,
            output_tokens=50,
        )
        result = analyze_intent(skill_dir, client=mock_client)
        assert result["status"] == "ok"
        assert result["intent"] == "safe"
        assert result["model"] == "test-model"
        assert result["tokens"]["input"] == 100

    def test_llm_error_returns_skipped(self, skill_dir):
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMResponse(
            text="", model="test", provider="test", error="timeout"
        )
        result = analyze_intent(skill_dir, client=mock_client)
        assert result["status"] == "skipped"
        assert "timeout" in result["reason"]

    def test_truncates_long_content(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("x" * 20000)
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMResponse(
            text='{"intent": "safe", "confidence": 0.9, "reasoning": "ok", "flags": []}',
            model="test", provider="test",
        )
        result = analyze_intent(tmp_path, client=mock_client)
        # Verify the prompt was truncated (check the call)
        call_args = mock_client.complete.call_args[0][0]
        assert "truncated" in call_args
        assert result["status"] == "ok"

    def test_exception_returns_skipped(self, skill_dir):
        mock_client = MagicMock()
        mock_client.complete.side_effect = RuntimeError("boom")
        result = analyze_intent(skill_dir, client=mock_client)
        assert result["status"] == "skipped"
        assert "boom" in result["reason"]
