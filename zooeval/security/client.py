"""Unified LLM client supporting Anthropic and OpenAI-compatible APIs.

Uses only stdlib (urllib) — zero external dependencies.

Configuration via environment variables:
  ANTHROPIC_API_KEY  — for Claude models (default provider)
  OPENAI_API_KEY     — for OpenAI/compatible models
  OPENAI_BASE_URL    — custom base URL for OpenAI-compatible APIs
"""

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM API call."""
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    error: str = ""

    @property
    def ok(self):
        return not self.error


_FALLBACK_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}

_ANTHROPIC_PREFIXES = ("claude-",)
_OPENAI_PREFIXES = ("gpt-", "o1-", "o3-", "chatgpt-")


def _default_model(provider):
    """Get default model for a provider, checking env at call time."""
    return os.environ.get("LLM_DEFAULT_MODEL") or _FALLBACK_MODELS[provider]


def _has_anthropic_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_TOKEN"))


def _detect_provider(model):
    lower = model.lower()
    if any(lower.startswith(p) for p in _ANTHROPIC_PREFIXES):
        return "anthropic"
    if any(lower.startswith(p) for p in _OPENAI_PREFIXES):
        return "openai"
    if _has_anthropic_key():
        return "anthropic"
    return "openai"


def _http_post(url, headers, body, timeout):
    data = json.dumps(body).encode("utf-8")
    headers.setdefault("User-Agent", "zooeval-security/1.0")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass
        return False, f"HTTP {e.code}: {error_body}"
    except urllib.error.URLError as e:
        return False, f"URL error: {e.reason}"
    except TimeoutError:
        return False, "Request timed out"
    except OSError as e:
        return False, f"OS error: {e}"


class LLMClient:
    """Unified LLM client for Anthropic and OpenAI-compatible APIs."""

    def __init__(self, provider, model, api_key, base_url="", timeout=120):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    @classmethod
    def from_env(cls, model="", timeout=120):
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_TOKEN", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        openai_base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

        if model:
            provider = _detect_provider(model)
            if provider == "anthropic" and not anthropic_key and openai_key:
                provider = "openai"
                model = _default_model("openai")
        elif anthropic_key:
            provider = "anthropic"
            model = _default_model("anthropic")
        elif openai_key:
            provider = "openai"
            model = _default_model("openai")
        else:
            raise ValueError("No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

        if provider == "anthropic":
            if not anthropic_key:
                raise ValueError("ANTHROPIC_API_KEY not set for Claude model")
            base = os.environ.get("ANTHROPIC_BASE_URL", "")
            return cls(provider, model, anthropic_key, base_url=base, timeout=timeout)
        else:
            if not openai_key:
                raise ValueError("OPENAI_API_KEY not set for OpenAI model")
            return cls(provider, model, openai_key, base_url=openai_base, timeout=timeout)

    @classmethod
    def available(cls):
        return bool(
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_API_TOKEN")
            or os.environ.get("OPENAI_API_KEY")
        )

    def complete(self, prompt, max_tokens=4096):
        if self.provider == "anthropic":
            return self._call_anthropic(prompt, max_tokens)
        return self._call_openai(prompt, max_tokens)

    def _call_anthropic(self, prompt, max_tokens):
        base = self.base_url.rstrip("/") if self.base_url else "https://api.anthropic.com"
        url = f"{base}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        ok, raw = _http_post(url, headers, body, self.timeout)
        if not ok:
            return LLMResponse(text="", model=self.model, provider="anthropic", error=raw)
        try:
            data = json.loads(raw)
            text = "".join(
                b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
            )
            usage = data.get("usage", {})
            return LLMResponse(
                text=text, model=data.get("model", self.model), provider="anthropic",
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            )
        except (json.JSONDecodeError, KeyError) as e:
            return LLMResponse(text="", model=self.model, provider="anthropic", error=f"Parse error: {e}")

    def _call_openai(self, prompt, max_tokens):
        base = self.base_url.rstrip("/")
        url = f"{base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        ok, raw = _http_post(url, headers, body, self.timeout)
        if not ok:
            return LLMResponse(text="", model=self.model, provider="openai", error=raw)
        try:
            data = json.loads(raw)
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return LLMResponse(
                text=text, model=data.get("model", self.model), provider="openai",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return LLMResponse(text="", model=self.model, provider="openai", error=f"Parse error: {e}")

    def __repr__(self):
        return f"LLMClient(provider={self.provider!r}, model={self.model!r})"
