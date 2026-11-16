import io
import json
import unittest
import ssl
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

from mr_robot_backend.providers import (
    CompatibleChatProvider, MockProvider, NoRedirects, ProviderConfig, ProviderError, MAX_RESPONSE_BYTES,
)
from mr_robot_backend.tls import verified_context


class Response(io.BytesIO):
    status = 200


def encoded(content="Hello"):
    return json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": content}}]}).encode()


class ProviderTests(unittest.TestCase):
    def test_tls_always_checks_hostname_and_certificate(self):
        context=verified_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
        self.assertGreater(context.cert_store_stats()["x509_ca"],0)
    def make(self, **kwargs):
        config = ProviderConfig("compatible", "https://example.test/v1", "test-model", "unit-test-only", **kwargs)
        provider = CompatibleChatProvider(config)
        provider._opener = Mock()
        provider._opener.open.return_value = Response(encoded())
        return provider

    def test_request_and_normalized_reply(self):
        provider = self.make()
        reply = provider.complete("Test input")
        request = provider._opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.test/v1/chat/completions")
        body = json.loads(request.data)
        self.assertEqual(body["messages"], [{"role": "user", "content": "Test input"}])
        self.assertFalse(body["stream"])
        self.assertEqual(body["max_tokens"], 256)
        self.assertEqual(request.get_header("Authorization"), "Bearer unit-test-only")
        self.assertEqual((reply.text, reply.provider, reply.model), ("Hello", "compatible", "test-model"))
        self.assertNotIn("unit-test-only", repr(provider.config))

    def test_bad_prompts_never_send(self):
        for text in ("", " ", "\x00", "a" * 4097, "🙂" * 1025, "\ud800", None):
            with self.subTest(text_type=type(text).__name__):
                provider = self.make()
                with self.assertRaises(ProviderError): provider.complete(text)
                provider._opener.open.assert_not_called()

    def test_oversized_response(self):
        provider = self.make()
        provider._opener.open.return_value = Response(b" " * (MAX_RESPONSE_BYTES + 1))
        with self.assertRaisesRegex(ProviderError, "response_too_large"): provider.complete("Test")

    def test_bad_response_shapes_and_unsupported_tools(self):
        for raw in [b"not json", b"[]", b"{}", b'{"error":{"message":"private upstream detail"}}',
                    encoded(None), encoded(""), encoded("x" * 4097),
                    b'{"choices":[{"finish_reason":"tool_calls","message":{"content":"tool"}}]}']:
            with self.subTest(bytes=len(raw)):
                provider = self.make(); provider._opener.open.return_value = Response(raw)
                with self.assertRaises(ProviderError) as error: provider.complete("Test")
                self.assertNotIn("private upstream detail", str(error.exception))

    def test_errors_do_not_expose_upstream_body_or_key(self):
        for error in [HTTPError("https://example.test", 401, "private detail", {}, io.BytesIO(b"private body")),
                      URLError("private key or endpoint detail"), TimeoutError("private detail")]:
            with self.subTest(error_type=type(error).__name__):
                provider = self.make();provider._opener.open.side_effect = error
                with self.assertRaises(ProviderError) as result: provider.complete("Test")
                self.assertNotIn("private", str(result.exception))

    def test_cloud_https_loopback_and_endpoint_validation(self):
        for url in ("http://example.test/v1", "https://user:pass@example.test/v1", "https://example.test/v1?key=secret",
                    "https://example.test/v1#fragment", "file:///tmp/model", "https://example.test:bad/v1", "https://example.test/v1\n"):
            with self.subTest(url=url), self.assertRaises(ProviderError):
                ProviderConfig("compatible", url, "test", "unit-test-only")
        self.assertEqual(ProviderConfig("compatible", "http://127.0.0.1:1234/v1", "test").provider, "compatible")
        with self.assertRaises(ProviderError): ProviderConfig("openrouter", "https://wrong.test/v1", "test", "unit-test-only")
        with self.assertRaises(ProviderError): ProviderConfig("compatible", "https://example.test/v1", "test")
        self.assertEqual(ProviderConfig("openrouter", "https://openrouter.ai/api/v1", "vendor/model", "unit-test-only").provider, "openrouter")

    def test_model_header_limits_and_redirect_rejection(self):
        for model in ("", "model\n", "x" * 129):
            with self.assertRaises(ProviderError): ProviderConfig("compatible", "http://localhost/v1", model)
        for key in ("token\nInjected: header", "token value", "非ASCII", "x" * 8193):
            with self.assertRaises(ProviderError): ProviderConfig("compatible", "http://localhost/v1", "test", key)
        for limit in (0, 513, True):
            with self.assertRaises(ProviderError): self.make(max_output_tokens=limit)
        for timeout in (0, 31, float("nan")):
            with self.assertRaises(ProviderError): self.make(timeout_seconds=timeout)
        with self.assertRaisesRegex(ProviderError, "redirect_rejected"):
            NoRedirects().redirect_request(None, None, None, None, None, "https://other.test")

    def test_mock_is_explicitly_offline(self):
        reply = MockProvider().complete("Test")
        self.assertEqual(reply.provider, "mock")
        self.assertIn("No AI service", reply.text)

    def test_openrouter_budget_requires_finite_scoped_cap(self):
        provider = CompatibleChatProvider(ProviderConfig("openrouter", "https://openrouter.ai/api/v1", "test/model", "synthetic-key"))
        provider._opener = Mock()
        valid = {"limit":1,"limit_remaining":0.9,"include_byok_in_limit":True,"is_management_key":False}
        provider._opener.open.return_value = Response(json.dumps({"data":valid}).encode())
        provider.verify_spend_cap(1)
        self.assertEqual(provider._opener.open.call_args.args[0].full_url,"https://openrouter.ai/api/v1/key")
        for change in ({"limit":None},{"limit":2},{"limit_remaining":0},{"include_byok_in_limit":False},{"is_management_key":True}):
            provider._opener.open.return_value = Response(json.dumps({"data":dict(valid,**change)}).encode())
            with self.assertRaises(ProviderError):provider.verify_spend_cap(1)


if __name__ == "__main__": unittest.main()
