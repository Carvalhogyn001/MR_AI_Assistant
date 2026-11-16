# MR. Robot

A personal AI gadget built in small, verified steps. Primary target: **Waveshare ESP32-S3-Touch-AMOLED-1.75**. The Freenove ESP32 Wrover stays available as a separate camera device.

This source snapshot includes the firmware, host backend, Control Room and setup notes. Local photos, captures and backup images are omitted.

## Start here

- [Current state and next action](docs/PROJECT-STATUS.md)
- [Beginner setup and visual guide](docs/FIRST-CONNECTION.md)
- [Hardware evidence, voltages and pin assignments](docs/HARDWARE-INVENTORY.md)
- [Architecture and AI choices](docs/ARCHITECTURE.md)
- [Milestones and screen ideas](docs/ROADMAP.md)
- [Muse findings and correct board profile](docs/MUSE-EVALUATION.md)
- [128 GB card validation](docs/SD-CARD-PLAN.md)
- [Green talk button, AA power and Wi-Fi wiring](docs/BATTERY-WIFI-WIRING.md)
- [Talk button, camera and display drawings](docs/BREADBOARD-CAMERA-DISPLAYS.md)
- [Two-AA power plan and green/red status LEDs](docs/POWER-AND-STATUS-LEDS.md)

## Current state — 2026-11-14

**Face Lab 0.10.0** adds swipe navigation through Face, Settings, Device Status and Gallery. The browser keeps typed chat and generated PNGs locally. Control Room has a tall conversation pane and a Three.js pixel companion with orbit controls and an exploded view. Z-Image Turbo can send a preview to Gallery over USB. The Waveshare still has Muse and Face Lab side by side. Switch with **Providers → Save & apply**. [Web interface](docs/CONTROL-ROOM-DESIGN.md) · [Device interface](docs/DEVICE-INTERFACE.md) · [November 14 audit](docs/SYSTEM-AUDIT-2026-11-14.md)

**Optional status LEDs** are disabled in the installed build until the GPIO and parts checks are complete. The two-AA holder needs an identified regulator and USB power interface. Battery power alone does not replace the current USB voice-data connection. [Power and LED drawings](docs/POWER-AND-STATUS-LEDS.md) · [Firmware behavior](docs/STATUS-LEDS-FIRMWARE.md)

Gemini voice arms automatically with Control Room running and the Waveshare connected by USB. Say “Hey Mr. Robot” or press and release the green button. In Connection, switch to **Ollama · local** for text on the Mac and green-button questions with Gemma 4 12B. [Ollama device guide](docs/OLLAMA-DEVICE.md) Muse pairing and integration are tracked in the [provider plan](docs/VOICE-PROVIDERS.md). [Voice guide](docs/GEMINI-VOICE.md) · [Project status](docs/PROJECT-STATUS.md)

**Gemini 3.8 Flash** handles text. Gemini 3.8 Live uses the private host key and existing attempt limits. Keep the Mac and USB connected for wake detection, Gemini and power. Earlier firmware recovery images remain in ignored storage.

From this folder, start/open the external default browser with:

```sh
~/.platformio/penv/bin/python tools/manager.py --open
```

The local URL is http://127.0.0.1:18765/. Existing verified service is reused. See [API setup](docs/API-HOST-SETUP.md) and [Muse build/provisioning guide](firmware/muse-evaluation/README.md).

Muse inference runs remotely over Wi-Fi, not as an on-device language model. After pairing, its Wi-Fi path is intended to operate without the Mac. The current Gemini USB route still needs the Mac. The 128 GB card is storage, not extra RAM.

## Project map

| Path | Purpose |
| --- | --- |
| `firmware/` | Existing Freenove camera firmware |
| `firmware/waveshare-bringup/` | Separate Waveshare USB/memory diagnostic |
| `firmware/assistant/` | Independent Face Lab application and recovery baseline |
| `firmware/muse-evaluation/` | Muse live-voice overlay and setup guide; pinned SDK stays in ignored external/ |
| `protocol/` | USB commands for the future PC manager |
| `backend/` | Authenticated laptop service, native Gemini and optional provider adapters |
| `manager/` | Local Control Room GUI |
| `docs/` | Canonical engineering documentation |
| `docs/visuals/` | Editable diagrams and screen concepts |
| `tools/` | Repeatable verification utilities |

Read [AGENTS.md](AGENTS.md) before changing hardware or firmware. Never wire 5 V logic to an ESP32 GPIO or embed a production OpenRouter key in firmware.

New boundaries: [PC manager plan](docs/DEVICE-MANAGER-PLAN.md), [USB controls](protocol/README.md), [AI provider foundation](backend/README.md), [firmware trust](docs/FIRMWARE-TRUST.md). Initial PC control: `~/.platformio/penv/bin/python tools/device.py status`; replace `status` with `face orbit`, `expression happy`, `brightness 80`, `card`, `tone`, `mic`, `mic-arm`, or `mic-cancel`. Use `--port PORT` before the command if more than one device is connected.
