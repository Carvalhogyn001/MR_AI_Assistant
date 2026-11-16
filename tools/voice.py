#!/usr/bin/env python3
"""Explicit Gemini greeting through the board; no audio/key/transcript files."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from mr_robot_backend.gateway import Gateway
from mr_robot_backend.gemini_live import GeminiLive, LIVE_MODEL
from mr_robot_backend.providers import ProviderError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("greet",))
    parser.add_argument("--port")
    args = parser.parse_args()
    gateway = Gateway(ROOT / "private/host")
    audio = None
    try:
        settings = gateway.settings.value
        if settings.provider != "gemini" or not settings.api_key or not settings.gemini_free_tier_confirmed:
            raise ProviderError("confirmed_free_gemini_connection_required")
        gateway.usb.connect(args.port)
        gateway.usage.reserve(settings)
        print(json.dumps({"stage": "generating", "model": LIVE_MODEL}), flush=True)
        audio = GeminiLive(settings.api_key, settings.max_output_tokens).exchange(
            text="Say exactly: Hello! I am Mr. Robot. Our Gemini voice connection is ready.")
        print(json.dumps({"stage": "transferring", "audio_seconds": len(audio) / 48000}), flush=True)
        with gateway.usb.voice_session() as device:
            device.request("arm")
            result = device.play(audio)
        print(json.dumps({"model": LIVE_MODEL, "audio_seconds": len(audio) / 48000,
                          "device_phase": result.get("phase"), "played_turns": result.get("turns")}))
        return 0
    except (ProviderError, OSError, RuntimeError, ValueError, TimeoutError) as error:
        code = str(error) if isinstance(error, ProviderError) else "voice_device_failed"
        print(json.dumps({"ok": False, "error": code}), file=sys.stderr)
        return 1
    finally:
        if isinstance(audio, bytearray):
            audio[:] = b"\0" * len(audio)
        gateway.usb.close()


if __name__ == "__main__":
    raise SystemExit(main())
