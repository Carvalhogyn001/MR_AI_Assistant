# Laptop API Route

Updated 2026-11-06. Gemini is the current laptop route for text and voice; Muse evaluation is deferred. The Mac must stay running for this route. Gemini inference is remote; the ESP32 supplies the screen, microphone, speaker and hardware controls. No Muse account or phone enrollment is needed for this route.

## Run Control Room

From the project root, using the existing PlatformIO Python environment:

```sh
~/.platformio/penv/bin/python tools/manager.py --open
```

Default address: `http://127.0.0.1:18765/`. The launcher binds only to loopback. Its browser unlock credential is consumed from the URL fragment and removed; it is not a provider API key. Reloading an unlocked page loses its in-memory credential; run the launcher with `--open` to unlock again. If it is already running, a nonce/HMAC challenge first verifies the existing listener holds our local manager key, then the launcher reopens that service without starting a second server or printing a credential. This is a local development server; LAN/TLS deployment is a separate task.

For a separate environment, create `.venv-host` and install `backend/requirements.txt`. Dependencies are pinned certifi (the verified CA bundle) and pyserial (USB). The existing portable Python had no default CA file; explicit certifi fixes certificate validation without disabling it.

## Gemini setup

1. Create a project/API key in [Google AI Studio](https://aistudio.google.com/apikey). For this first free-only route, use a project marked **Free**, without paid billing.
2. In Control Room select Google Gemini, currently `gemini-3.8-flash` (also suggested: 3.6 Flash and 3.5/3.1 Flash-Lite). Paste the key only into the local password field, check the Free-tier box, and Save connection. A blank key preserves the existing key only for the same destination.
3. Send a short test message. Saving settings does not send a prompt; unsaved changes block sending. No automatic retry or model/provider fallback occurs.
4. Connect the Waveshare by USB and click Connect USB. Existing face/expression/brightness controls use the reusable device client. Caption-capable firmware can show a short preview of successful AI replies.

Google currently lists free text input/output for this model, subject to project quotas. The app does not inspect or change Google billing: the Free-tier check is the owner's attestation, not independent billing verification. Local attempt/token ceilings do not turn a paid project into a free one. Google states that free-tier data may be used to improve its products. Sources: [pricing](https://ai.google.dev/gemini-api/docs/pricing), [keys](https://ai.google.dev/gemini-api/docs/api-key), [billing](https://ai.google.dev/gemini-api/docs/billing).

The native adapter uses `generateContent`, `x-goog-api-key`, bounded text input/output, and model-specific thinking settings: low for3.8/3.6 Flash, minimal for3.5/3.1 Flash-Lite. Live3.1 and3.8 text requests are verified; the current saved model is3.8 Flash. Other model IDs need separate compatibility testing. [Native text API](https://ai.google.dev/gemini-api/docs/generate-content/text-generation).

## Private storage and limits

`private/host/provider.json` holds the host key/config at mode 0600; its directory is 0700 and ignored. These are local plaintext files, not Keychain encryption. The API/public settings never return the key. Manager/device bearer credentials are separate mode 0600 files; the device credential cannot change provider settings or USB controls. No provider key is copied to firmware, SD or vault. Variable-name equivalents: `GEMINI_API_KEY`, `MR_ROBOT_PROVIDER`, `MR_ROBOT_MODEL`.

Defaults: 20 attempts/day (UTC), 4/minute, 256 output tokens; one inference at a time. Attempts are reserved atomically in SQLite before inference and remain counted after failures/restarts. Only timestamps are retained; prompts/replies are not stored there. The browser keeps a short in-memory text history; each request sends just its current message. No raw audio, image or file endpoint exists.

## Service boundary

| Route | Required role | Purpose |
| --- | --- | --- |
| `POST /v1/chat` | Device or manager | Bounded text request; provider/model chosen on host |
| `GET /api/status` | Manager | Public settings and attempt count |
| `POST /api/settings` | Manager | Validate/save private configuration |
| `GET /api/device` | Manager | USB enumeration and actual device state |
| `POST /api/device/connect` | Manager | Match native USB and firmware handshake |
| `POST /api/device/command` | Manager | Whitelisted face/expression/brightness and hardware diagnostics |
| `POST /api/device/reply` | Manager | Replay a bounded caption without another inference |
| `POST /api/device/disconnect` | Manager | Clear a supported caption, cancel pending mic arming and release USB |
| `POST /api/voice/start` | Manager | Explicitly enable bounded tap or local wake mode |
| `POST /api/voice/stop` | Manager | Stop voice mode and clean up microphone/playback |

Host/Origin validation, bearer authentication, body limits, certificate verification, redirect rejection and bounded worker/socket timeouts are implemented. No arbitrary shell, filesystem path, model endpoint or executable command is accepted from chat input. A USB delivery failure preserves the AI reply and never regenerates it automatically.

OpenRouter and compatible services remain optional. OpenRouter checks a finite, nonexhausted provider-side key cap (including BYOK) before inference. Other remote compatible services require owner-confirmed spending controls, which are not independently verified. Local compatible endpoints can use loopback HTTP. Only Gemini has live acceptance in this session.

## Current limits

The round-screen caption is a short ASCII preview; the laptop holds the full text. Gemini Live receives bounded audio commands and returns speaker audio through the Mac. Tap-to-talk and local wake mode are implemented; repeated voice-turn reliability and physical switch acceptance remain pending. See [voice guide](GEMINI-VOICE.md). No independent on-device model, autonomous tool execution, camera submission or Wi-Fi service route is implemented.

See [status](PROJECT-STATUS.md), [roadmap](ROADMAP.md), [USB protocol](../protocol/README.md) and [Muse account explanation](MUSE-EVALUATION.md).


## Separate Muse image

Muse evaluation is no longer installed. Face Lab is the current Control Room-compatible firmware. A known Live model selected in the text setup form is rejected before a request; use the dedicated voice controls for Gemini Live.
