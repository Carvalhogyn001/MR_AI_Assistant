"""Select the resident ESP32 app over the native USB console."""
import json
import time

from tools.muse import parse_status_line, public_status
from tools.usb_console import preserve_modem_lines

from .providers import ProviderError


def open_console(port):
    import serial

    connection = serial.Serial(port=None, baudrate=115200, timeout=.2, write_timeout=2, exclusive=True)
    connection.dtr = connection.rts = True
    connection.port = port
    connection.open()
    preserve_modem_lines(connection)
    return connection


def identify(connection, timeout=2):
    connection.write(b"\n>status\n")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = connection.read_until(b"\n", 16385)
        at = line.find(b"@status ")
        state = parse_status_line(line[at:]) if at >= 0 else None
        if state:
            return "muse", public_status(state)
    connection.write(b">host-face-status\n")
    deadline = time.monotonic() + .7
    while time.monotonic() < deadline:
        line = connection.read_until(b"\n", 16385)
        muse = parse_status_line(line)
        if muse:
            return "muse", public_status(muse)
        if line.startswith(b"MRR1 "):
            try:
                face = json.loads(line[5:])
                if (face.get("id") == 65535 and face.get("protocol") == 1
                        and face.get("firmware", "").startswith("face-lab-")):
                    return "face-lab", face
            except (ValueError, AttributeError):
                pass
    return "unknown", {}


def inspect(ports):
    if len(ports) != 1:
        return {"firmware": "disconnected"}
    try:
        with open_console(ports[0]) as connection:
            firmware, state = identify(connection)
            result = {"firmware": firmware}
            if firmware == "muse":
                result.update(paired=state["paired"], online=state["link_state"] == "Online")
            return result
    except OSError:
        return {"firmware": "unknown"}


def switch(port, target):
    if target not in ("face-lab", "muse"):
        raise ValueError("unknown firmware target")
    try:
        with open_console(port) as connection:
            current, _ = identify(connection)
            if current == "unknown":
                current, _ = identify(connection)
            if current == target:
                return
            if current == "unknown":
                raise ProviderError("device_firmware_unknown")
            connection.write(f">boot={target}\n".encode("ascii"))
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                line = connection.read_until(b"\n", 16385).strip()
                if line == b"@boot error":
                    raise ProviderError("device_switch_rejected")
                if line == b"@boot ok":
                    break
    except OSError:
        pass  # The native port can disappear between the acknowledgement and reboot.

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        time.sleep(.5)
        try:
            with open_console(port) as connection:
                if identify(connection, timeout=1)[0] == target:
                    return
        except OSError:
            continue
    raise ProviderError("device_switch_unverified")


def muse_chat(port, text):
    from tools.muse import read_status

    def receive(connection, deadline):
        while time.monotonic() < deadline:
            line = connection.read_until(b"\n", 16385)
            if line.startswith(b"@chat "):
                try:
                    frame = json.loads(line[6:])
                    if isinstance(frame, dict):
                        if frame.get("type") == "error":
                            raise ProviderError("muse_request_failed")
                        return frame
                except (ValueError, UnicodeError):
                    continue
        raise ProviderError("muse_reply_timeout")

    data = text.encode("utf-8")
    try:
        with open_console(port) as connection:
            state = read_status(connection)
            state = public_status(state)
            if not state["paired"]:
                raise ProviderError("muse_board_unavailable")
            if state["link_state"] != "Online":
                raise ProviderError("muse_link_offline")
            connection.reset_input_buffer()
            try:
                for offset in range(0, len(data), 400):
                    end = min(offset + 400, len(data))
                    chunk = data[offset:end].replace(b"\\", b"\\\\").replace(b"\n", b"\\n").replace(b"\r", b"\\r").replace(b"\t", b"\\t")
                    command = b">chat+=" if end < len(data) else b">chat="
                    connection.write(command + chunk + b"\n")
                    frame = receive(connection, time.monotonic() + 4)
                    if frame.get("type") != "ack" or frame.get("bytes") != end:
                        raise ProviderError("muse_request_failed")
                partial, final = {}, {}
                deadline = time.monotonic() + 75
                while True:
                    frame = receive(connection, deadline)
                    kind = frame.get("type")
                    if kind == "done":
                        if not frame.get("complete"):
                            raise ProviderError("muse_request_failed")
                        reply = "\n\n".join("".join(final.get(index) or partial[index])
                                            for index in sorted(partial.keys() | final.keys()))
                        if not reply.strip():
                            raise ProviderError("muse_request_failed")
                        return reply
                    if kind in ("text", "final") and type(frame.get("msg")) is int and isinstance(frame.get("text"), str):
                        (final if kind == "final" else partial).setdefault(frame["msg"], []).append(frame["text"])
            except ProviderError:
                connection.write(b">chat.cancel\n")
                raise
    except (OSError, ValueError):
        raise ProviderError("muse_board_unavailable") from None
