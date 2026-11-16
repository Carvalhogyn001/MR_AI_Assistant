#!/usr/bin/env python3
"""Install the pinned, public wake model into the ignored project directory."""
import hashlib
from pathlib import Path
import shutil
import sys
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from mr_robot_backend.wake_word import KEYWORD_LINE, MODEL, PARTS

RELEASE = "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/{RELEASE}.tar.bz2"
SHA256 = "68447f4fbc67e70eee3a93961f36e81e98f47aef73ce7e7ca00885c6cd3616a6"


def main():
    MODEL.mkdir(parents=True, exist_ok=True)
    archive = MODEL / "model.tar.bz2"
    if not archive.is_file():
        temporary = MODEL / "download.partial"
        with urlopen(URL, timeout=30) as source, temporary.open("wb") as target:
            while data := source.read(65536):
                if target.tell() + len(data) > 40_000_000:
                    raise SystemExit("Wake model archive exceeded its size limit.")
                target.write(data)
        with temporary.open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != SHA256:
                raise SystemExit("Wake model download checksum failed.")
        temporary.replace(archive)
    with archive.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != SHA256:
            raise SystemExit("Wake model archive checksum failed.")
    with tarfile.open(archive) as package:
        for name in PARTS.values():
            member = package.getmember(f"{RELEASE}/{name}")
            if not member.isfile() or member.size > 20_000_000:
                raise SystemExit("Wake model archive contains an invalid component.")
            with package.extractfile(member) as source, (MODEL / name).open("wb") as target:
                shutil.copyfileobj(source, target)
    (MODEL / "keywords.txt").write_text(KEYWORD_LINE, encoding="utf-8")
    print("Installed the verified local Hey Mr. Robot model.")


if __name__ == "__main__":
    main()
