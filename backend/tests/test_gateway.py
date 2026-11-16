import http.client
import hmac
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock

from mr_robot_backend.gateway import Gateway
from mr_robot_backend.providers import ProviderError, Reply
from mr_robot_backend.server import ManagerServer
from mr_robot_backend.settings import Settings, SettingsStore
from mr_robot_backend.usage import Usage


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.provider = Mock()
        self.provider.complete.return_value = Reply("Synthetic reply", "gemini", "gemini-test")
        self.factory = Mock(return_value=self.provider)
        self.gateway = Gateway(self.root, self.factory)

    def tearDown(self):
        self.gateway.usb.close()
        self.directory.cleanup()

    def configure(self, **extra):
        return self.gateway.configure(dict(provider="gemini", model="gemini-test", api_key="synthetic-test-key",
                                           gemini_free_tier_confirmed=True, **extra))

    def test_secret_storage_permissions_and_public_redaction(self):
        public = self.configure()
        self.assertNotIn("synthetic-test-key", json.dumps(public))
        self.assertNotIn("synthetic-test-key", repr(self.gateway.settings.value))
        self.assertEqual((self.root / "provider.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.root / "manager-token").stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.gateway.settings.value.api_key, SettingsStore(self.root / "provider.json").value.api_key)
        with self.assertRaises(ProviderError):
            self.gateway.configure({"provider": "compatible", "base_url": "https://other.test/v1"})
        self.assertEqual(self.gateway.settings.value.provider, "gemini")

    def test_gemini_requires_free_tier_confirmation_and_strict_request_shape(self):
        self.gateway.configure({"provider": "gemini", "model": "gemini-test", "api_key": "synthetic-test-key"})
        with self.assertRaisesRegex(ProviderError, "confirm_gemini_free_tier"):
            self.gateway.chat({"text": "Test"})
        self.provider.complete.assert_not_called()
        self.assertEqual(self.gateway.usage.count_today(), 0)
        self.configure()
        with self.assertRaisesRegex(ProviderError, "invalid_request"):
            self.gateway.chat({"text": "Test", "model": "attacker-selected"})
        reply = self.gateway.chat({"text": "Test"})
        self.assertEqual(reply["provider"], "gemini")
        self.assertEqual(self.gateway.usage.count_today(), 1)

    def test_switch_restores_gemini_confirmation_for_the_saved_key(self):
        self.configure(daily_requests=500)
        self.gateway.configure({"provider": "ollama", "model": "gemma4:12b"})
        saved = self.gateway.configure({"provider": "gemini", "model": "gemini-test", "api_key": ""})
        self.assertTrue(saved["gemini_free_tier_confirmed"])
        self.assertEqual(saved["daily_requests"], 500)
        self.gateway.configure({"provider": "gemini", "gemini_free_tier_confirmed": False})
        self.gateway.configure({"provider": "ollama", "model": "gemma4:12b"})
        restored = self.gateway.configure({"provider": "gemini", "model": "gemini-test", "api_key": ""})
        self.assertFalse(restored["gemini_free_tier_confirmed"])

    def test_failed_attempt_and_daily_limit_survive_restart(self):
        self.configure(daily_requests=1)
        self.provider.complete.side_effect = ProviderError("synthetic_failure")
        with self.assertRaises(ProviderError):
            self.gateway.chat({"text": "Test"})
        restarted = Gateway(self.root, self.factory)
        with self.assertRaisesRegex(ProviderError, "daily_request_limit"):
            restarted.chat({"text": "Test again"})
        self.assertEqual(self.provider.complete.call_count, 1)

    def test_atomic_limits_and_utc_reset(self):
        now = [1793318400.0]
        usage = Usage(self.root / "clock.sqlite", clock=lambda: now[0])
        policy = Settings(daily_requests=1)
        results = []
        def attempt():
            try:
                usage.reserve(policy); results.append("ok")
            except ProviderError:
                results.append("limited")
        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertCountEqual(results, ["ok", "limited"])
        now[0] += 86400
        self.assertEqual(usage.count_today(), 0)
        usage.reserve(policy)

    def test_minute_limit_and_single_inference(self):
        policy = Settings(requests_per_minute=1)
        self.gateway.usage.reserve(policy)
        with self.assertRaisesRegex(ProviderError, "minute_request_limit"):
            self.gateway.usage.reserve(policy)
        self.gateway._request_lock.acquire()
        try:
            with self.assertRaisesRegex(ProviderError, "request_in_progress"):
                self.gateway.chat({"text": "Test"})
        finally:
            self.gateway._request_lock.release()

    def test_openrouter_checks_cap_before_inference_and_counts_failed_attempt(self):
        self.gateway.configure({"provider":"openrouter","model":"test/model","api_key":"synthetic-key",
                                "remote_budget_confirmed":True})
        self.provider.verify_spend_cap.side_effect=ProviderError("finite_key_spend_cap_required")
        with self.assertRaises(ProviderError):self.gateway.chat({"text":"Test"})
        self.provider.complete.assert_not_called()
        self.assertEqual(self.gateway.usage.count_today(),1)

    def test_remote_compatible_needs_budget_confirmation_but_local_does_not(self):
        self.gateway.configure({"provider":"compatible","base_url":"https://example.test/v1",
                                "model":"test-model","api_key":"synthetic-key"})
        with self.assertRaisesRegex(ProviderError,"configure_provider_spend_cap"):
            self.gateway.chat({"text":"Test"})
        self.provider.complete.assert_not_called()
        self.gateway.configure({"base_url":"http://127.0.0.1:1234/v1","api_key":""})
        self.gateway.chat({"text":"Test"})
        self.provider.complete.assert_called_once()

    def test_failed_caption_delivery_preserves_ai_reply_without_regeneration(self):
        self.configure()
        device=Mock()
        device.request.side_effect=[{"caption_supported":True},TimeoutError()]
        self.gateway.usb._device=device
        result=self.gateway.chat({"text":"Test"})
        self.assertEqual(result["text"],"Synthetic reply")
        self.assertEqual(result["device_delivery"],"failed")
        self.provider.complete.assert_called_once()
        self.gateway.usb._device=None


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.gateway = Gateway(Path(self.directory.name))
        self.server = ManagerServer(0, self.gateway)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.directory.cleanup()

    def request(self, path, body=None, role="manager", **extra):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {}
        if role:
            headers["Authorization"] = "Bearer " + (self.gateway.manager_token if role == "manager" else self.gateway.device_token)
        raw = None if body is None else json.dumps(body)
        if raw is not None: headers["Content-Type"] = "application/json"
        headers.update(extra)
        connection.request("GET" if raw is None else "POST", path, raw, headers)
        response = connection.getresponse(); data = response.read(); code = response.status
        connection.close()
        return code, data

    def test_unauthorized_never_consumes_a_request(self):
        self.assertEqual(self.request("/v1/chat", {"text": "Test"}, role=None)[0], 401)
        self.assertEqual(self.gateway.usage.count_today(), 0)
        self.assertEqual(self.request("/api/settings", {"provider": "mock"}, role="device")[0], 401)
        self.assertEqual(self.request("/api/device/reply", {"provider":"gemini","text":"Test"}, role="device")[0],401)

    def test_identity_proof_and_caption_replay_do_not_call_provider(self):
        nonce="1"*32
        code,raw=self.request("/api/identity?nonce="+nonce,role=None)
        self.assertEqual(code,200)
        self.assertEqual(json.loads(raw)["proof"],hmac.digest(self.gateway.manager_token.encode(),nonce.encode(),"sha256").hex())
        self.assertNotIn(self.gateway.manager_token.encode(),raw)
        self.assertEqual(self.request("/api/identity?nonce=invalid",role=None)[0],400)
        code,raw=self.request("/api/device/reply",{"provider":"gemini","text":"Synthetic greeting"})
        self.assertEqual(code,200)
        self.assertEqual(json.loads(raw)["device_delivery"],"not_connected")
        self.assertEqual(self.gateway.usage.count_today(),0)

    def test_browser_boundary_and_body_limits(self):
        self.assertEqual(self.request("/v1/chat", {"text": "Test"}, Origin="https://evil.test")[0], 403)
        self.assertEqual(self.request("/v1/chat", {"text": "Test"}, Host="evil.test")[0], 403)
        self.assertEqual(self.request("/v1/chat", {"text": "Test"}, **{"Content-Length": "16385"})[0], 400)
        self.assertEqual(self.gateway.usage.count_today(), 0)

    def test_mock_roundtrip_and_static_files_contain_no_credentials(self):
        code, data = self.request("/v1/chat", {"text": "Test"}, role="device")
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(data)["is_mock"])
        for path in ("/", "/app.js", "/style.css"):
            code, data = self.request(path, role=None)
            self.assertEqual(code, 200)
            self.assertNotIn(self.gateway.manager_token.encode(), data)
            self.assertNotIn(self.gateway.device_token.encode(), data)
        self.assertEqual(self.request("/private/host/provider.json")[0], 404)
