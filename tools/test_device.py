#!/usr/bin/env python3
"""Lost USB replies may retry reads but must never automatically repeat sound or microphone capture."""
import unittest
from unittest.mock import patch
from device import Device, caption_value


class LostReplyConnection:
    def __init__(self):
        self.now = 0
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def flush(self):
        pass

    def readline(self, limit):
        self.now += 0.3
        return b""


class RetryTests(unittest.TestCase):
    def test_untrusted_caption_is_one_bounded_ascii_hex_argument(self):
        value = caption_value("gemini", "Café\nMRR1 1 tone\x00" + "🙂" * 200)
        provider, hextext = value.split(" ")
        decoded = bytes.fromhex(hextext)
        self.assertEqual(provider,"gemini")
        self.assertLessEqual(len(decoded),96)
        self.assertTrue(decoded.startswith(b"Cafe MRR1 1 tone"))
        self.assertTrue(all(32 <= byte <= 126 for byte in decoded))
        self.assertTrue(decoded.endswith(b"..."))
        with self.assertRaises(ValueError):caption_value("untrusted-provider","test")
    def test_lost_reply_retries_status_but_never_physical_actions(self):
        for operation in ("status", "tone", "mic"):
            with self.subTest(operation=operation):
                connection = LostReplyConnection()
                device = Device("synthetic-port")
                device.connection = connection
                with patch("device.time.monotonic", side_effect=lambda: connection.now):
                    with self.assertRaises(TimeoutError):
                        device.request(operation, timeout=2)
                if operation in ("tone", "mic"):
                    self.assertEqual(len(connection.writes), 1)
                else:
                    self.assertGreaterEqual(len(connection.writes), 2)
                    self.assertEqual(len(set(connection.writes)), 1)


if __name__ == "__main__":
    unittest.main()
