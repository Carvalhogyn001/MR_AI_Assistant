# Optional status LED firmware

Face Lab **0.9.4 source** adds a small, disabled-by-default status-LED module. It has not been uploaded or electrically verified as part of this change. The working 0.9.3 image and its compiled recovery files remain separate. Read the [hardware inventory](HARDWARE-INVENTORY.md) and [power/LED guide](POWER-AND-STATUS-LEDS.md) before using any external circuit.

The conditional reservations are **Waveshare IO17 for green** and **IO18 for red**, each active-high at 3.3 V logic through its own verified series resistor. They were recorded in the inventory before coding. The owner identifies the separate two-leg kit red/green LEDs. The guide proposes setting aside two nominal 1 kΩ kit resistors for lower current than the official Freenove 220 Ω example. Actual resistor values/tolerances and LED polarity/current rating remain unmeasured. The actual board's GPS fitment is unresolved: the GPS-G option has an onboard LC76G sharing GPIO17/18, so no attached antenna does not prove those pins are free. This document is not an instruction to wire or energize the proposed circuit.

## Meaning and lifecycle

| Event | Green | Red |
| --- | --- | --- |
| Boot, idle or voice-ready | Off | Off |
| Ambient wake-word capture | Off | Off |
| Question capture has successfully started, phase `Recording` | On | Off |
| Thinking or receiving a reply | Off | Off |
| First reply PCM buffer is accepted after output setup, phase `Speaking` | Off | On |
| Capture/playback completes, fails, is cancelled or expires | Off | Off |
| Local microphone diagnostic or diagnostic tone | Off | Off |

Green marks the **question-capture interval**, including any silence within it. It does not detect whether the user is currently making sound. Red marks active reply PCM playback after output setup and acceptance of the first buffer; it does not independently prove audible sound. A button press starts a turn only when voice mode is armed; the existing switch remains press-and-release, not hold-to-talk. Pressing again during an active turn requests cancellation.

`statusLedPolicy` requires the appropriate phase and actual activity flags. Contradictory capture/playback activity produces both-off. `StatusLedScope` turns outputs off on every return from blocking microphone/output work. Streamed microphone start, wake-to-question transition and stop paths update the output directly; stream timeout and cancellation use the existing stop path. Amplifier shutdown also clears LED outputs. No additional display frames, timers, delays, audio reads or memory allocation are introduced.

## Default and future activation

`MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS` defaults to `0`. The normal module compiles without Arduino GPIO calls: it does not configure, read or write either candidate pin. USB status reports `status_leds_supported=true`, `status_leds_enabled=false`, `status_led_green=false` and `status_led_red=false`. These are software capability/command fields, not electrical measurements or physical part detection.

Only after actual variant, LED/resistor data and an unpowered circuit check are recorded should a reviewed hardware-specific build set `MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS=1`. There is no remote command to enable it. The enabled branch sets both inactive latches before configuring outputs and always turns an old LED off before another on. Actual LED current, behavior and cleanup still require bench acceptance. Existing USB status clients accept the additional fields within their existing 4096-byte reply bound.

## Verification — 2026-11-06

Before edits, the 0.9.3 source built successfully (22,004 static RAM bytes; 416,245 application flash bytes) and command/audio parser ASan/UBSan suites passed. Root-agent metadata showed 0.9.3 with display/touch ready, mic off, idle voice and continuing operation. A compiled recovery set with flash addresses, sizes and SHA-256 values was retained under ignored `private/backups/face-lab-0.9.3-led-baseline/`; it is not a complete flash/NVS backup.

The normal **0.9.4 build passes** with **22,004 static RAM bytes** and **416,689 application flash bytes**. These are build section sizes, not free heap or physical capacity. Existing command/audio parser sanitizer checks and actual-renderer host checks also pass.

Host checks compile the actual LED module twice: once with the default macro omitted, once with a fake-GPIO opt-in. They cover all phases/activity combinations, no GPIO operation before initialization, zero GPIO calls in the default build, inactive startup latches, no simultaneous green/red output, unchanged-state write suppression, and scope/explicit cleanup. They use ASan/UBSan. These tests do not drive physical pins.

```sh
python3 firmware/assistant/tests/test_status_leds.py
python3 tools/test_assistant.py
python3 firmware/assistant/tests/preview_display.py
~/.platformio/penv/bin/pio run -d firmware/assistant
```

Physical LED acceptance is pending the hardware facts and circuit. No claim of a wired, lit or measured LED is made. Installation/bench results belong in [Project Status](PROJECT-STATUS.md).
