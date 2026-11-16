"""Synthetic checks for private provisioning and the non-C flash guard."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tools import muse
from tools.usb_console import preserve_modem_lines

TOKEN = "mgst_" + "A" * 43  # Synthetic format fixture, never a service credential.


class MuseTests(unittest.TestCase):
    def test_status_does_not_expose_network_or_account_fields(self):
        state = {"board": muse.BOARD, "device": {
            "wifi": {"state": "connected", "ssid": "synthetic-private-network", "ip": "192.0.2.1"},
            "link": {"paired": False}, "hatch": {"token": True, "vm": "synthetic-private-account"}}}
        status = muse.public_status(state)
        self.assertTrue(status["wifi_connected"])
        self.assertFalse(status["paired"])
        self.assertTrue(status["standalone_account_credential_configured"])
        self.assertNotIn("synthetic-private", str(status))
        self.assertNotIn("192.0.2.1", str(status))

    def test_pairing_is_distinct_from_standalone_token_and_labels_are_allowlisted(self):
        state = {"board": muse.BOARD, "device": {
            "link": {"paired": True, "state": "Online"},
            "hatch": {"token": False, "state": "Connected"}}}
        status = muse.public_status(state)
        self.assertTrue(status["paired"])
        self.assertFalse(status["standalone_account_credential_configured"])
        self.assertEqual((status["link_state"], status["voice_state"]), ("Online", "Connected"))
        for value in (TOKEN, [TOKEN], {"secret": TOKEN}, None):
            state["device"]["link"]["state"] = value
            state["device"]["hatch"]["state"] = value
            status = muse.public_status(state)
            self.assertEqual((status["link_state"], status["voice_state"]), ("Unknown", "Unknown"))
            self.assertNotIn(TOKEN, str(status))

    def test_status_parser_refuses_wrong_board_bad_json_and_oversized_lines(self):
        good = b"@status " + json.dumps({"board": muse.BOARD}).encode() + b"\n"
        self.assertIsNotNone(muse.parse_status_line(good))
        for line in (b"@status []\n", b"@status {\n", b'@status {"board":"other"}\n',
                     TOKEN.encode() + b"\n", b"@status " + b" " * 16385 + good[8:]):
            self.assertIsNone(muse.parse_status_line(line))

    def test_watch_is_bounded_redacts_logs_and_only_reads_status(self):
        initial = {"board": muse.BOARD, "device": {"link": {"paired": False, "state": "Ready to pair"}}}
        confirm = {"board": muse.BOARD, "device": {"link": {"paired": False, "state": "Confirm pairing"}}}
        connection = MagicMock()
        connection.read_until.side_effect = [
            TOKEN.encode() + b"\n", b'@status {"board":"wrong-board"}\n',
            b"@status " + json.dumps(confirm).encode() + b"\n",
            b"I (1000) link.app: talk button confirmed active pairing session\r\n",
        ] + [b""] * 100
        ticks = iter(i / 4 for i in range(100))
        output = io.StringIO()
        with patch.object(muse.time, "monotonic", side_effect=lambda: next(ticks)), redirect_stdout(output):
            self.assertEqual(muse.watch_pairing(connection, initial, 10), 0)
        lines = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([line["event"] for line in lines],
                         ["status", "status", "physical_pairing_button_confirmed", "watch_finished"])
        self.assertEqual(lines[1]["link_state"], "Confirm pairing")
        self.assertNotIn(TOKEN, output.getvalue())
        self.assertNotIn("wrong-board", output.getvalue())
        self.assertLessEqual(connection.write.call_count, 5)
        self.assertTrue(all(call.args == (b">status\n",) for call in connection.write.call_args_list))
        connection.reset_input_buffer.assert_not_called()

    def test_posix_hangup_bit_is_cleared_without_changing_other_flags(self):
        connection = MagicMock()
        connection.fileno.return_value = 12
        attributes = [1, 2, 0xFFFF, 4, 5, 6, []]
        fake = SimpleNamespace(HUPCL=0x100, TCSANOW=0,
                               tcgetattr=MagicMock(return_value=attributes), tcsetattr=MagicMock())
        with patch.dict("sys.modules", {"termios": fake}):
            self.assertTrue(preserve_modem_lines(connection))
        self.assertEqual(attributes, [1, 2, 0xFEFF, 4, 5, 6, []])
        fake.tcsetattr.assert_called_once_with(12, 0, attributes)

    def test_private_env_is_data_and_requires_one_valid_named_token(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / ".env"
            p.write_text("MUSE_GADGET_SDK_TOKEN=" + TOKEN + "\n")
            self.assertEqual(muse.load_sdk_token(p), TOKEN)
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            for value in ("", "MUSE_GADGET_SDK_TOKEN=$(touch unwanted)\n",
                          "MUSE_GADGET_SDK_TOKEN=invalid\n",
                          ("MUSE_GADGET_SDK_TOKEN=" + TOKEN + "\n") * 2):
                p.write_text(value)
                with self.assertRaises(ValueError) as error:
                    muse.load_sdk_token(p)
                self.assertNotIn(TOKEN, str(error.exception))
            self.assertFalse((Path(directory) / "unwanted").exists())

    def test_wrong_board_status_is_not_accepted(self):
        connection = MagicMock()
        connection.read_until.return_value = b'@status {"board":"wrong-board"}\n'
        with patch.object(muse.time, "monotonic", side_effect=[0, 0, 6]):
            with self.assertRaisesRegex(ValueError, "no token sent"):
                muse.read_status(connection)

    def test_provision_drops_token_echo_and_sends_once(self):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.read_until.side_effect = [TOKEN.encode() + b"\n", b"@sdk_token ok\n"]
        output = io.StringIO()
        with patch.object(muse, "load_sdk_token", return_value=TOKEN), \
             patch.object(muse, "pick_port", return_value="synthetic-port"), \
             patch.object(muse, "read_status", return_value={"board": muse.BOARD}), \
             patch("serial.Serial", return_value=connection), redirect_stdout(output):
            self.assertEqual(muse.serial_action("provision"), 0)
        self.assertNotIn(TOKEN, output.getvalue())
        connection.write.assert_called_once_with((">sdk_token=" + TOKEN + "\n").encode())

    def test_flash_guard_rejects_credentials_and_different_board(self):
        good = '\n'.join([
            'CONFIG_IDF_TARGET="esp32s3"', 'CONFIG_MUSE_BOARD_WAVESHARE_S3_175=y',
            'CONFIG_ESPTOOLPY_FLASHSIZE="16MB"', 'CONFIG_SPIRAM_MODE_OCT=y',
            'CONFIG_MUSE_REALTIME_VOICE=y', 'CONFIG_GADGET_SDK_TOKEN=""',
            'CONFIG_HOMEHUB_WIFI_SSID=""', 'CONFIG_HOMEHUB_WIFI_PASSWORD=""'])
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "sdkconfig"
            p.write_text(good)
            muse.validate_config(p)
            for extra in ('\nCONFIG_MUSE_BOARD_WAVESHARE_S3_175C=y',
                          '\nCONFIG_SECURE_BOOT_ENABLED=y', '\nCONFIG_NVS_ENCRYPTION=y',
                          '\nCONFIG_HOMEHUB_TUNNEL=y',
                          '\nCONFIG_GADGET_SDK_TOKEN="' + TOKEN + '"'):
                p.write_text(good + extra)
                with self.assertRaises(ValueError):
                    muse.validate_config(p)


if __name__ == "__main__":
    unittest.main()
