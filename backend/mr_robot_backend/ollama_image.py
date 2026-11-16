"""Run the installed text-to-image model on its compatible local runtime."""
import base64
import binascii
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from .providers import NoRedirects, ProviderError, validate_prompt

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "private/ollama-image"
MODEL_MANIFEST = Path("manifests/registry.ollama.ai/x/z-image-turbo/latest")
ENDPOINT = "http://127.0.0.1:11435"
VERSION = "0.32.5"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class OllamaImage:
    def __init__(self):
        self._opener = build_opener(ProxyHandler({}), NoRedirects())
        self._process = None

    def _ready(self):
        try:
            with self._opener.open(ENDPOINT + "/api/version", timeout=1) as reply:
                return json.loads(reply.read(1024)).get("version") == VERSION
        except (OSError, ValueError, AttributeError):
            return False

    def _ensure_runtime(self):
        if self._ready():
            return
        binary = RUNTIME / "ollama"
        if not binary.is_file():
            raise ProviderError("image_runtime_missing")
        if self._process is None or self._process.poll() is not None:
            source = Path.home() / ".ollama/models"
            models = RUNTIME / "models"
            manifest = models / MODEL_MANIFEST
            env = {**os.environ, "OLLAMA_HOST": "127.0.0.1:11435", "OLLAMA_NOPRUNE": "true",
                   "OLLAMA_NO_CLOUD": "true", "OLLAMA_KEEP_ALIVE": "0",
                   "OLLAMA_MODELS": str(models)}
            try:
                manifest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                shutil.copyfile(source / MODEL_MANIFEST, manifest)
                blobs = models / "blobs"
                if not blobs.is_symlink():
                    blobs.symlink_to(source / "blobs", target_is_directory=True)
                self._process = subprocess.Popen([str(binary), "serve"], env=env,
                                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                raise ProviderError("image_runtime_unavailable") from None
        deadline = time.monotonic() + 8
        while self._process.poll() is None and time.monotonic() < deadline:
            if self._ready():
                return
            time.sleep(.25)
        raise ProviderError("image_runtime_unavailable")

    def generate(self, prompt):
        validate_prompt(prompt)
        self._ensure_runtime()
        data = json.dumps({"model": "x/z-image-turbo:latest", "prompt": prompt, "width": 512,
                           "height": 512, "steps": 8, "stream": False, "keep_alive": 0}).encode()
        request = Request(ENDPOINT + "/api/generate", data=data, headers={"Content-Type": "application/json"})
        try:
            with self._opener.open(request, timeout=180) as response:
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise ValueError()
            image = json.loads(raw)["image"]
            if not isinstance(image, str) or not base64.b64decode(image, validate=True).startswith(PNG_SIGNATURE):
                raise ValueError()
            return image
        except HTTPError as error:
            error.close()
            raise ProviderError("image_generation_failed") from None
        except TimeoutError:
            raise ProviderError("image_generation_timeout") from None
        except (URLError, OSError):
            raise ProviderError("image_runtime_unavailable") from None
        except (ValueError, KeyError, TypeError, binascii.Error):
            raise ProviderError("image_generation_failed") from None

    def close(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
