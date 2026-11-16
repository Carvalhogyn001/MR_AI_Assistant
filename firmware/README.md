# Firmware Workspace

`platformio.ini` and `src/main.cpp` contain the existing Freenove ESP32 Wrover camera portal. It falls back from native JPEG to RGB565/software JPEG for the previously detected camera. Existing helper tests are in `tests/`.

Build from the project root with `pio run -d firmware`; run helper tests with `python3 tools/run_host_tests.py`. Hardware pin evidence is in `docs/HARDWARE-INVENTORY.md` and `docs/SD-CAMERA-PIN-MAP.md` at the project root.

The new Waveshare diagnostic is isolated in `waveshare-bringup/`. Build it with `pio run -d firmware/waveshare-bringup`. Never flash the Freenove build onto the Waveshare or vice versa. The camera portal is a lab prototype for a controlled bench. It uses a device-derived Wi-Fi password and lacks application-level authentication. Leave the camera portal off around untrusted devices and keep it off shared or public networks.

The current Waveshare application is now `assistant/`: custom face/USB controls and read-only card metadata. See its README and the project status; the memory diagnostic remains the recovery baseline.
