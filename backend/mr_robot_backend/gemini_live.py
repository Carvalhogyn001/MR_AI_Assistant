"""Bounded Gemini Live turns. Credentials, audio and transcripts stay out of logs."""
import base64
from contextlib import ExitStack, contextmanager
import json
import logging
import re
import time

from .providers import ProviderError
from .tls import verified_context

LIVE_MODEL = "gemini-3.8-live"
LIVE_VOICE = "Charon"
ENDPOINT = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
MAX_INPUT = 256000
MAX_AUDIO = 960000


def reaction_for(transcript):
    """Choose a fixed display expression from conversational cues."""
    if re.search(r"\b(sorry|tough|difficult|frustrating|upsetting)\b", transcript, re.I):
        return "soft"
    if re.search(r"\b(congratulations|well done|great job|wonderful|exciting|joke|funny)\b", transcript, re.I):
        return "happy"
    if "?" in transcript or re.search(r"\b(let.s explore|here.s why|works by|let.s look)\b", transcript, re.I):
        return "curious"
    return "neutral"


def validate_input(pcm, text):
    if (pcm is None) == (text is None):
        raise ProviderError("voice_input_required")
    if pcm is not None and (not isinstance(pcm, (bytes, bytearray)) or not 2 <= len(pcm) <= MAX_INPUT or len(pcm) % 2):
        raise ProviderError("voice_invalid_audio")
    if text is not None and (not isinstance(text, str) or not 1 <= len(text) <= 256):
        raise ProviderError("voice_invalid_text")


def check_turn(cancelled, deadline):
    if cancelled():
        raise ProviderError("voice_cancelled")
    if time.monotonic() >= deadline:
        raise ProviderError("voice_timeout")


def receive(ws, cancelled, deadline):
    while True:
        check_turn(cancelled, deadline)
        try:
            raw = ws.recv(timeout=min(1, max(.01, deadline - time.monotonic())))
        except TimeoutError:
            continue
        if not isinstance(raw, (str, bytes)) or len(raw) > 262144:
            raise ProviderError("voice_invalid_response")
        message = json.loads(raw)
        if not isinstance(message, dict) or "error" in message:
            raise ProviderError("voice_service_rejected")
        if "toolCall" in message or "goAway" in message:
            raise ProviderError("voice_unsupported_response")
        return message


class LiveSession:
    def __init__(self, ws, conversation):
        self._ws = ws
        self._conversation = conversation
        self._used = False

    def exchange(self, pcm=None, text=None, cancelled=lambda: False, on_reaction=None):
        validate_input(pcm, text)
        if self._used and not self._conversation:
            raise ProviderError("voice_session_finished")
        self._used = True
        deadline = time.monotonic() + 45
        audio = bytearray()
        transcript = ""
        try:
            check_turn(cancelled, deadline)
            if text is not None:
                self._ws.send(json.dumps({"clientContent": {"turns": [{"role": "user", "parts": [{"text": text}]}], "turnComplete": True}}))
            else:
                self._ws.send(json.dumps({"realtimeInput": {"activityStart": {}}}))
                for offset in range(0, len(pcm), 8192):
                    check_turn(cancelled, deadline)
                    self._ws.send(json.dumps({"realtimeInput": {"audio": {"mimeType": "audio/pcm;rate=16000",
                                                    "data": base64.b64encode(pcm[offset:offset + 8192]).decode("ascii")}}}))
                self._ws.send(json.dumps({"realtimeInput": {"activityEnd": {}}}))

            while True:
                message = receive(self._ws, cancelled, deadline)
                content = message.get("serverContent", {})
                if not isinstance(content, dict) or content.get("interrupted"):
                    raise ProviderError("voice_interrupted")
                output_text = content.get("outputTranscription")
                if on_reaction and isinstance(output_text, dict) and isinstance(output_text.get("text"), str):
                    transcript += output_text["text"][:max(0, 2048 - len(transcript))]
                for part in content.get("modelTurn", {}).get("parts", []):
                    if "functionCall" in part:
                        raise ProviderError("voice_unsupported_response")
                    if "inlineData" in part:
                        data = part["inlineData"]
                        if data.get("mimeType") != "audio/pcm;rate=24000":
                            raise ProviderError("voice_unsupported_audio")
                        decoded = base64.b64decode(data["data"], validate=True)
                        if len(decoded) % 2 or len(audio) + len(decoded) > MAX_AUDIO:
                            raise ProviderError("voice_audio_limit")
                        audio.extend(decoded)
                complete = content.get("turnComplete") or (
                    not self._conversation and content.get("generationComplete"))
                if complete:
                    if not audio:
                        raise ProviderError("voice_no_audio")
                    if on_reaction:
                        on_reaction(reaction_for(transcript))
                    return audio
        except ProviderError:
            audio[:] = b"\0" * len(audio)
            raise
        except Exception:
            audio[:] = b"\0" * len(audio)
            raise ProviderError("voice_connection_failed") from None


class GeminiLive:
    def __init__(self, key, max_tokens=256, connector=None):
        if not isinstance(key, str) or not key or len(key) > 8192 or any(not 33 <= ord(c) <= 126 for c in key):
            raise ProviderError("invalid_api_key")
        if type(max_tokens) is not int or not 16 <= max_tokens <= 512:
            raise ProviderError("invalid_token_limit")
        if connector is None:
            from websockets.sync.client import connect
            connector = connect
        self._connector, self._key, self._max_tokens = connector, key, max_tokens

    @contextmanager
    def session(self, cancelled, conversation=True):
        logger = logging.Logger("mr_robot_private_websocket", level=logging.CRITICAL + 1)
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
        deadline = time.monotonic() + 45
        check_turn(cancelled, deadline)
        # Only translate exceptions from the upstream connection and setup.
        with ExitStack() as stack:
            try:
                ws = stack.enter_context(self._connector(
                    ENDPOINT, additional_headers={"x-goog-api-key": self._key},
                    ssl=verified_context(), proxy=None, compression=None, open_timeout=8,
                    close_timeout=1, ping_interval=10, ping_timeout=10,
                    max_size=262144, max_queue=4, logger=logger, legacy=True))
                setup = {"model": "models/" + LIVE_MODEL,
                         "generationConfig": {
                             "responseModalities": ["AUDIO"], "maxOutputTokens": self._max_tokens,
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": LIVE_VOICE}}},
                         },
                         "systemInstruction": {"parts": [{"text": "You are Mr. Robot, a friendly desk companion. Answer briefly in one or two short sentences. Use the earlier turns in this session when relevant. Do not claim you performed actions or controlled hardware. You have no tools."}]},
                         "realtimeInputConfig": {"automaticActivityDetection": {"disabled": True}}}
                if conversation:
                    setup["outputAudioTranscription"] = {}
                ws.send(json.dumps({"setup": setup}))
                if "setupComplete" not in receive(ws, cancelled, deadline):
                    raise ProviderError("voice_setup_failed")
            except ProviderError:
                raise
            except Exception:
                raise ProviderError("voice_connection_failed") from None
            yield LiveSession(ws, conversation)

    def exchange(self, pcm=None, text=None, cancelled=lambda: False):
        validate_input(pcm, text)
        with self.session(cancelled, conversation=False) as session:
            return session.exchange(pcm, text, cancelled)
