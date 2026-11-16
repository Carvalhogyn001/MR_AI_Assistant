# MR. Robot Project Charter

## Goal

Create a round-screen voice assistant on the Waveshare ESP32-S3-Touch-AMOLED-1.75, with useful local controls and optional remote intelligence through Muse or an authenticated API backend. Explore offline command recognition without promising a conversational language model on the ESP32.

## Known equipment

- New Waveshare 1.75 board: primary assistant, connected and identified; no enclosure
- Supplied Waveshare speaker: owner confirmed, initially unattached
- Freenove ESP32 Wrover with previously verified camera: optional secondary node
- New reported 128 GB microSD: filesystem and real capacity pending; older 256 GB claim retired as unsupported
- Older LCD/audio/sensor kit: retained, not needed for first Waveshare milestones
- Mac development machine
- OpenRouter account and API access planned

## Architecture direction

The ESP32 handles device responsibilities: sensors, camera capture, local buffering, SD storage, network connection, and output control. A backend proxy will hold the OpenRouter key, apply rate limits and request validation, and return a deliberately small response for the ESP32 to render or speak.

Direct production calls from the ESP32 to OpenRouter are excluded because a firmware image can expose a long lived API key.

## First milestone

See [roadmap](ROADMAP.md). First: observe factory behavior, identify the board/memory, privately preserve factory flash, run the USB/PSRAM diagnostic and record actual output. Display/touch, microphone, speaker and SD follow as separate slices. Measured power budget and a 3D-printed enclosure come later.

## Explicitly deferred

- Wake word detection
- Continuous audio recording
- Autonomous actions
- Facial recognition or biometric identification
- Exposing OpenRouter credentials on the device
- Storing sensitive images or audio without a retention policy
