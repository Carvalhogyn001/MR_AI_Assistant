#!/usr/bin/env python3
"""Exercise the real bounded command parser with sanitizers on the host."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory(prefix="mr-robot-control-tests-") as directory:
    executable = Path(directory) / "control_protocol_test"
    subprocess.run([
        os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
        "-I", str(ROOT / "firmware/assistant/include"),
        str(ROOT / "firmware/assistant/tests/control_protocol_test.cpp"),
        str(ROOT / "firmware/assistant/src/control_protocol.cpp"), "-o", str(executable),
    ], check=True)
    subprocess.run([str(executable)], check=True)
    voice = Path(directory) / "voice_protocol_test"
    subprocess.run([
        os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
        "-I", str(ROOT / "firmware/assistant/include"),
        str(ROOT / "firmware/assistant/tests/voice_protocol_test.cpp"),
        str(ROOT / "firmware/assistant/src/voice_protocol.cpp"), "-o", str(voice),
    ], check=True)
    subprocess.run([str(voice)], check=True)
    image = Path(directory) / "image_transfer_test"
    assistant = ROOT / "firmware/assistant"
    subprocess.run([
        os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
        "-I", str(assistant / "include"), "-I", str(assistant / "tests/render_stubs"),
        str(assistant / "tests/image_transfer_test.cpp"),
        *(str(assistant / "src" / source) for source in ("control_protocol.cpp", "voice_protocol.cpp", "image_transfer.cpp")),
        "-o", str(image),
    ], check=True)
    subprocess.run([str(image)], check=True)
print("PASS: command validation, bounds, rejection without state mutation and image retry safety (ASan/UBSan)")
