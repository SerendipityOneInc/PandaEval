"""Tests for security.client module."""

import json
from unittest.mock import patch, MagicMock

from zooeval.security.client import LLMResponse, LLMClient, _detect_provider, _http_post


class TestLLMResponse:
    def test_ok_when_no_error(self):
        r = LLMResponse(text="hi", model="m", provider="p")
        assert r.ok is True

    def test_not_ok_when_error(self):
        r = LLMResponse(text="", model="m", provider="p", error="fail")
        assert r.ok is False

    def test_defaults(self):
        r = LLMResponse(text="x", model="m", provider="p")
        assert r.input_tokens == 0
        assert r.output_tokens == 0
        assert r.error == ""


class TestDetectProvider:
    def test_claude_prefix(self):
        assert _detect_provider("claude-sonnet-4-20250514") == "anthropic"
        assert _detect_provider("Claude-3-opus") == "anthropic"

    def test_openai_prefixes(self):
        assert _detect_provider("gpt-4o") == "openai"
        assert _detect_provider("o1-mini") == "openai"
        assert _detect_provider("o3-mini") == "openai"
        assert _detect_provider("chatgpt-4o") == "openai"

    def test_unknown_falls_back_to_env(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-123"}, clear=True):
            assert _detect_provider("custom-model") == "anthropic"

    def test_unknown_no_env_defaults_openai(self):
        with patch.dict("os.environ", {}, clear=True):
            assert _detect_provider("custom-model") == "openai"


class TestLLMClientFromEnv:
    def test_anthropic_key(self):
        env = {"ANTHROPIC_API_KEY": "sk-ant-test"}
        with patch.dict("os.environ", env, clear=True):
            client = LLMClient.from_env()
            assert client.provider == "anthropic"
            assert client.api_key == "sk-ant-test"

    def test_openai_key(self):
        env = {"OPENAI_API_KEY": "sk-openai-test"}
        with patch.dict("os.environ", env, clear=True):
            client = LLMClient.from_env()
            assert client.provider == "openai"
            assert client.api_key == "sk-openai-test"

    def test_anthropic_token_fallback(self):
        env = {"ANTHROPIC_API_TOKEN": "sk-token"}
        with patch.dict("os.environ", env, clear=True):
            client = LLMClient.from_env()
            assert client.provider == "anthropic"

    def test_no_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            try:
                LLMClient.from_env()
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "No LLM API key" in str(e)

    def test_explicit_model_detects_provider(self):
        env = {"ANTHROPIC_API_KEY": "sk-ant", "OPENAI_API_KEY": "sk-oai"}
        with patch.dict("os.environ", env, clear=True):
            client = LLMClient.from_env(model="gpt-4o")
            assert client.provider == "openai"

    def test_claude_model_without_anthropic_key_falls_back(self):
        env = {"OPENAI_API_KEY": "sk-oai"}
        with patch.dict("os.environ", env, clear=True):
            client = LLMClient.from_env(model="claude-sonnet-4-20250514")
            assert client.provider == "openai"  # falls back


class TestLLMClientAvailable:
    def test_available_with_anthropic(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "x"}, clear=True):
            assert LLMClient.available() is True

    def test_available_with_openai(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "x"}, clear=True):
            assert LLMClient.available() is True

    def test_not_available(self):
        with patch.dict("os.environ", {}, clear=True):
            assert LLMClient.available() is False


class TestLLMClientComplete:
    def test_routes_to_anthropic(self):
        client = LLMClient("anthropic", "claude-test", "key")
        with patch.object(client, "_call_anthropic", return_value="mock") as m:
            result = client.complete("hello")
            m.assert_called_once_with("hello", 4096)
            assert result == "mock"

    def test_routes_to_openai(self):
        client = LLMClient("openai", "gpt-test", "key")
        with patch.object(client, "_call_openai", return_value="mock") as m:
            result = client.complete("hello")
            m.assert_called_once_with("hello", 4096)


class TestLLMClientCallAnthropic:
    def test_parses_success_response(self):
        client = LLMClient("anthropic", "claude-test", "key")
        mock_resp = json.dumps({
            "content": [{"type": "text", "text": "Hello!"}],
            "model": "claude-test",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        })
        with patch("zooeval.security.client._http_post", return_value=(True, mock_resp)):
            resp = client._call_anthropic("hi", 100)
            assert resp.ok
            assert resp.text == "Hello!"
            assert resp.input_tokens == 10
            assert resp.provider == "anthropic"

    def test_handles_http_error(self):
        client = LLMClient("anthropic", "claude-test", "key")
        with patch("zooeval.security.client._http_post", return_value=(False, "HTTP 401: Unauthorized")):
            resp = client._call_anthropic("hi", 100)
            assert not resp.ok
            assert "401" in resp.error


class TestLLMClientCallOpenAI:
    def test_parses_success_response(self):
        client = LLMClient("openai", "gpt-test", "key", base_url="https://api.openai.com/v1")
        mock_resp = json.dumps({
            "choices": [{"message": {"content": "World!"}}],
            "model": "gpt-test",
            "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        })
        with patch("zooeval.security.client._http_post", return_value=(True, mock_resp)):
            resp = client._call_openai("hi", 100)
            assert resp.ok
            assert resp.text == "World!"
            assert resp.input_tokens == 8
            assert resp.provider == "openai"

    def test_handles_http_error(self):
        client = LLMClient("openai", "gpt-test", "key", base_url="https://api.openai.com/v1")
        with patch("zooeval.security.client._http_post", return_value=(False, "HTTP 500: error")):
            resp = client._call_openai("hi", 100)
            assert not resp.ok
            assert "500" in resp.error


class TestLLMClientRepr:
    def test_repr(self):
        client = LLMClient("anthropic", "claude-test", "secret")
        s = repr(client)
        assert "anthropic" in s
        assert "claude-test" in s
        assert "secret" not in s  # API key should not appear
