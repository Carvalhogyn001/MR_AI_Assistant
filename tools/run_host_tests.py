#!/usr/bin/env python3
"""Compile and run the existing firmware helper tests without ESP32 hardware."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    tests = sorted((ROOT / "firmware/tests").glob("*_test.cpp"))
    if not tests:
        raise SystemExit("No existing helper tests found")
    with tempfile.TemporaryDirectory(prefix="mr-robot-tests-") as directory:
        for test in tests:
            executable = Path(directory) / test.stem
            subprocess.run(
                [os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra", "-Werror",
                 "-I", str(ROOT / "firmware/include"), str(test), "-o", str(executable)],
                check=True,
            )
            subprocess.run([str(executable)], check=True)
            print(f"PASS {test.name}", flush=True)
    print(f"{len(tests)} existing helper tests passed")


if __name__ == "__main__":
    main()
