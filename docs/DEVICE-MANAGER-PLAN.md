# PC Device Manager Plan

Owner direction, 2026-10-29: a future system on the PC should select different faces and manage the device. The owner accepts remote Muse and also wants other AI APIs. Keep visual style independent of the AI provider.

## Foundation implemented now

- Custom application: `firmware/assistant/`, separated from the memory diagnostic and Freenove camera.
- Three built-in face IDs, four cosmetic expressions and bounded brightness.
- Bounded USB protocol and reusable Python client in `tools/device.py`; a graphical UI can call that client without shelling out.
- Host text-provider interface in `backend/mr_robot_backend/providers.py`: mock, OpenRouter and explicitly configured compatible chat services. Eight test methods exercise the adapter with synthetic responses. No live provider, speech path or device-to-backend request exists yet.

## Planned components

```text
PC manager UI → Local host service
Local host service → USB device client
USB device client → ESP32 face and hardware state
Local host service → Face/profile catalog
Local host service → AI provider adapters
AI provider adapters → Selected remote API
AI provider adapters → Optional local host model
Muse SDK evaluation → ESP32 face and hardware state
```

The first graphical version should run locally and show detected device, firmware version, current face, actual capabilities and errors. It should offer the three supported faces, expressions and brightness, with a preview generated from the same design parameters. A selected provider is distinct from a connected/working provider; a physically inserted card/speaker is distinct from a mounted/working peripheral.

Future UI responsibilities: device discovery, face/profile selection, selected model/provider, audio controls, SD status, logs limited to non-sensitive diagnostics, and explicit reconnect/update flows. Build only controls whose device capability exists. Show unavailable functions honestly. Do not add arbitrary shell, file-path or firmware commands to the first manager.

## Integration order

1. Complete display and USB visual-control acceptance (current slice); validate touch independently.
2. Verify audio input/output and card metadata separately. Card formatting and retained recordings are not part of face selection.
3. Build a small local manager over the existing USB client. Choose UI packaging then; no extra frontend dependency is justified yet.
4. Add an authenticated host AI service with persistent usage/cost limits, cancellation, bounded requests/responses and selected provider. Keep provider keys on the host. Tests should reject unauthenticated requests before any upstream call.
5. Connect a bounded text request/response, then separately add speech and camera input. Muse uses its own SDK/pairing and must be evaluated separately; do not imply its service is a generic chat-completions endpoint.
6. Add validated face assets/profiles and explicit storage/persistence after SD/NVS verification. Later LAN management or firmware updates need their own authentication/recovery design.

Current protocol: [device control](../protocol/README.md). Current acceptance: [project status](PROJECT-STATUS.md). See [firmware trust](FIRMWARE-TRUST.md) for the factory-demo question and [architecture](ARCHITECTURE.md) for provider/device boundaries.

## Implemented Control Room — 2026-10-30

The first local GUI now exists in manager/, with separate HTML/CSS/JS and no frontend framework or CDN. tools/manager.py starts the loopback host service on 18765. Face/expression/brightness previews, native USB discovery/connect/disconnect, explicit hardware diagnostics, host-held provider setup and text chat are implemented. Current device status is polled through one reusable serialized connection; supported captions are cleared on disconnect. API keys are never returned to the UI after saving.

Native Gemini 3.1 Flash-Lite is live-verified in the browser. The owner confirmed the generated greeting on the round screen through Face Lab 0.7.0. Mock mode is labelled explicitly. Unsaved connection changes block sending; failed/lost inference requests are not automatically retried. Gemini's Free-tier flag is owner attestation. OpenRouter/compatible adapters remain available but have synthetic acceptance only.

26 backend tests, two USB-client tests, parser ASan/UBSan and physical caption observation support this milestone. Local authentication/body/Origin limits and persistent attempt reservations are implemented. Remaining: voice path, cancellation, validated asset/profile persistence, optional LAN/TLS deployment and richer previews. This supersedes the earlier statement that no GUI or running service exists.

## Current interface — 2026-11-06

The November 6 layout separated Conversation, Device and Connection, with a responsive light layout, explicit microphone/voice state and progressive disclosure for settings/diagnostics. Wake and tap voice modes use the existing Mac-hosted Gemini Live route. Stop remains available across tabs; stale/lost status is explicitly unavailable and read-only polls time out after ten seconds. Pending actions and unsaved settings retain their ownership while polling runs.

The 0.9.3 round display retains the three face styles and adds clearer capture, thinking, receiving, playback and recovery states. The web illustration is not a screen mirror or audio meter. Profiles/assets, persistent storage and production LAN/TLS remain future work. [Web design](CONTROL-ROOM-DESIGN.md) · [Device design](DEVICE-INTERFACE.md) · [Final audit](INTERFACE-AUDIT.md)

The November 13 [Control Room redesign](CONTROL-ROOM-DESIGN.md) uses a responsive terminal layout and a shared companion panel. The underlying host and device routes are the same.
