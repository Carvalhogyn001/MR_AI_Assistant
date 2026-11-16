import base64
import json
from pathlib import Path
import tempfile
import unittest
import zlib
from unittest.mock import MagicMock, patch

from mr_robot_backend.gemini_live import GeminiLive, ENDPOINT
from mr_robot_backend.gateway import Gateway
from mr_robot_backend.providers import ProviderError
from mr_robot_backend.voice_capture import capture_turn
from tools.voice_device import VoiceDevice, normalize_speech

KEY = "synthetic-private-key"


def message(audio=b"\x01\x00" * 20, complete=True):
    return json.dumps({"serverContent": {"modelTurn": {"parts": [
        {"text": "synthetic private transcript"},
        {"inlineData": {"mimeType": "audio/pcm;rate=24000", "data": base64.b64encode(audio).decode()}}]}, "turnComplete": complete}})


class VoiceTests(unittest.TestCase):
    def provider(self, messages):
        self.connector = MagicMock()
        self.ws = self.connector.return_value.__enter__.return_value
        self.ws.recv.side_effect = [json.dumps({"setupComplete": {}}), *messages]
        return GeminiLive(KEY, connector=self.connector)

    def test_live_audio_round_trip_is_single_connection_no_tools_and_key_only_in_header(self):
        provider = self.provider([message()])
        result = provider.exchange(pcm=b"\x01\x00" * 200)
        self.assertEqual(result, b"\x01\x00" * 20)
        self.connector.assert_called_once()
        args, options = self.connector.call_args
        self.assertEqual(args, (ENDPOINT,))
        self.assertNotIn(KEY, ENDPOINT)
        self.assertEqual(options["additional_headers"], {"x-goog-api-key": KEY})
        self.assertIsNone(options["proxy"])
        self.assertTrue(options["ssl"].check_hostname)
        sent = [json.loads(call.args[0]) for call in self.ws.send.call_args_list]
        self.assertNotIn("tools", sent[0]["setup"])
        self.assertNotIn("thinkingConfig", sent[0]["setup"]["generationConfig"])
        speech = sent[0]["setup"]["generationConfig"]["speechConfig"]
        self.assertEqual(speech["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"], "Charon")
        self.assertIn("activityStart", sent[1]["realtimeInput"])
        self.assertIn("activityEnd", sent[-1]["realtimeInput"])
        self.assertNotIn(KEY, str(sent))

    def test_bad_response_large_audio_wrong_rate_and_tools_are_redacted_without_retry(self):
        cases = ["bad json", json.dumps({"error": {"message": KEY}}),
                 json.dumps({"toolCall": {"secret": KEY}}), message(b"a"),
                 message().replace("24000", "16000"),
                 json.dumps({"serverContent": {"turnComplete": True}})]
        for raw in cases:
            with self.subTest(raw=raw[:20]):
                provider = self.provider([raw])
                with self.assertRaises(ProviderError) as error:
                    provider.exchange(text="Hello")
                self.assertNotIn(KEY, str(error.exception))
                self.connector.assert_called_once()

    def test_followup_reuses_connection_and_waits_for_turn_complete(self):
        first = json.loads(message(complete=False))
        first["serverContent"]["generationComplete"] = True
        first["serverContent"]["outputTranscription"] = {"text": "Well done!"}
        complete = json.dumps({"serverContent": {"turnComplete": True}})
        provider = self.provider([json.dumps(first), complete, message(b"\x02\0" * 20)])
        reaction = MagicMock()
        with provider.session(lambda: False) as session:
            self.assertEqual(session.exchange(pcm=b"\x40\0" * 100, on_reaction=reaction), b"\x01\0" * 20)
            self.assertEqual(session.exchange(pcm=b"\x50\0" * 100, on_reaction=reaction), b"\x02\0" * 20)
        self.connector.assert_called_once()
        self.assertEqual([call.args[0] for call in reaction.call_args_list], ["happy", "neutral"])

    def test_host_waits_for_speech_after_playback_and_ends_on_silence(self):
        with tempfile.TemporaryDirectory() as directory:
            gateway = Gateway(Path(directory))
            usb = gateway.usb.voice_session = MagicMock()
            device = usb.return_value.__enter__.return_value
            device.streaming = device.conversation = True
            device.request.return_value = {"phase": "thinking"}
            provider = MagicMock()
            live = provider.session.return_value.__enter__.return_value
            live.exchange.side_effect = [bytearray(4), bytearray(4)]
            capture_audio = [bytearray(b"\x60\0" * 200), bytearray(400), bytearray(b"\x60\0" * 200)]
            gateway._request_lock.acquire()
            with patch("mr_robot_backend.voice.capture_turn", side_effect=[*capture_audio, None]) as capture:
                gateway.voice._run(gateway.settings.value, provider)
            provider.session.assert_called_once()
            deadlines = [call.kwargs["followup_until"] for call in capture.call_args_list]
            self.assertIsNone(deadlines[0])
            self.assertEqual(deadlines[1], deadlines[2])
            self.assertGreaterEqual(deadlines[3], deadlines[2])
            device.clear.assert_called_once()
            self.assertEqual(live.exchange.call_count, 2)
            self.assertEqual(device.play.call_count, 2)
            self.assertEqual(gateway.voice.status()["stage"], "off")
            self.assertEqual(gateway.voice.status()["turns"], 2)
            self.assertTrue(all(not any(block) for block in capture_audio))

    def test_preflight_cancel_and_input_limits_do_not_connect(self):
        provider = self.provider([])
        with self.assertRaisesRegex(ProviderError, "voice_cancelled"):
            provider.exchange(text="Hello", cancelled=lambda: True)
        for pcm in (b"", b"a", b"x" * 256002):
            with self.assertRaises(ProviderError):
                provider.exchange(pcm=pcm)
        self.connector.assert_not_called()

    def test_cumulative_output_limit_is_enforced_across_many_messages(self):
        provider = self.provider([message(b"\0" * 180000, complete=False)] * 6)
        with self.assertRaisesRegex(ProviderError, "voice_audio_limit"):
            provider.exchange(text="Hello")
        self.connector.assert_called_once()

    def test_local_hardware_press_starts_capture_and_delivers_text(self):
        with tempfile.TemporaryDirectory() as directory:
            gateway = Gateway(Path(directory))
            gateway.configure({"provider": "ollama", "model": "gemma4:12b"})
            device = MagicMock()
            device.local_voice = True
            device.request.return_value = {"phase": "thinking"}
            gateway.usb.voice_session = MagicMock()
            gateway.usb.voice_session.return_value.__enter__.return_value = device
            provider = MagicMock()
            provider.complete_audio.return_value.text = "Twelve."
            gateway._request_lock.acquire()
            with patch("mr_robot_backend.voice.capture_turn", return_value=bytearray(b"\x60\0" * 200)) as capture:
                gateway.voice._run(gateway.settings.value, provider, "local")
            self.assertTrue(capture.call_args.kwargs["immediate"])
            provider.complete_audio.assert_called_once()
            device.show_local_reply.assert_called_once_with("Twelve.")
            device.play.assert_not_called()
            self.assertEqual(gateway.voice.status()["turns"], 1)
            self.assertFalse(gateway._request_lock.locked())

    def test_busy_usb_returns_cached_metadata_and_refuses_other_controls(self):
        from mr_robot_backend.usb_bridge import UsbBridge
        bridge = UsbBridge()
        bridge._device = MagicMock()
        bridge._voice_busy = True
        bridge._last_state = {"firmware": "face-lab-0.8.0"}
        self.assertTrue(bridge.status()["voice_busy"])
        bridge._device.request.assert_not_called()
        with self.assertRaisesRegex(ProviderError, "voice_mode_owns_usb"):
            bridge.command("tone")
        with self.assertRaisesRegex(ProviderError, "stop_voice_mode_first"):
            bridge.close()

    def test_audio_normalization_refuses_silence_and_bounds_gain(self):
        with self.assertRaisesRegex(ValueError, "voice_too_quiet"):
            normalize_speech(b"\0" * 100)
        normalized = normalize_speech(b"\x64\0" * 100)
        self.assertEqual(len(normalized), 200)
        self.assertEqual(int.from_bytes(normalized[:2], "little", signed=True), 1600)

    def test_checksum_failure_never_returns_captured_speech(self):
        voice = VoiceDevice(MagicMock())
        voice.request = MagicMock(side_effect=[{}, {"phase": "thinking", "bytes": 256000, "crc32": 1}] +
                                  [{"offset": i, "data": "0000" * (min(512, 256000-i)//2)} for i in range(0, 256000, 512)])
        with self.assertRaisesRegex(ValueError, "voice_input_checksum_failed"):
            voice.record()
        self.assertNotIn("thinking", [call.args[0] for call in voice.request.call_args_list])

    def test_corrupt_live_block_is_rejected_before_recognition(self):
        voice = VoiceDevice(MagicMock(), streaming=True)
        voice.request = MagicMock(return_value={"pcm": 2048, "sequence": 1, "crc32": 0, "phase": "wake"})
        voice.connection.read.return_value = b"\0" * 2048
        with self.assertRaisesRegex(ValueError, "voice_stream_checksum"):
            voice.sample()
        self.assertEqual(voice.sequence, 0)

    def test_short_question_ends_after_pause_and_stops_the_mic(self):
        device = MagicMock()
        device.request.return_value = {"phase": "recording"}
        device.confirm.return_value = {"phase": "thinking"}
        blocks = [bytearray(b"\x64\0" * 1024) for _ in range(4)]
        blocks += [bytearray(2048) for _ in range(10)]
        device.sample.side_effect = [("recording", block) for block in blocks]
        speech = capture_turn(device, None, lambda: False, MagicMock())
        self.assertEqual(len(speech), 14 * 2048)
        self.assertTrue(all(not any(block) for block in blocks))
        device.confirm.assert_called_with("finish", timeout=.5)

    def test_recording_block_confirms_trigger_with_no_separate_ack(self):
        voice = VoiceDevice(MagicMock(), streaming=True)
        block = bytes(2048)
        voice.connection.write.side_effect = len
        metadata = {"id": voice.session, "ok": True, "phase": "recording",
                    "sequence": 1, "pcm": len(block), "crc32": zlib.crc32(block)}
        voice.connection.readline.return_value = b"MRV1 " + json.dumps(metadata).encode() + b"\n"
        voice.connection.read.return_value = block
        phase, pcm = voice.sample(trigger=True)
        self.assertEqual((phase, pcm), ("recording", block))
        self.assertEqual(voice.connection.write.call_count, 1)

    def test_missing_bulk_ack_checks_offset_without_resending_audio(self):
        voice = VoiceDevice(MagicMock(), streaming=True)
        audio = bytes(4096)
        voice.request = MagicMock(side_effect=[
            {"phase": "receiving", "expected": len(audio), "crc32": zlib.crc32(audio),
             "bytes": 0, "turns": 4},
            TimeoutError("voice_usb_timeout"),
            {"phase": "receiving", "bytes": len(audio)},
            {"phase": "idle", "turns": 5},
        ])
        self.assertEqual(voice.play(audio)["turns"], 5)
        self.assertEqual([call.args[0] for call in voice.request.call_args_list],
                         ["begin", "bulk", "status", "play"])

    def test_voice_start_requires_gemini_and_confirmed_free_project(self):
        with tempfile.TemporaryDirectory() as directory:
            gateway = Gateway(Path(directory))
            with self.assertRaisesRegex(ProviderError, "configure_gemini_first"):
                gateway.voice.start()
            gateway.configure({"provider": "gemini", "model": "gemini-3.8-flash", "api_key": KEY})
            with self.assertRaisesRegex(ProviderError, "confirm_gemini_free_tier_project_first"):
                gateway.voice.start()
            self.assertEqual(gateway.usage.count_today(), 0)
            self.assertFalse(gateway.voice.status()["active"])

    def test_quota_failure_after_tap_clears_audio_and_never_calls_live_service(self):
        with tempfile.TemporaryDirectory() as directory:
            gateway = Gateway(Path(directory))
            context = MagicMock()
            device = context.__enter__.return_value
            pcm = bytearray(b"\x64\0" * 200)
            device.record.return_value = pcm
            device.request.return_value = {"phase": "thinking"}
            gateway.usb.voice_session = MagicMock(return_value=context)
            gateway.usage.reserve = MagicMock(side_effect=ProviderError("daily_request_limit"))
            provider = MagicMock()
            gateway._request_lock.acquire()
            gateway.voice._run(gateway.settings.value, provider)
            provider.exchange.assert_not_called()
            device.play.assert_not_called()
            self.assertEqual(pcm, b"\0" * len(pcm))
            self.assertEqual(gateway.voice.status()["error"], "daily_request_limit")
            self.assertFalse(gateway.voice.status()["active"])
            self.assertFalse(gateway._request_lock.locked())
            context.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
