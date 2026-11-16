#!/usr/bin/env python3
"""Run the pinned SDK host suite with its source dependencies and Darwin tool flags."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FREEINK_PIN = "2c047df7792cedece1191503793f18f5d8f1c695"


def main():
    source = ROOT / "external/freeink-sdk"
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if revision != FREEINK_PIN:
        raise SystemExit("Use the unchanged FreeInk pin required by the SDK tests")
    env = os.environ.copy()
    env["IDF_PATH"] = str(ROOT / "external/esp-idf-v6.0.1")
    env["FREEINK_SOURCE_DIR"] = str(source)
    # Ninja detects source-selection changes by command hash; the default
    # Makefiles generator can retain the previous avatar in rapid rebuilds.
    env["CMAKE_GENERATOR"] = "Ninja"
    tools = ROOT / "external/esp-idf-tools/tools"
    env["PATH"] = os.pathsep.join([str(tools / "cmake/4.0.3/CMake.app/Contents/bin"),
                                  str(tools / "ninja/1.12.1"), env["PATH"]])
    with tempfile.TemporaryDirectory(prefix="mr-robot-host-cc-") as directory:
        if sys.platform == "darwin":
            # Host harnesses use GNU ld flags. Translate only their Darwin equivalents;
            # keep assertions, ASan/UBSan and all non-portability warnings intact.
            shim = '''#!/usr/bin/python3
import os, sys
compiler = '/usr/bin/clang++' if os.path.basename(sys.argv[0]) == 'cxx' else '/usr/bin/clang'
args = ['-Wno-error=deprecated-declarations', '-Wno-error=unused-command-line-argument']
for argument in sys.argv[1:]:
    if argument == '-no-pie':
        continue
    args.append('-Wl,-dead_strip' if argument == '-Wl,--gc-sections' else argument)
os.execv(compiler, [compiler, *args])
'''
            for name, variable in (("cc", "CC"), ("cxx", "CXX")):
                path = Path(directory) / name
                path.write_text(shim)
                path.chmod(0o700)
                env[variable] = str(path)
        return subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                                "-p", "test_*.py", "-v"],
                               cwd=ROOT / "external/muse-gadget-sdk/esp32", env=env)


if __name__ == "__main__":
    raise SystemExit(main())
