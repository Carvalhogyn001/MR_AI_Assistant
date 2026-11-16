#!/usr/bin/env python3
"""USB control client. Future desktop UI should reuse Device, not spawn a shell."""
import argparse
import json
import time
import unicodedata
import zlib

try:
    from .usb_console import preserve_modem_lines
except ImportError:
    from usb_console import preserve_modem_lines

try:
    import serial
    from serial.tools import list_ports
except ImportError as error:
    raise SystemExit("pyserial is required; use ~/.platformio/penv/bin/python tools/device.py") from error

VALUES = {
    "face": ("classic", "pixel", "orbit"),
    "expression": ("neutral", "happy", "curious", "sleepy", "surprised", "wink", "excited", "concerned", "squint", "blush", "dizzy"),
    "screen": ("face", "settings", "status", "gallery"),
}

def caption_value(provider, text, limit=96):
    if provider not in ("mock", "gemini", "openrouter", "compatible", "ollama", "ollama-prompt") or not isinstance(text, str):
        raise ValueError("Unsupported caption")
    normalized = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    ascii_text = normalized.encode("ascii", "replace").decode("ascii")
    plain = " ".join("".join(c if 32 <= ord(c) <= 126 else " " for c in ascii_text).split())
    if not plain:
        raise ValueError("Empty caption")
    if len(plain) > limit:
        plain = plain[:limit - 3] + "..."
    return provider + " " + plain.encode("ascii").hex()


def choose_port(explicit=None):
    if explicit:
        return explicit
    matches = [p.device for p in list_ports.comports() if (p.vid, p.pid) == (0x303A, 0x1001)]
    if len(matches) != 1:
        raise ValueError("Connect one Waveshare native USB device, or select it with --port.")
    return matches[0]


class Device:
    """One outstanding request at a time; no credentials, networking or file writes."""

    def __init__(self, port=None):
        self.port = choose_port(port)
        self.sequence = 0
        self.connection = None

    def __enter__(self):
        connection = serial.Serial(exclusive=True)
        connection.port = self.port
        connection.baudrate = 115200
        connection.timeout = 0.15
        connection.write_timeout = 1
        connection.dtr = True
        connection.rts = True
        connection.open()
        preserve_modem_lines(connection)
        self.connection = connection
        try:
            status = self.request("status")
            if status.get("protocol") != 1 or not status.get("firmware", "").startswith("face-lab-"):
                raise ValueError("The connected firmware does not identify as MR. Robot Face Lab.")
        except BaseException:
            connection.close()
            self.connection = None
            raise
        return self

    def __exit__(self, *_):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def send_image(self, pixels):
        if not isinstance(pixels, bytes) or len(pixels) != 300 * 300 * 2:
            raise ValueError("Invalid RGB565 frame")
        self._request("image-begin", zlib.crc32(pixels), timeout=3, retry_delay=.25)
        for offset in range(0, len(pixels), 240):
            self._request("image-chunk", f"{offset} {pixels[offset:offset + 240].hex()}", timeout=3, retry_delay=.25)
        status = self._request("image-end", timeout=3, retry_delay=.25)
        if status.get("image_available") is not True:
            raise ValueError("Board did not acknowledge the image")

    def show_activity(self, activity):
        if activity not in ("idle", "thinking", "drawing", "done", "error"):
            raise ValueError("Invalid host activity")
        return self._request("activity", activity, timeout=2)

    def request(self, operation, value=None, timeout=6):
        if operation in ("status", "card", "tone", "mic", "mic-arm", "mic-cancel", "caption-clear"):
            if value is not None:
                raise ValueError(f"{operation} takes no value")
        elif operation == "caption":
            if not isinstance(value, tuple) or len(value) != 2:
                raise ValueError("Caption requires provider and text")
            value = caption_value(*value, limit=480 if value[0] in ("ollama", "ollama-prompt") else 96)
        elif operation in VALUES:
            if value not in VALUES[operation]:
                raise ValueError(f"Unsupported {operation}")
        elif operation == "brightness":
            if isinstance(value, bool) or not isinstance(value, int) or not 16 <= value <= 160:
                raise ValueError("Brightness must be an integer from 16 to 160")
        else:
            raise ValueError("Unsupported operation")
        return self._request(operation, value, timeout, retry=operation not in ("tone", "mic"))

    def _request(self, operation, value=None, timeout=6, retry=True, retry_delay=.8):
        if self.connection is None:
            raise RuntimeError("Use Device inside a with block")
        self.sequence = self.sequence % 65535 + 1
        line = f"MRR1 {self.sequence} {operation}" + (f" {value}" if value is not None else "") + "\n"
        data = line.encode("ascii")
        deadline = time.monotonic() + timeout
        resend = 0.0
        while time.monotonic() < deadline:
            if time.monotonic() >= resend:
                self.connection.write(data)
                self.connection.flush()
                # A tone is a physical action; don't repeat it if a reply is lost.
                resend = time.monotonic() + retry_delay if retry else float("inf")
            raw = self.connection.readline(4096)
            if not raw.startswith(b"MRR1 ") or not raw.endswith(b"\n"):
                continue
            try:
                response = json.loads(raw[5:].decode("ascii"))
            except (ValueError, UnicodeError):
                continue
            if not isinstance(response, dict) or response.get("id") != self.sequence:
                continue
            if response.get("ok") is not True:
                raise RuntimeError(f"Device rejected command: {response.get('error', 'unknown_error')}")
            return response
        raise TimeoutError("No MR. Robot reply. Check port, firmware and other serial monitors.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-p", "--port", help="Explicit USB serial path; otherwise requires exactly one matching USB device")
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("status")
    commands.add_parser("card", help="Read raw SD capacity and boot-sector signature; no mount or writes")
    commands.add_parser("tone", help="One quiet 440 Hz/400 ms speaker test; no automatic retry")
    commands.add_parser("mic", help="One four-second microphone level test; no raw audio saved or automatic retry")
    commands.add_parser("mic-arm", help="Wait up to 60 seconds for a physical tap to start a four-second level test")
    commands.add_parser("mic-cancel", help="Cancel a pending armed test; an active diagnostic ends automatically")
    commands.add_parser("caption-clear", help="Clear the volatile host reply preview")
    command = commands.add_parser("caption", help="Show a bounded ASCII reply preview")
    command.add_argument("provider", choices=("mock", "gemini", "openrouter", "compatible"))
    command.add_argument("text")
    for operation, values in VALUES.items():
        command = commands.add_parser(operation)
        command.add_argument("value", choices=values)
    command = commands.add_parser("brightness")
    command.add_argument("value", type=int, choices=range(16, 161), metavar="16..160")
    arguments = parser.parse_args()
    try:
        with Device(arguments.port) as device:
            value = (arguments.provider, arguments.text) if arguments.operation == "caption" else getattr(arguments, "value", None)
            result = device.request(arguments.operation, value)
    except (OSError, ValueError, RuntimeError, TimeoutError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
