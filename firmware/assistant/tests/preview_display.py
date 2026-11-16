#!/usr/bin/env python3
"""Build the actual display renderer on the host and capture an SVG contact sheet.

Uses the already installed pinned GFX font, without downloading dependencies.
The host recorder approximates rounded primitive rasterization; it does not
verify panel behavior, SPI/audio timing, touch, colors or brightness on hardware.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
GFX = PROJECT / ".pio/libdeps/mr_robot_waveshare_175/GFX Library for Arduino/src"
if not (GFX / "font/glcdfont.h").is_file():
    raise SystemExit("Build firmware/assistant with PlatformIO first to install the pinned GFX font")
output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "private/previews/device-interface.svg"
output.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="mr-robot-display-") as directory:
    executable = Path(directory) / "preview"
    subprocess.run([
        os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
        "-I", str(PROJECT / "tests/render_stubs"), "-I", str(PROJECT / "include"), "-I", str(GFX),
        str(PROJECT / "src/face_renderer.cpp"), str(PROJECT / "tests/render_preview.cpp"), "-o", str(executable),
    ], check=True)
    subprocess.run([str(executable), str(output)], check=True)
print(output)
