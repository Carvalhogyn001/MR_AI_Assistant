#!/usr/bin/env python3
"""Build, provision and inspect the pinned non-C Muse evaluation privately."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

try:
    from .usb_console import preserve_modem_lines
except ImportError:
    from usb_console import preserve_modem_lines

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "external/muse-gadget-sdk"
IDF = ROOT / "external/esp-idf-v6.0.1"
BUILD = SDK / "esp32/build-mr-robot-s3n"
PATCHES = ("io16-talk.patch", "dual-boot.patch")
BOARD = "Waveshare ESP32-S3-Touch-AMOLED-1.75"
LINK_STATES = frozenset(("Starting", "Ready to pair", "App connected", "Confirm pairing",
                         "Connecting", "Online", "Offline", "Error"))
VOICE_STATES = frozenset(("Not set up", "Offline", "Saved", "Connecting", "Connected", "Can't connect"))
PINS = {SDK: "1b894f551e64416e2844452ec6056ec56d6a10f1",
        IDF: "8c19b156084a0753687347cca1f5355782893533"}


def load_sdk_token(path):
    """Read data, never source shell code or include secret values in errors."""
    path = Path(path)
    path.chmod(0o600)
    found = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        name, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and name.strip() == "MUSE_GADGET_SDK_TOKEN":
            found.append(value.strip().strip("\"'"))
    if len(found) != 1 or not re.fullmatch(r"mgst_[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]", found[0]):
        raise ValueError("Save exactly one valid MUSE_GADGET_SDK_TOKEN assignment in .env")
    return found[0]


def check_sources():
    for source, revision in PINS.items():
        result = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True)
        if result.stdout.strip() != revision:
            raise ValueError("Source revision differs from the reviewed pin")


def apply_local_patches():
    command = ["git", "-C", str(SDK), "apply"]
    for name in PATCHES:
        patch = str(ROOT / "firmware/muse-evaluation" / name)
        if subprocess.run([*command, "--reverse", "--check", patch], capture_output=True).returncode:
            subprocess.run([*command, patch], check=True)


def validate_config(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
        elif line.startswith("# CONFIG_") and line.endswith(" is not set"):
            values[line[2:-11]] = "n"
    expected = {"CONFIG_IDF_TARGET": '"esp32s3"',
                "CONFIG_MUSE_BOARD_WAVESHARE_S3_175": "y",
                "CONFIG_ESPTOOLPY_FLASHSIZE": '"16MB"',
                "CONFIG_SPIRAM_MODE_OCT": "y", "CONFIG_MUSE_REALTIME_VOICE": "y",
                "CONFIG_GADGET_SDK_TOKEN": '""', "CONFIG_HOMEHUB_WIFI_SSID": '""',
                "CONFIG_HOMEHUB_WIFI_PASSWORD": '""'}
    if any(values.get(k) != v for k, v in expected.items()):
        raise ValueError("Build profile/credential validation failed")
    forbidden = ("CONFIG_MUSE_BOARD_WAVESHARE_S3_175C", "CONFIG_SECURE_BOOT",
                 "CONFIG_SECURE_BOOT_ENABLED", "CONFIG_SECURE_FLASH_ENC_ENABLED",
                 "CONFIG_HOMEHUB_NVS_ENCRYPTION", "CONFIG_NVS_ENCRYPTION",
                 "CONFIG_HOMEHUB_PAIRING_EFUSE_AUTH", "CONFIG_HOMEHUB_OTA_ENABLED",
                 "CONFIG_HOMEHUB_TUNNEL", "CONFIG_HOMEHUB_BLE_COMMANDS")
    if any(values.get(k) == "y" for k in forbidden):
        raise ValueError("Unexpected board, security-fuse, update or tunnel setting")


def idf_action(action, port=None):
    check_sources()
    apply_local_patches()
    if action == "flash":
        validate_config(BUILD / "sdkconfig")
        port = pick_port(port)
    defaults = ";".join(str(SDK / "esp32" / p) for p in
                        ("sdkconfig.defaults", "devices/sdkconfig.muse",
                         "devices/sdkconfig.muse-waveshare-s3-175"))
    defaults += ";" + str(ROOT / "firmware/muse-evaluation/sdkconfig.mr-robot")
    args = ["-B", str(BUILD), "-DIDF_TARGET=esp32s3", "-DSDKCONFIG=" + str(BUILD / "sdkconfig"),
            "-DSDKCONFIG_DEFAULTS=" + defaults]
    if port:
        args += ["-p", port]
    env = os.environ.copy()
    env["IDF_TOOLS_PATH"] = str(ROOT / "external/esp-idf-tools")
    # The command uses positional arguments; no credentials enter the shell or argv.
    result = subprocess.call(["bash", "-c", '. "$1" >/dev/null || exit; shift; exec idf.py "$@"',
                              "mr-robot-muse", str(IDF / "export.sh"), *args, action],
                             cwd=SDK / "esp32", env=env)
    if result:
        return result
    validate_config(BUILD / "sdkconfig")
    print("PASS: reviewed non-C profile, realtime voice and empty compiled credentials")
    return 0


def pick_port(requested=None):
    from serial.tools import list_ports
    ports = [p.device for p in list_ports.comports() if (p.vid, p.pid) == (0x303A, 0x1001)]
    if requested in ports:
        return requested
    if requested is None and len(ports) == 1:
        return ports[0]
    raise ValueError("Connect one Waveshare USB board or pass its --port")


def parse_status_line(line):
    """Accept only bounded JSON for our exact board; never return other UART text."""
    if len(line) > 16384 or not line.startswith(b"@status "):
        return None
    try:
        state = json.loads(line[8:])
    except (ValueError, UnicodeError):
        return None
    if isinstance(state, dict) and state.get("board") == BOARD:
        return state
    return None


def read_status(connection):
    connection.reset_input_buffer()
    connection.write(b">status\n")
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        state = parse_status_line(connection.read_until(b"\n", 16385))
        if state is not None:
            return state
    raise ValueError("Expected Muse non-C board status was not received; no token sent")


def public_status(state):
    device = state.get("device", {})
    if not isinstance(device, dict):
        device = {}
    wifi, link, voice = (device.get(k, {}) for k in ("wifi", "link", "hatch"))
    wifi, link, voice = (v if isinstance(v, dict) else {} for v in (wifi, link, voice))
    def known_label(value, allowed):
        return value if isinstance(value, str) and value in allowed else "Unknown"

    return {"board": BOARD, "muse_status_received": True,
            "wifi_connected": wifi.get("state") == "connected",
            "paired": link.get("paired") is True,
            # This is the standalone Settings token, not the app Link credential.
            "standalone_account_credential_configured": voice.get("token") is True,
            "link_state": known_label(link.get("state"), LINK_STATES),
            "voice_state": known_label(voice.get("state"), VOICE_STATES)}


def watch_pairing(connection, initial_state, seconds):
    """Poll metadata on one connection. No reset, token write or simulated button."""
    started = time.monotonic()
    deadline = started + seconds
    next_poll = started
    previous = public_status(initial_state)
    print(json.dumps({"event": "status", **previous}), flush=True)
    while time.monotonic() < deadline:
        if time.monotonic() >= next_poll:
            connection.write(b">status\n")
            next_poll = time.monotonic() + 2
        line = connection.read_until(b"\n", 16385)
        state = parse_status_line(line)
        if state is not None:
            current = public_status(state)
            if current != previous:
                print(json.dumps({"event": "status", **current}), flush=True)
                previous = current
        elif re.search(rb"\blink\.app: talk button confirmed active pairing session\r?\n?$", line):
            print(json.dumps({"event": "physical_pairing_button_confirmed"}), flush=True)
    print(json.dumps({"event": "watch_finished", "seconds": seconds}), flush=True)
    return 0


def serial_action(action, port=None, seconds=120):
    import serial
    token = load_sdk_token(ROOT / ".env") if action == "provision" else None
    connection = serial.Serial(port=None, baudrate=115200, timeout=0.2, write_timeout=2, exclusive=True)
    # Match the SDK console's default asserted lines. Deasserting DTR while
    # RTS is still asserted during open resets native USB Serial/JTAG devices.
    connection.dtr = True
    connection.rts = True
    connection.port = pick_port(port)
    with connection:
        preserve_modem_lines(connection)
        state = read_status(connection)
        if action == "status":
            # Never print raw status, which contains SSID, IP and account/VM fields.
            print(json.dumps(public_status(state)))
            return 0
        if action == "watch":
            return watch_pairing(connection, state, seconds)
        connection.write((">sdk_token=" + token + "\n").encode("ascii"))
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            line = connection.read_until(b"\n", 1024).strip()
            # Drop all logs/echoes. Never print raw serial while provisioning.
            if line == b"@sdk_token ok":
                print("SDK token stored; board restarting. No token value was logged.")
                return 0
            if line.startswith(b"@sdk_token error "):
                raise ValueError("Device rejected token provisioning")
    raise ValueError("Provisioning acknowledgement missing; no automatic retry")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "flash", "status", "watch", "provision"))
    parser.add_argument("--port")
    parser.add_argument("--seconds", type=int, default=120, help="watch duration, 10–600 seconds")
    args = parser.parse_args()
    if not 10 <= args.seconds <= 600:
        parser.error("--seconds must be between 10 and 600")
    os.umask(0o077)
    try:
        if args.action in ("build", "flash"):
            return idf_action(args.action, args.port)
        return serial_action(args.action, args.port, args.seconds)
    except KeyboardInterrupt:
        print("Monitor stopped; device setup was preserved.")
        return 130
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("Muse step failed: check local token format, source pins, build profile and USB connection. No secret values were printed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
