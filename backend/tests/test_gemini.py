import io
import json
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError

from mr_robot_backend.providers import GeminiProvider, ProviderConfig, ProviderError, MAX_RESPONSE_BYTES


class Response(io.BytesIO):
    status = 200


class GeminiTests(unittest.TestCase):
    def provider(self, raw=None):
        provider = GeminiProvider(ProviderConfig("gemini", "https://generativelanguage.googleapis.com/v1beta",
                                                "gemini-3.1-flash-lite", "synthetic-test-key"))
        provider._opener = Mock()
        if raw is None:
            raw = json.dumps({"candidates": [{"finishReason": "STOP", "content": {"parts": [
                {"text": "private reasoning", "thought": True}, {"text": "Hello"}, {"text": " robot"}]}}]}).encode()
        provider._opener.open.return_value = Response(raw)
        return provider

    def test_native_request_and_public_text_only(self):
        provider = self.provider()
        reply = provider.complete("Test prompt")
        request = provider._opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent")
        self.assertNotIn("synthetic-test-key", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "synthetic-test-key")
        self.assertIsNone(request.get_header("Authorization"))
        data = json.loads(request.data)
        self.assertEqual(data["contents"], [{"parts": [{"text": "Test prompt"}]}])
        self.assertEqual(data["generationConfig"]["maxOutputTokens"], 256)
        self.assertEqual(data["generationConfig"]["thinkingConfig"], {"thinkingLevel":"minimal"})
        self.assertEqual(reply.text, "Hello robot")
        self.assertEqual(reply.provider, "gemini")

    def test_invalid_responses_and_tools_never_escape(self):
        for raw in (b"not json", b"[]", b"{}", b'{"candidates":[]}', b'{"error":{"message":"private"}}',
                    b'{"promptFeedback":{"blockReason":"SAFETY"}}',
                    b'{"candidates":[{"finishReason":"SAFETY"}]}',
                    b'{"candidates":[{"finishReason":"STOP","content":{"parts":[{"functionCall":{}}]}}]}',
                    b'{"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":7}]}}]}',
                    b"x" * (MAX_RESPONSE_BYTES + 1)):
            with self.subTest(length=len(raw)), self.assertRaises(ProviderError) as error:
                self.provider(raw).complete("Test")
            self.assertNotIn("private", str(error.exception))

    def test_new_flash_models_use_supported_thinking_level(self):
        for model, level in (("gemini-3.8-flash", "low"), ("gemini-3.6-flash", "low"),
                             ("gemini-3.5-flash-lite", "minimal")):
            with self.subTest(model=model):
                provider = self.provider()
                provider.config = ProviderConfig("gemini", "https://generativelanguage.googleapis.com/v1beta",
                                                 model, "synthetic-test-key")
                provider.complete("Test")
                request = provider._opener.open.call_args.args[0]
                self.assertIn("/models/" + model + ":generateContent", request.full_url)
                self.assertEqual(json.loads(request.data)["generationConfig"]["thinkingConfig"],
                                 {"thinkingLevel": level})

    def test_live_model_is_not_sent_to_text_endpoint(self):
        config = ProviderConfig("gemini", "https://generativelanguage.googleapis.com/v1beta",
                                "gemini-3.8-live", "synthetic-test-key")
        with self.assertRaisesRegex(ProviderError, "gemini_live_requires_voice_transport"):
            GeminiProvider(config)

    def test_quota_key_errors_are_redacted_and_never_retried(self):
        for code, expected in ((429, "gemini_quota_exceeded"), (403, "gemini_key_rejected"), (404, "gemini_model_not_found")):
            provider = self.provider()
            provider._opener.open.side_effect = HTTPError("https://example.test", code, "private", {}, io.BytesIO(b"private"))
            with self.assertRaisesRegex(ProviderError, expected):
                provider.complete("Test")
            self.assertEqual(provider._opener.open.call_count, 1)

    def test_invalid_prompt_endpoint_and_model(self):
        provider = self.provider()
        for prompt in ("", "x" * 4097, "\ud800"):
            with self.assertRaises(ProviderError):
                provider.complete(prompt)
        provider._opener.open.assert_not_called()
        for base, model in (("https://evil.test", "gemini-test"), ("https://generativelanguage.googleapis.com/v1beta", "gemini-../key")):
            with self.assertRaises(ProviderError):
                ProviderConfig("gemini", base, model, "synthetic-test-key")
