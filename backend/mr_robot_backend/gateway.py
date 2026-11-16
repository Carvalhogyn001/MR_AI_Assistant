"""Authenticated HTTP is outside this class; route selection always stays on host."""
import secrets
import threading
from urllib.parse import urlsplit

from . import board_runtime
from .automatic_voice import AutomaticVoice
from .ollama_image import OllamaImage
from .providers import OLLAMA_IMAGE_MODELS, OLLAMA_VOICE_MODELS, CompatibleChatProvider, GeminiProvider, MockProvider, OllamaProvider, ProviderError, validate_prompt
from .settings import SettingsStore, load_token
from .usage import Usage
from .usb_bridge import UsbBridge
from .voice import VoiceController


def make_provider(config):
    return {"gemini": GeminiProvider, "ollama": OllamaProvider}.get(config.provider, CompatibleChatProvider)(config)


class Gateway:
    def __init__(self, private_dir, provider_factory=make_provider):
        self.settings = SettingsStore(private_dir / "provider.json")
        self.manager_token = load_token(private_dir / "manager-token")
        self.device_token = load_token(private_dir / "device-token")
        self.usage = Usage(private_dir / "usage.sqlite")
        self.images = OllamaImage()
        self.latest_image = None
        self.image_id = None
        self.usb = UsbBridge()
        self._request_lock = threading.Lock()
        self._config_lock = threading.Lock()
        self._runtime_lock = threading.Lock()
        self._runtime = {"firmware": "unknown"}
        self._provider_factory = provider_factory
        self.voice = VoiceController(self)
        self.automatic = AutomaticVoice(self)

    def authenticate(self, authorization, manager_only=False):
        if not isinstance(authorization, str) or len(authorization) > 128:
            return False
        prefix = "Bearer "
        if not authorization.startswith(prefix):
            return False
        token = authorization[len(prefix):]
        if not token.isascii():
            return False
        return secrets.compare_digest(token, self.manager_token) or (
            not manager_only and secrets.compare_digest(token, self.device_token))

    def status(self):
        with self._config_lock:
            settings = self.settings.value.public()
            gemini = self.settings.gemini_saved()
        return {"settings": settings, "requests_today": self.usage.count_today(),
                "transport": "loopback_http", "voice_chat_ready": settings["provider"] == "gemini" and settings["key_configured"],
                "local_button_supported": settings["provider"] == "ollama" and settings["model"] in OLLAMA_VOICE_MODELS,
                "voice": self.voice.status(), "voice_paused": self.automatic.paused,
                "voice_arm_error": self.automatic.arm_error, "image_id": self.image_id,
                "gemini_profile_confirmed": bool(gemini and gemini.gemini_free_tier_confirmed)}

    def generate_image(self, prompt):
        image = self.images.generate(prompt)
        with self._config_lock:
            self.image_id = secrets.token_hex(16)
            self.latest_image = {"id": self.image_id, "png": image}
            return self.latest_image

    def device_status(self):
        usb = self.usb.status()
        if usb["connected"]:
            self._runtime = {"firmware": "face-lab"}
        elif self._runtime_lock.acquire(blocking=False):
            try:
                if not self.voice.status()["active"]:
                    self._runtime = board_runtime.inspect(usb["ports"])
            finally:
                self._runtime_lock.release()
        return {**usb, "runtime": self._runtime}

    def apply_device_provider(self, expected):
        with self._runtime_lock, self.automatic.lock:
            if self.voice.stop(wait=True)["active"]:
                raise ProviderError("stop_voice_mode_first")
            if not self._request_lock.acquire(blocking=False):
                raise ProviderError("request_in_progress")
            try:
                with self._config_lock:
                    provider = self.settings.value.provider
                if provider != expected:
                    raise ProviderError("provider_changed")
                ports = self.usb.ports()
                if len(ports) != 1:
                    raise ProviderError("connect_one_waveshare_usb")
                self.usb.close()
                target = "muse" if provider == "muse" else "face-lab"
                board_runtime.switch(ports[0], target)
                self._runtime = {"firmware": target}
                self.automatic.usb_paused = target == "muse"
                self.automatic.paused = False
                self.automatic.retry_at = 0
                self.automatic.reset_button()
                return self._runtime
            finally:
                self._request_lock.release()

    def configure(self, body):
        with self.automatic.lock:
            if self.voice.status()["active"]:
                raise ProviderError("stop_voice_mode_first")
            with self._config_lock:
                previous = self.settings.value.provider
                updated = self.settings.update(body)
            self.automatic.reset_button()
            if previous != updated["provider"] and updated["provider"] in ("gemini", "ollama"):
                self.automatic.paused = False
                self.automatic.retry_at = 0
            return updated

    def chat(self, body):
        if not isinstance(body, dict) or set(body) != {"text"}:
            raise ProviderError("invalid_request")
        validate_prompt(body["text"])
        if not self._request_lock.acquire(blocking=False):
            raise ProviderError("request_in_progress")
        try:
            with self._config_lock:
                settings = self.settings.value
            if settings.provider == "muse":
                ports = self.usb.ports()
                if len(ports) != 1:
                    raise ProviderError("connect_one_waveshare_usb")
                self.usage.reserve(settings)
                if not self._runtime_lock.acquire(blocking=False):
                    raise ProviderError("request_in_progress")
                try:
                    text = board_runtime.muse_chat(ports[0], body["text"])
                finally:
                    self._runtime_lock.release()
                return {"text": text, "provider": "muse", "model": "Muse",
                        "is_mock": False, "device_delivery": "muse_text"}
            if settings.provider == "mock":
                provider = MockProvider()
            else:
                provider = self._provider_factory(settings.provider_config())
                local = urlsplit(settings.base_url).hostname in ("localhost", "127.0.0.1", "::1")
                if settings.provider == "gemini" and not settings.gemini_free_tier_confirmed:
                    raise ProviderError("confirm_gemini_free_tier_project_first")
                if settings.provider != "gemini" and not local and not settings.remote_budget_confirmed:
                    raise ProviderError("configure_provider_spend_cap_first")
            self.usage.reserve(settings)  # Failed upstream attempts remain counted; no automatic retry.
            if settings.provider == "ollama" and settings.model in OLLAMA_IMAGE_MODELS:
                self.usb.show_activity("drawing")
                try:
                    image = self.generate_image(body["text"])
                except ProviderError:
                    self.usb.show_activity("error")
                    raise
                delivery = self.usb.show_image(image["png"])
                if delivery != "image_sent":
                    self.usb.show_activity("done")
                    self.usb.show_reply("Image ready in Control Room.", "ollama")
                return {"text": "Image ready.", "provider": "ollama", "model": settings.model, "is_mock": False,
                        "device_delivery": delivery, "image_id": image["id"]}
            if settings.provider == "ollama":
                self.usb.show_reply(body["text"], "ollama-prompt")
            self.usb.show_activity("thinking")
            try:
                if settings.provider == "openrouter":
                    provider.verify_spend_cap(settings.max_key_budget_usd)
                reply = provider.complete(body["text"])
            except ProviderError:
                self.usb.show_activity("error")
                raise
            self.usb.show_activity("done")
            return {"text": reply.text, "provider": reply.provider, "model": reply.model,
                    "is_mock": reply.provider == "mock",
                    "device_delivery": self.usb.show_reply(reply.text, reply.provider)}
        finally:
            self._request_lock.release()
