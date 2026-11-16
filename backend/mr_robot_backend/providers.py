"""Bounded text-provider adapter foundation. No server or device credentials here."""
import base64
import io
import wave
from dataclasses import dataclass, field
import json
import math
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener
from .tls import verified_context

MAX_PROMPT_BYTES = 4096
MAX_RESPONSE_BYTES = 65536
MAX_REPLY_BYTES = 4096


class ProviderError(RuntimeError):
    """A stable error code; never echo provider bodies or authorization headers."""


@dataclass(frozen=True)
class Reply:
    text: str
    provider: str
    model: str


class TextProvider(Protocol):
    def complete(self, text: str) -> Reply:
        ...


def validate_prompt(text):
    if not isinstance(text, str) or not text.strip() or "\x00" in text:
        raise ProviderError("invalid_prompt")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError:
        raise ProviderError("invalid_prompt") from None
    if size > MAX_PROMPT_BYTES:
        raise ProviderError("prompt_too_large")


class MockProvider:
    """Offline fixture for integration work; never represented as a model response."""

    def complete(self, text):
        validate_prompt(text)
        return Reply("Mock connection is working. No AI service was contacted.", "mock", "fixture")


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    base_url: str
    model: str
    api_key: str = field(default="", repr=False)
    max_output_tokens: int = 256
    timeout_seconds: float = 20

    def __post_init__(self):
        if self.provider not in ("gemini", "openrouter", "compatible", "ollama"):
            raise ProviderError("unsupported_provider")
        try:
            url = urlsplit(self.base_url)
            _ = url.port  # Reject invalid port syntax too.
        except ValueError:
            raise ProviderError("invalid_base_url") from None
        if (not url.hostname or url.username is not None or url.password is not None or
                url.query or url.fragment or any(c.isspace() or ord(c) < 32 for c in self.base_url)):
            raise ProviderError("invalid_base_url")
        loopback = url.hostname in ("127.0.0.1", "localhost", "::1")
        if url.scheme != "https" and not (url.scheme == "http" and loopback):
            raise ProviderError("https_required")
        if self.provider == "openrouter" and self.base_url.rstrip("/") != "https://openrouter.ai/api/v1":
            raise ProviderError("invalid_openrouter_endpoint")
        if self.provider == "gemini" and self.base_url.rstrip("/") != "https://generativelanguage.googleapis.com/v1beta":
            raise ProviderError("invalid_gemini_endpoint")
        if self.provider == "ollama" and (self.base_url != "http://127.0.0.1:11434" or self.api_key):
            raise ProviderError("invalid_ollama_endpoint")
        if url.path.rstrip("/").endswith("/chat/completions"):
            raise ProviderError("expected_base_url_not_completion_url")
        if not isinstance(self.api_key, str) or len(self.api_key) > 8192 or any(c.isspace() or not 33 <= ord(c) <= 126 for c in self.api_key):
            raise ProviderError("invalid_api_key")
        if not loopback and not self.api_key:
            raise ProviderError("api_key_required")
        if not isinstance(self.model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/@+\-]{0,127}", self.model):
            raise ProviderError("invalid_model")
        if self.provider == "gemini" and not re.fullmatch(r"gemini-[A-Za-z0-9.\-]{1,110}", self.model):
            raise ProviderError("invalid_gemini_model")
        if type(self.max_output_tokens) is not int or not 1 <= self.max_output_tokens <= 512:
            raise ProviderError("invalid_token_limit")
        ceiling = 50 if self.provider == "ollama" else 30
        if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, (int, float)) or not 1 <= self.timeout_seconds <= ceiling:
            raise ProviderError("invalid_timeout")


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, *_):
        # Do not forward a provider credential to a redirected destination.
        raise ProviderError("redirect_rejected")


class CompatibleChatProvider:
    """OpenRouter or an explicitly configured compatible /chat/completions service."""

    def __init__(self, config):
        if config.provider not in ("openrouter", "compatible"):
            raise ProviderError("invalid_compatible_config")
        self.config = config
        self._opener = build_opener(
            ProxyHandler({}), NoRedirects(), HTTPSHandler(context=verified_context())
        )

    def verify_spend_cap(self, maximum):
        """OpenRouter enforces the money cap; verify it before each inference."""
        if self.config.provider != "openrouter":
            raise ProviderError("budget_check_unsupported")
        request = Request("https://openrouter.ai/api/v1/key", headers={
            "Authorization": "Bearer " + self.config.api_key, "Accept": "application/json"})
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if response.status != 200 or len(raw) > MAX_RESPONSE_BYTES:
                    raise ProviderError("budget_check_failed")
            info = json.loads(raw)["data"]
            limit, remaining = info.get("limit"), info.get("limit_remaining")
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                   for v in (limit, remaining)):
                raise ProviderError("finite_key_spend_cap_required")
            if not 0 < limit <= maximum or remaining <= 0:
                raise ProviderError("key_spend_cap_or_balance_rejected")
            if info.get("is_management_key") is not False or info.get("include_byok_in_limit") is not True:
                raise ProviderError("scoped_key_with_byok_cap_required")
        except HTTPError as error:
            error.close()
            raise ProviderError("budget_check_failed") from None
        except (URLError, TimeoutError, OSError, KeyError, TypeError, ValueError, AttributeError, RecursionError):
            raise ProviderError("budget_check_failed") from None

    def complete(self, text):
        validate_prompt(text)
        body = json.dumps({
            "model": self.config.model,
            "messages": [{"role": "user", "content": text}],
            "max_tokens": self.config.max_output_tokens,
            "stream": False,
        }).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = "Bearer " + self.config.api_key
        request = Request(self.config.base_url.rstrip("/") + "/chat/completions", data=body, headers=headers, method="POST")
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                if response.status != 200:
                    raise ProviderError("upstream_http_error")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            error.close()
            raise ProviderError("upstream_http_error") from None
        except (URLError, TimeoutError, OSError):
            raise ProviderError("upstream_unavailable") from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderError("response_too_large")
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or "error" in data:
                raise ProviderError("invalid_response")
            choice = data["choices"][0]
            if choice.get("error") or choice.get("finish_reason") in ("error", "tool_calls"):
                raise ProviderError("unsupported_response")
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip() or "\x00" in content:
                raise ProviderError("invalid_response")
            if len(content.encode("utf-8")) > MAX_REPLY_BYTES:
                raise ProviderError("reply_too_large")
        except (KeyError, IndexError, TypeError, AttributeError, ValueError, RecursionError):
            raise ProviderError("invalid_response") from None
        return Reply(content, self.config.provider, self.config.model)


OLLAMA_IMAGE_MODELS = frozenset(("x/z-image-turbo", "x/z-image-turbo:latest"))
OLLAMA_TRANSCRIBED_MODELS = frozenset(("qwen3.6", "qwen3.6:latest")) | OLLAMA_IMAGE_MODELS
OLLAMA_VOICE_MODELS = frozenset(("gemma4:12b",)) | OLLAMA_TRANSCRIBED_MODELS


class OllamaProvider:
    def __init__(self, config):
        self.config = config
        self._opener = build_opener(ProxyHandler({}), NoRedirects())

    def complete(self, text):
        validate_prompt(text)
        return self._complete({"role": "user", "content": text}, audio=False)

    def complete_audio(self, pcm, *, transcribe=False):
        if not 2 <= len(pcm) <= 256000 or len(pcm) % 2:
            raise ProviderError("voice_invalid_audio")
        with io.BytesIO() as stream:
            with wave.open(stream, "wb") as wav:
                wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                wav.writeframes(pcm)
            data = base64.b64encode(stream.getbuffer()).decode("ascii")
        instruction = ("Transcribe the spoken request verbatim. Return only the transcription. "
                       "If there is no intelligible speech, return [unclear]." if transcribe else
                       "Answer the spoken question directly and briefly for a small screen. If the audio is unclear, ask the user to repeat it.")
        return self._complete({"role": "user", "content": [
            {"type": "text", "text": instruction},
            {"type": "input_audio", "input_audio": {"data": data, "format": "wav"}},
        ]}, audio=True, transcribe=transcribe)

    def _complete(self, message, audio, transcribe=False):
        body = {"model": "gemma4:12b" if transcribe else self.config.model, "messages": [message], "stream": False}
        if audio:
            endpoint = "/v1/chat/completions"
            body["max_tokens"] = self.config.max_output_tokens
            body["reasoning_effort"] = "none"
        else:
            endpoint = "/api/chat"
            body["think"] = False
            body["options"] = {"num_predict": self.config.max_output_tokens, "num_ctx": 4096}
        request = Request(self.config.base_url + endpoint, data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            error.close()
            raise ProviderError("upstream_http_error") from None
        except TimeoutError:
            raise ProviderError("ollama_timeout") from None
        except (URLError, OSError):
            raise ProviderError("upstream_unavailable") from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderError("response_too_large")
        try:
            value = json.loads(raw)
            choice = value["choices"][0] if audio else value
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip() or "\x00" in content:
                if choice.get("finish_reason") == "length" or value.get("done_reason") == "length":
                    raise ProviderError("ollama_empty_at_limit")
                raise ValueError()
        except (KeyError, TypeError, IndexError, ValueError, RecursionError):
            raise ProviderError("invalid_response") from None
        if len(content.encode("utf-8")) > MAX_REPLY_BYTES:
            raise ProviderError("reply_too_large")
        return Reply(content, "ollama", self.config.model)


class GeminiProvider:
    """Native Google generateContent text path. No tools, uploads or hidden fallback."""

    def __init__(self, config):
        if config.provider != "gemini":
            raise ProviderError("invalid_gemini_config")
        if config.model in ("gemini-3.8-live", "gemini-3.8-live-extended-thinking", "gemini-3.1-flash-live-preview"):
            raise ProviderError("gemini_live_requires_voice_transport")
        self.config = config
        self._opener = build_opener(ProxyHandler({}), NoRedirects(), HTTPSHandler(context=verified_context()))

    def complete(self, text):
        validate_prompt(text)
        generation = {"maxOutputTokens": self.config.max_output_tokens}
        if self.config.model in ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite"):
            generation["thinkingConfig"] = {"thinkingLevel": "minimal"}
        elif self.config.model in ("gemini-3.8-flash", "gemini-3.6-flash"):
            generation["thinkingConfig"] = {"thinkingLevel": "low"}
        request = Request(self.config.base_url.rstrip("/") + "/models/" + self.config.model + ":generateContent",
                          data=json.dumps({"contents": [{"parts": [{"text": text}]}],
                                           "generationConfig": generation}).encode(),
                          headers={"Content-Type": "application/json", "Accept": "application/json",
                                   "x-goog-api-key": self.config.api_key}, method="POST")
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if response.status != 200:
                    raise ProviderError("upstream_http_error")
        except HTTPError as error:
            code = error.code
            error.close()
            raise ProviderError("gemini_quota_exceeded" if code == 429 else "gemini_key_rejected" if code in (401, 403)
                                else "gemini_model_not_found" if code == 404 else "gemini_http_" + str(code)) from None
        except (URLError, TimeoutError, OSError):
            raise ProviderError("upstream_unavailable") from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderError("response_too_large")
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or data.get("error") or data.get("promptFeedback", {}).get("blockReason"):
                raise ProviderError("gemini_blocked_or_invalid")
            candidate = data["candidates"][0]
            if candidate.get("finishReason") not in ("STOP", "MAX_TOKENS"):
                raise ProviderError("gemini_incomplete_or_blocked")
            parts = candidate["content"]["parts"]
            if any("functionCall" in part or "inlineData" in part for part in parts):
                raise ProviderError("unsupported_response")
            content = "".join(part["text"] for part in parts if not part.get("thought", False))
            if not content.strip() or "\x00" in content or len(content.encode("utf-8")) > MAX_REPLY_BYTES:
                raise ProviderError("invalid_response")
        except (KeyError, IndexError, TypeError, AttributeError, ValueError, RecursionError):
            raise ProviderError("invalid_response") from None
        return Reply(content, "gemini", self.config.model)
