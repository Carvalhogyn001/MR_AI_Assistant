"""Keep local wake detection available without depending on a browser tab."""
from threading import Event, Lock, Thread
import time

from .providers import OLLAMA_IMAGE_MODELS, OLLAMA_VOICE_MODELS, ProviderError


class AutomaticVoice:
    def __init__(self, gateway):
        self.gateway = gateway
        self.lock = Lock()
        self._closed = Event()
        self._worker = None
        self.paused = False
        self.usb_paused = False
        self.retry_at = 0
        self.last_error = None
        self.error_delay = 0
        self.arm_error = None
        self._button_previous = None

    def start(self):
        self._worker = Thread(target=self._run, name="automatic-voice", daemon=True)
        self._worker.start()

    def close(self):
        self._closed.set()
        if self._worker:
            self._worker.join()

    def set_paused(self, paused):
        with self.lock:
            self.paused = paused
            self.retry_at = 0
            self.last_error = None
            self.error_delay = 0
            self.reset_button()
            if paused:
                self.gateway.voice.stop()

    def reset_button(self):
        self._button_previous = None
        self.arm_error = None

    def connect(self, port):
        with self.lock:
            result = self.gateway.usb.connect(port)
            self.usb_paused = False
            self.reset_button()
            self.retry_at = 0
            return result

    def disconnect(self):
        with self.lock:
            self.gateway.usb.close()
            self.usb_paused = True
            self._button_previous = None

    def _run(self):
        while not self._closed.is_set():
            with self.lock:
                self._step()
            self._closed.wait(.3 if self._button_previous is not None else 2)

    def _step(self):
        now = time.monotonic()
        if self.paused or self.usb_paused or now < self.retry_at:
            return
        if self.gateway._runtime["firmware"] == "muse":
            return
        with self.gateway._config_lock:
            config = self.gateway.settings.value
        local = config.provider == "ollama"
        image = local and config.model in OLLAMA_IMAGE_MODELS
        gemini = config.provider == "gemini" and config.api_key and config.gemini_free_tier_confirmed
        if not (local or gemini):
            if config.provider == "gemini":
                self.arm_error = "confirm_gemini_free_tier_project_first" if config.api_key else "configure_gemini_first"
            self._button_previous = None
            return
        voice = self.gateway.voice.status()
        if voice["active"]:
            return
        try:
            usb = self.gateway.usb.status()
            if not usb["connected"] and len(usb["ports"]) == 1:
                usb = self.gateway.usb.connect(usb["ports"][0])
                self.last_error = None
                self.error_delay = 0
                self._button_previous = None
            if not usb["connected"]:
                self._button_previous = None
                return
            if local and not image:
                self._local_button(usb["state"], config)
                return
            self._button_previous = None
            if not usb["state"].get("voice_stream_supported"):
                return
            if voice["error"] and voice["error"] != self.last_error:
                self.last_error = voice["error"]
                self.error_delay = 5
                self.retry_at = now + self.error_delay
                return
            if not voice["error"]:
                self.last_error = None
                self.error_delay = 0
            self.gateway.voice.start("image" if image else "auto")
            self.arm_error = None
            if voice["error"]:
                self.error_delay = min(60, max(5, self.error_delay * 2))
                self.retry_at = now + self.error_delay
        except ProviderError as error:
            if str(error) != "request_in_progress":
                self.arm_error = str(error)
            # Another explicit operation may temporarily own the request lock.
            self.retry_at = now + (60 if str(error) == "daily_request_limit" else 5)
        except (OSError, RuntimeError, ValueError):
            self.retry_at = now + 5

    def _local_button(self, state, config):
        if config.model not in OLLAMA_VOICE_MODELS or not state.get("local_voice_supported"):
            self._button_previous = None
            return
        if state.get("microphone_active") or state.get("microphone_armed"):
            self._button_previous = state.get("talk_button_presses")
            return
        count = state["talk_button_presses"]
        baseline = self._button_previous
        if baseline is not None and count > baseline:
            # Consume a press only as a fresh event; never send it after a busy
            # text request or use a press from an earlier provider selection.
            self._button_previous = None
            self.gateway.voice.start("local")
            self.arm_error = None
        else:
            self._button_previous = count
