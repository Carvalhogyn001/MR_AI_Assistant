"""Owner-selected host configuration. Secrets never appear in public settings."""
from dataclasses import asdict, dataclass, field
import json
import math
import os
from pathlib import Path
import secrets
import tempfile

from .providers import ProviderConfig, ProviderError


def private_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_token(path):
    path = Path(path)
    if not path.exists():
        private_write(path, secrets.token_urlsafe(32))
    os.chmod(path, 0o600)
    token = path.read_text().strip()
    if len(token) != 43 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for c in token):
        raise ValueError("invalid_local_token_file")
    return token


@dataclass(frozen=True)
class Settings:
    provider: str = "mock"
    model: str = "fixture"
    base_url: str = ""
    api_key: str = field(default="", repr=False)
    max_output_tokens: int = 256
    daily_requests: int = 20
    requests_per_minute: int = 4
    max_key_budget_usd: float = 1.0
    remote_budget_confirmed: bool = False
    gemini_free_tier_confirmed: bool = False

    def __post_init__(self):
        if self.provider not in ("mock", "gemini", "openrouter", "compatible", "ollama", "muse"):
            raise ProviderError("unsupported_provider")
        for value, low, high in ((self.max_output_tokens, 16, 512), (self.daily_requests, 1, 500),
                                 (self.requests_per_minute, 1, 10)):
            if type(value) is not int or not low <= value <= high:
                raise ProviderError("invalid_limit")
        if (isinstance(self.max_key_budget_usd, bool) or not isinstance(self.max_key_budget_usd, (int, float)) or
                not math.isfinite(self.max_key_budget_usd) or not 0.01 <= self.max_key_budget_usd <= 100):
            raise ProviderError("invalid_budget")
        if type(self.remote_budget_confirmed) is not bool or type(self.gemini_free_tier_confirmed) is not bool:
            raise ProviderError("invalid_budget_confirmation")
        if self.provider not in ("mock", "muse"):
            self.provider_config()

    def provider_config(self):
        return ProviderConfig(self.provider, self.base_url, self.model, self.api_key, self.max_output_tokens,
                              timeout_seconds={"gemini": 30, "ollama": 50}.get(self.provider, 20))

    def public(self):
        values = asdict(self)
        values.pop("api_key")
        values["key_configured"] = bool(self.api_key)
        return values


class SettingsStore:
    def __init__(self, path):
        self.path = Path(path)
        self.gemini_profile = self.path.with_name("gemini-profile.json")
        self.value = Settings(**json.loads(self.path.read_text())) if self.path.exists() else Settings()
        if self.path.exists():
            os.chmod(self.path, 0o600)

    def gemini_saved(self):
        if self.gemini_profile.exists():
            profile = Settings(**json.loads(self.gemini_profile.read_text()))
            if profile.provider == "gemini":
                return profile
        return None

    def update(self, incoming):
        if not isinstance(incoming, dict) or set(incoming) - set(Settings.__dataclass_fields__):
            raise ProviderError("invalid_settings")
        values = asdict(self.value)
        values.update(incoming)
        same_destination = (values["provider"], values["base_url"]) == (self.value.provider, self.value.base_url)
        # A blank form keeps the existing key only for the identical destination.
        if incoming.get("api_key") == "" and same_destination:
            values["api_key"] = self.value.api_key
        elif not same_destination and "api_key" not in incoming:
            values["api_key"] = ""
        if values["provider"] == "openrouter":
            values["base_url"] = "https://openrouter.ai/api/v1"
        if values["provider"] == "gemini":
            values["base_url"] = "https://generativelanguage.googleapis.com/v1beta"
            if incoming.get("api_key") and incoming["api_key"] != self.value.api_key:
                values["gemini_free_tier_confirmed"] = incoming.get("gemini_free_tier_confirmed", False)
        if values["provider"] == "gemini" and not incoming.get("api_key"):
            profile = self.gemini_saved()
            if profile:
                if not values["api_key"]:
                    values["api_key"] = profile.api_key
                if values["api_key"] == profile.api_key and "gemini_free_tier_confirmed" not in incoming:
                    values["gemini_free_tier_confirmed"] |= profile.gemini_free_tier_confirmed
        if values["provider"] == "ollama":
            values.update(base_url="http://127.0.0.1:11434", api_key="", gemini_free_tier_confirmed=False)
        if values["provider"] == "mock":
            values.update(model="fixture", base_url="", api_key="", remote_budget_confirmed=False)
        if values["provider"] == "muse":
            values.update(model="Muse", base_url="", api_key="", remote_budget_confirmed=False,
                          gemini_free_tier_confirmed=False)
        value = Settings(**values)
        if value.provider == "gemini":
            private_write(self.gemini_profile, json.dumps(asdict(value), indent=2) + "\n")
        private_write(self.path, json.dumps(asdict(value), indent=2) + "\n")
        self.value = value
        return value.public()
