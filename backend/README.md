# Host AI Service

Control Room runs an authenticated loopback service with separate provider, settings, usage and USB modules. The owner selected **native Google Gemini first**. Mock, OpenRouter and explicitly configured compatible services remain available; Muse is a separate optional SDK path.

```sh
~/.platformio/penv/bin/python tools/manager.py --open
PYTHONPATH=backend ~/.platformio/penv/bin/python -m unittest discover -s backend/tests -v
```

Run from the project root. Setup, endpoints, private-file locations and limits: [API host setup](../docs/API-HOST-SETUP.md).

| Module | Responsibility |
| --- | --- |
| providers.py | Bounded native Gemini/compatible text adapters; mock; redacted errors |
| tls.py | Hostname/certificate verification with pinned certifi trust bundle |
| settings.py | Strict owner configuration; atomic mode 0600 files; public secret redaction |
| usage.py | Persistent UTC daily/minute attempt reservations without prompts/replies |
| gateway.py | Explicit provider routing; one inference at a time; no hidden fallback |
| server.py | Loopback HTTP, role authentication, Host/Origin checks and body/worker limits |
| device_image.py | PNG conversion to fixed-size RGB565 for the board |
| usb_bridge.py | Persistent serialized USB client, caption and image delivery, and hardware controls |

**45 synthetic tests pass**, plus live native Gemini generation, authenticated browser chat, USB controls and delivery to Face Lab 0.7.0. The owner confirms the generated greeting is readable on the round screen. Tests cover request shape, output filtering, TLS, secret redaction, authentication/scope, persistence/concurrency, cross-origin/body rejection, optional OpenRouter caps and preserving AI replies after USB delivery failure. Tests use no real key. Physical results are separate in PROJECT-STATUS.md.

Provider keys remain on the laptop. Gemini's Free-tier flag is owner attestation; the app cannot verify Google billing. Local request/token bounds are not a monetary cap on a paid Google project. OpenRouter verifies its own finite key cap; generic compatible-service billing remains owner-managed. No LAN listener or production HTTPS deployment exists.

The browser persists text and generated PNGs locally in IndexedDB. The host does not write a transcript or user audio to disk. Each text inference sends one message. For current provider and hardware results, see the [November 14 system audit](../docs/SYSTEM-AUDIT-2026-11-14.md).

# Gemini voice extension — 2026-10-31

`gemini_live.py` implements bounded single-turn WSS audio; `voice.py` coordinates explicit tap-to-talk mode, persistent attempts and exclusive USB ownership. Owner confirms a clear physical speech/reply round trip on Face Lab 0.8. API keys remain host-only. See [voice guide](../docs/GEMINI-VOICE.md) for operation, limits and checks. The existing text/provider architecture below remains available.
