"""RAM-only audio over one existing Face Lab USB connection; no automatic retries."""
import array
import json
import math
import re
import secrets
import sys
import time
import zlib

INPUT_BYTES = 256000
OUTPUT_BYTES = 960000
CHUNK = 512
STREAM_BYTES = 2048
BULK_BYTES = 4096


class VoiceDevice:
    def __init__(self, device, streaming=False, conversation=False, local_voice=False, host_activity=False, image_display=False):
        self.device = device
        self.connection = device.connection
        self.local_voice = local_voice
        self.host_activity = host_activity
        self.image_display = image_display
        self.session = secrets.randbelow(65535) + 1
        self.streaming = streaming
        self.conversation = conversation
        self.sequence = 0

    def request(self, operation, *values, timeout=12, payload=b"", trigger=False):
        if operation not in ("arm", "arm-fast", "watch", "local", "follow", "react", "trigger", "sample", "finish",
                              "status", "clear", "thinking", "read", "begin", "write", "bulk", "play"):
            raise ValueError("invalid_voice_operation")
        command = "MRV1 " + str(self.session) + " " + operation + "".join(" " + str(v) for v in values) + "\n"
        if trigger:
            if operation != "sample":
                raise ValueError("voice_trigger_requires_sample")
            command = f"MRV1 {self.session} trigger\n" + command
        if len(command) > 1153 or not command.isascii():
            raise ValueError("invalid_voice_command")
        if payload and (operation != "bulk" or len(payload) > BULK_BYTES):
            raise ValueError("invalid_voice_payload")
        frame = command.encode("ascii") + payload
        if self.connection.write(frame) != len(frame):
            raise OSError("voice_usb_short_write")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            raw = self.connection.readline(1537)
            if len(raw) > 1536 or not raw.startswith(b"MRV1 ") or not raw.endswith(b"\n"):
                continue
            try:
                value = json.loads(raw[5:])
            except (ValueError, UnicodeError):
                continue
            if not isinstance(value, dict) or value.get("id") != self.session:
                continue
            if value.get("ok") is not True:
                raise ValueError("voice_device_rejected")
            if operation == "sample" and "pcm" not in value:
                continue
            return value
        raise TimeoutError("voice_usb_timeout")

    def stream_start(self, wake, followup=False, immediate=False):
        self.sequence = 0
        operation = "local" if immediate else "follow" if followup else "watch" if wake else "arm-fast"
        phase = "recording" if followup or immediate else "wake" if wake else "ready"
        if self.confirm(operation, timeout=3).get("phase") != phase:
            raise ValueError("voice_device_rejected")

    def show_local_reply(self, text):
        self.device.request("caption", ("ollama", text), timeout=3)

    def show_reaction(self, reaction):
        code = {"neutral": 0, "happy": 1, "curious": 2, "soft": 3}[reaction]
        if self.confirm("react", code, timeout=.6).get("phase") != "thinking":
            raise ValueError("voice_device_rejected")

    def confirm(self, operation, *values, timeout, payload=b""):
        """Read state after a missed acknowledgement without repeating the action."""
        try:
            return self.request(operation, *values, timeout=timeout, payload=payload)
        except TimeoutError:
            return self.request("status", timeout=1)

    def sample(self, trigger=False):
        # The next PCM header confirms the recording transition even if the
        # preceding control acknowledgement is lost on native USB.
        meta = self.request("sample", timeout=2, trigger=trigger)
        if trigger and meta.get("phase") != "recording":
            raise ValueError("voice_trigger_not_confirmed")
        if meta.get("pcm") != STREAM_BYTES or meta.get("sequence") != self.sequence + 1:
            raise ValueError("voice_stream_sequence")
        deadline = time.monotonic() + 1
        pcm = bytearray()
        try:
            while len(pcm) < STREAM_BYTES and time.monotonic() < deadline:
                pcm.extend(self.connection.read(STREAM_BYTES - len(pcm)))
            if len(pcm) != STREAM_BYTES or zlib.crc32(pcm) != meta.get("crc32"):
                raise ValueError("voice_stream_checksum")
            self.sequence += 1
            return meta["phase"], pcm
        except BaseException:
            pcm[:] = b"\0" * len(pcm)
            raise

    def record(self, cancelled=lambda: False):
        self.request("arm")
        deadline = time.monotonic() + 65
        while time.monotonic() < deadline:
            if cancelled():
                raise ValueError("voice_cancelled")
            state = self.request("status")
            if state.get("phase") == "thinking" and state.get("bytes") == INPUT_BYTES:
                break
            if state.get("phase") not in ("ready", "recording"):
                raise ValueError("voice_cancelled_or_expired")
            time.sleep(.1)
        else:
            raise TimeoutError("voice_tap_timeout")
        audio = bytearray()
        try:
            for offset in range(0, INPUT_BYTES, CHUNK):
                if cancelled():
                    raise ValueError("voice_cancelled")
                reply = self.request("read", offset)
                data = reply.get("data")
                expected = min(CHUNK, INPUT_BYTES - offset)
                if reply.get("offset") != offset or not isinstance(data, str) or not re.fullmatch(r"[0-9a-f]{" + str(expected * 2) + "}", data):
                    raise ValueError("voice_input_frame_invalid")
                audio.extend(bytes.fromhex(data))
            if zlib.crc32(audio) != state.get("crc32"):
                raise ValueError("voice_input_checksum_failed")
            self.request("thinking")
            return audio
        except BaseException:
            audio[:] = b"\0" * len(audio)
            raise

    def play(self, audio, cancelled=lambda: False, on_play=lambda: None):
        if not isinstance(audio, (bytes, bytearray)) or not 2 <= len(audio) <= OUTPUT_BYTES or len(audio) % 2:
            raise ValueError("invalid_voice_output")
        checksum = zlib.crc32(audio)
        if self.streaming:
            initial = self.confirm("begin", len(audio), checksum, timeout=.6)
            if (initial.get("phase"), initial.get("expected"), initial.get("crc32"), initial.get("bytes")) != (
                "receiving", len(audio), checksum, 0
            ):
                raise ValueError("voice_output_begin_failed")
        else:
            self.request("begin", len(audio), checksum)
        chunk_bytes = BULK_BYTES if self.streaming else CHUNK
        for offset in range(0, len(audio), chunk_bytes):
            if cancelled():
                raise ValueError("voice_cancelled")
            block = audio[offset:offset + chunk_bytes]
            if self.streaming:
                reply = self.confirm("bulk", offset, len(block), payload=block, timeout=.6)
                if reply.get("phase") != "receiving":
                    raise ValueError("voice_output_phase_failed")
            else:
                reply = self.request("write", offset, block.hex())
            if reply.get("bytes") != min(offset + chunk_bytes, len(audio)):
                raise ValueError("voice_output_offset_failed")
        if cancelled():
            raise ValueError("voice_cancelled")
        on_play()
        if not self.streaming:
            return self.request("play", timeout=25)
        result = self.confirm("play", timeout=25)
        if result.get("phase") != "idle" or result.get("turns") != initial.get("turns", -1) + 1:
            raise ValueError("voice_playback_not_confirmed")
        return result

    def clear(self):
        return self.request("clear")


def normalize_speech(pcm):
    """Bound gain on the verified MIC1 slot; refuse near-silence before cloud use."""
    samples = array.array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    rms = math.sqrt(sum(v * v for v in samples) / max(1, len(samples)))
    peak = max((abs(v) for v in samples), default=0)
    if rms < 20 or not peak:
        raise ValueError("voice_too_quiet")
    gain = min(16, 12000 / peak)
    for i, value in enumerate(samples):
        samples[i] = max(-32768, min(32767, int(value * gain)))
    if sys.byteorder != "little":
        samples.byteswap()
    result = bytearray(samples.tobytes())
    for i in range(len(samples)):
        samples[i] = 0
    return result
