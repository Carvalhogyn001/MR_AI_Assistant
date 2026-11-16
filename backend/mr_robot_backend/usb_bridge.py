"""One reusable USB connection; UI calls never construct shell commands."""
import threading
from contextlib import contextmanager

from .device_image import image_pixels
from .providers import ProviderError


class UsbBridge:
    def __init__(self):
        self._device = None
        self._lock = threading.Lock()
        self._voice_busy = False
        self._last_state = {}

    def ports(self):
        try:
            from serial.tools import list_ports
            return [p.device for p in list_ports.comports() if (p.vid, p.pid) == (0x303A, 0x1001)]
        except ImportError:
            return []

    def status(self):
        with self._lock:
            return self._status()

    def _status(self):
        result = {"connected": self._device is not None, "ports": self.ports()}
        if self._device:
            if self._voice_busy:
                return {**result, "state": self._last_state, "voice_busy": True}
            try:
                result["state"] = self._device.request("status", timeout=7)
                self._last_state = result["state"]
            except (OSError, RuntimeError, TimeoutError, ValueError):
                self._device.__exit__()
                self._device = None
                result.update(connected=False, error="usb_disconnected")
        return result

    def connect(self, port=None):
        from tools.device import Device
        with self._lock:
            if self._device:
                return self._status()
            ports = self.ports()
            if port is None and len(ports) == 1:
                port = ports[0]
            if port not in ports:
                raise ProviderError("connect_one_waveshare_usb")
            try:
                self._device = Device(port).__enter__()
                return self._status()
            except (OSError, RuntimeError, TimeoutError, ValueError):
                self._device = None
                raise ProviderError("usb_connection_failed") from None

    def command(self, operation, value=None):
        if operation not in ("face", "expression", "brightness", "tone", "mic-arm", "mic-cancel", "screen"):
            raise ProviderError("unsupported_device_command")
        with self._lock:
            if self._voice_busy:
                raise ProviderError("voice_mode_owns_usb")
            if not self._device:
                raise ProviderError("usb_not_connected")
            try:
                return self._device.request(operation, value, timeout=7)
            except (OSError, RuntimeError, TimeoutError, ValueError):
                raise ProviderError("usb_command_failed") from None

    def close(self):
        with self._lock:
            if self._voice_busy:
                raise ProviderError("stop_voice_mode_first")
            if self._device:
                try:
                    if self._device.request("status", timeout=1).get("caption_supported"):
                        self._device.request("caption-clear", timeout=1)
                    self._device.request("mic-cancel", timeout=1)
                except (OSError, RuntimeError, TimeoutError, ValueError):
                    pass
                self._device.__exit__()
                self._device = None

    def show_reply(self, text, provider):
        with self._lock:
            if self._voice_busy:
                return "voice_mode_busy"
            if not self._device:
                return "not_connected"
            try:
                state = self._device.request("status", timeout=3)
                if not state.get("caption_supported"):
                    return "unsupported_firmware"
                if provider in ("ollama", "ollama-prompt") and not state.get("paged_caption_supported"):
                    if provider == "ollama-prompt":
                        return "unsupported_firmware"
                    provider = "compatible"
                self._device.request("caption", (provider, text), timeout=3)
                return "sent"
            except (OSError, RuntimeError, TimeoutError, ValueError):
                return "failed"

    def show_activity(self, activity):
        with self._lock:
            if self._voice_busy or not self._device or not self._last_state.get("activity_supported"):
                return
            try:
                self._last_state = self._device.show_activity(activity)
            except (OSError, RuntimeError, TimeoutError, ValueError):
                pass

    def show_image(self, png, *, voice_device=None):
        try:
            pixels = image_pixels(png, 300)
            if voice_device is not None:
                if voice_device.image_display:
                    voice_device.device.send_image(pixels)
                    return "image_sent"
                return "unsupported_firmware"
            with self._lock:
                if self._voice_busy:
                    return "voice_mode_busy"
                if not self._device:
                    return "not_connected"
                if not self._last_state.get("image_supported"):
                    return "unsupported_firmware"
                self._device.send_image(pixels)
                return "image_sent"
        except (ImportError, OSError, RuntimeError, TimeoutError, ValueError):
            return "failed"

    @contextmanager
    def voice_session(self):
        from tools.voice_device import VoiceDevice
        with self._lock:
            if self._voice_busy or not self._device:
                raise ProviderError("usb_not_connected")
            self._last_state = self._device.request("status")
            if self._last_state.get("voice_supported") is not True:
                raise ProviderError("voice_firmware_required")
            self._voice_busy = True
            voice = VoiceDevice(self._device, streaming=self._last_state.get("voice_stream_supported") is True,
                                conversation=self._last_state.get("voice_conversation_supported") is True,
                                local_voice=self._last_state.get("local_voice_supported") is True,
                                host_activity=self._last_state.get("activity_supported") is True,
                                image_display=self._last_state.get("image_supported") is True)
        try:
            yield voice
        finally:
            try:
                voice.clear()
            except (OSError, RuntimeError, ValueError, TimeoutError):
                pass
            with self._lock:
                self._voice_busy = False
