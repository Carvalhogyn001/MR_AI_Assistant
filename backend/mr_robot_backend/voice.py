"""Explicit voice sessions with local follow-up detection and bounded turns."""
from contextlib import ExitStack, suppress
import threading
import time

from .gemini_live import GeminiLive, LIVE_MODEL, LIVE_VOICE
from .providers import OLLAMA_IMAGE_MODELS, OLLAMA_TRANSCRIBED_MODELS, OLLAMA_VOICE_MODELS, ProviderError
from .voice_capture import capture_turn
from .wake_word import WakeWord
from tools.voice_device import normalize_speech


class VoiceController:
    def __init__(self, gateway, live_factory=GeminiLive):
        self.gateway, self._factory = gateway, live_factory
        self._lock = threading.Lock()
        self._cancel = threading.Event()
        self._thread = None
        self._state = {"active": False, "stage": "off", "turns": 0, "model": LIVE_MODEL,
                       "voice_name": LIVE_VOICE, "mode": "tap", "error": None}

    def status(self):
        with self._lock:
            return dict(self._state)

    def _update(self, **values):
        with self._lock:
            self._state.update(values)

    def start(self, mode="tap"):
        if mode not in ("tap", "wake", "auto", "local", "image"):
            raise ProviderError("invalid_voice_mode")
        with self._lock:
            if self._state["active"]:
                return dict(self._state)
            with self.gateway._config_lock:
                settings = self.gateway.settings.value
            local = mode in ("local", "image")
            if local:
                if settings.provider != "ollama" or settings.model not in OLLAMA_VOICE_MODELS:
                    raise ProviderError("local_voice_model_required")
                if (mode == "image") != (settings.model in OLLAMA_IMAGE_MODELS):
                    raise ProviderError("local_voice_model_required")
            else:
                if settings.provider != "gemini" or not settings.api_key:
                    raise ProviderError("configure_gemini_first")
                if not settings.gemini_free_tier_confirmed:
                    raise ProviderError("confirm_gemini_free_tier_project_first")
            if self.gateway.usage.count_today() >= settings.daily_requests:
                raise ProviderError("daily_request_limit")
            if not self.gateway._request_lock.acquire(blocking=False):
                raise ProviderError("request_in_progress")
            try:
                provider = (self.gateway._provider_factory(settings.provider_config()) if local
                            else self._factory(settings.api_key, settings.max_output_tokens))
                self._cancel.clear()
                self._state.update(active=True, stage="starting", turns=0, error=None, mode=mode,
                                   model=settings.model if local else LIVE_MODEL,
                                   voice_name=None if local else LIVE_VOICE,
                                   model_ms=None, reply_start_ms=None, reaction="neutral")
                self._thread = threading.Thread(target=self._run, args=(settings, provider, mode), daemon=True)
                self._thread.start()
            except BaseException:
                self._state.update(active=False, stage="off")
                self.gateway._request_lock.release()
                raise
            return dict(self._state)

    def stop(self, wait=False):
        self._cancel.set()
        if wait and self._thread:
            self._thread.join(timeout=26)
        return self.status()

    def _run(self, settings, provider, mode="tap"):
        pcm = normalized = audio = None
        try:
            with self.gateway.usb.voice_session() as device, ExitStack() as stack:
                if mode in ("local", "image"):
                    self._run_local(settings, provider, device, image=mode == "image")
                    return
                streaming = getattr(device, "streaming", False) is True
                conversation = streaming and getattr(device, "conversation", False) is True
                if mode in ("wake", "auto") and not streaming:
                    raise ProviderError("voice_stream_firmware_required")
                wake = WakeWord() if mode in ("wake", "auto") else None
                deadline = time.monotonic() + 600
                turns = 0
                live = None
                followup_until = None
                def stopped():
                    return self._cancel.is_set() or time.monotonic() >= deadline

                while not stopped() and turns < 10:
                    followup = followup_until is not None
                    if followup and time.monotonic() >= followup_until:
                        break
                    if not followup and not wake:
                        self._update(stage="waiting_for_tap")
                    if streaming:
                        pcm = capture_turn(device, None if followup else wake, stopped,
                                           lambda state: self._update(stage=state), followup_until=followup_until)
                        if pcm is None:
                            if followup:
                                break
                            device.clear()
                            continue
                    else:
                        pcm = device.record(stopped)
                    try:
                        normalized = normalize_speech(pcm)
                    except ValueError as error:
                        if not followup or str(error) != "voice_too_quiet":
                            raise
                        # Weak local audio should not end the conversation or
                        # generate a provider request. Keep the same idle deadline.
                        pcm[:] = b"\0" * len(pcm)
                        pcm = None
                        device.clear()
                        continue
                    self._update(stage="thinking", model_ms=None, reply_start_ms=None, reaction="neutral")
                    checked_at = 0.
                    device_cancelled = False

                    def cancelled():
                        nonlocal checked_at, device_cancelled
                        if stopped():
                            return True
                        now = time.monotonic()
                        if now - checked_at >= .2:
                            device_cancelled = device.request("status", timeout=2).get("phase") != "thinking"
                            checked_at = now
                        return device_cancelled

                    if cancelled():
                        raise ProviderError("voice_cancelled")
                    self.gateway.usage.reserve(settings)
                    request_started = time.monotonic()
                    def show_reaction(reaction):
                        device.show_reaction(reaction)
                        self._update(reaction=reaction)

                    if conversation:
                        if live is None:
                            live = stack.enter_context(provider.session(cancelled))
                        audio = live.exchange(pcm=normalized, cancelled=cancelled,
                                              on_reaction=show_reaction)
                    else:
                        audio = provider.exchange(pcm=normalized, cancelled=cancelled)
                    self._update(stage="sending_reply", model_ms=round(1000 * (time.monotonic() - request_started)))
                    device.play(audio, stopped, lambda: self._update(
                        stage="speaking", reply_start_ms=round(1000 * (time.monotonic() - request_started))))
                    turns += 1
                    if conversation:
                        followup_until = time.monotonic() + 15
                    self._update(turns=turns)
                    for value in (pcm, normalized, audio):
                        value[:] = b"\0" * len(value)
                    pcm = normalized = audio = None
        except ProviderError as error:
            if not self._cancel.is_set():
                self._update(error=str(error), stage="stopped")
        except (OSError, RuntimeError, ValueError, TimeoutError) as error:
            if not self._cancel.is_set():
                codes = ("voice_stream_checksum", "voice_stream_sequence", "voice_usb_timeout",
                         "voice_device_rejected", "voice_too_quiet")
                code = str(error)
                self._update(error=code if code in codes else "voice_device_or_input_error", stage="stopped")
        except Exception:
            self._update(error="voice_failed", stage="stopped")
        finally:
            for value in (pcm, normalized, audio):
                if isinstance(value, bytearray):
                    value[:] = b"\0" * len(value)
            with self._lock:
                self._state["active"] = False
                if not self._state["error"]:
                    self._state["stage"] = "off"
            self.gateway._request_lock.release()

    def _run_local(self, settings, provider, device, image=False):
        if not device.local_voice:
            raise ProviderError("local_voice_firmware_required")
        pcm = normalized = None
        try:
            try:
                wake = WakeWord() if image else None
                pcm = capture_turn(device, wake, self._cancel.is_set,
                                   lambda state: self._update(stage=state), immediate=not image, pause_blocks=16)
            except ValueError as error:
                if str(error) == "voice_device_rejected" and device.request("status", timeout=1).get("phase") == "idle":
                    return
                raise
            if pcm is None or self._cancel.is_set():
                return
            normalized = normalize_speech(pcm)
            self._update(stage="thinking")
            self.gateway.usage.reserve(settings)
            transcribe = settings.model in OLLAMA_TRANSCRIBED_MODELS
            reply = provider.complete_audio(normalized, transcribe=True) if transcribe else provider.complete_audio(normalized)
            if self._cancel.is_set() or device.request("status", timeout=2).get("phase") != "thinking":
                return
            device.clear()
            if transcribe:
                prompt = reply.text.strip()
                if prompt.casefold().strip(" .[]") in ("", "unclear", "no intelligible speech"):
                    raise ProviderError("local_prompt_unclear")
            if image:
                self._update(stage="generating_image")
                with suppress(OSError, RuntimeError, ValueError, TimeoutError):
                    if device.host_activity:
                        device.device.show_activity("drawing")
                    else:
                        device.show_local_reply("Generating image in Control Room.")
                try:
                    generated = self.gateway.generate_image(prompt)
                except ProviderError:
                    with suppress(OSError, RuntimeError, ValueError, TimeoutError):
                        device.device.show_activity("error")
                    raise
                self._update(turns=1)
                if not self._cancel.is_set():
                    # The generated picture remains available if USB was lost.
                    if self.gateway.usb.show_image(generated["png"], voice_device=device) != "image_sent":
                        with suppress(OSError, RuntimeError, ValueError, TimeoutError):
                            if device.host_activity:
                                device.device.show_activity("idle")
                            device.show_local_reply("Image ready in Control Room.")
            else:
                if transcribe:
                    device.show_local_reply("Preparing reply.")
                    reply = provider.complete(prompt)
                    if self._cancel.is_set():
                        return
                self._update(stage="sending_reply")
                device.show_local_reply(reply.text)
            self._update(turns=1)
        finally:
            for block in (pcm, normalized):
                if isinstance(block, bytearray):
                    block[:] = b"\0" * len(block)
