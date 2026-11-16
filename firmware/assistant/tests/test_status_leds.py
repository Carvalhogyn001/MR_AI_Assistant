#!/usr/bin/env python3
"""Host-only LED policy, default-off GPIO isolation and cleanup checks."""
from pathlib import Path
import os
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="mr-robot-status-leds-") as directory:
    for enabled in (0, 1):
        executable = Path(directory) / f"status_leds_{enabled}"
        subprocess.run([
            os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
            *(["-DMR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS=1"] if enabled else []),
            "-I", str(PROJECT / "tests/led_stubs"), "-I", str(PROJECT / "include"),
            str(PROJECT / "src/status_leds.cpp"), str(PROJECT / "tests/status_leds_test.cpp"),
            "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)
print("LED checks are host simulations; no physical GPIO or LED was accessed.")
