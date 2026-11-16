# MR. Robot Face Lab

Current source build: **0.10.0**, with four swipe screens, three more expressions, text and image activity reactions, and a USB-fed Gallery preview. It also carries the paged Ollama captions and local green-button capture from 0.9.8. [Ollama device guide](../../docs/OLLAMA-DEVICE.md). Optional status LEDs remain disabled pending physical verification.

The **0.9.3** display refinement preserves 0.9.2's local wake, pause-based speech and optional IO16 talk-button flow. The face remains familiar at idle; listening, thinking, receiving, speaking and stopped states now have distinct symbols and explicit microphone labels. [Interface and acceptance](../../docs/DEVICE-INTERFACE.md) · [Voice setup, data flow and limits](../../docs/GEMINI-VOICE.md).

The build and host-rendered previews pass; physical acceptance of the revised pixels is tracked separately in PROJECT-STATUS.md. Compiled 0.9.2 and 0.9.3 baselines are preserved privately. Historical physical speech acceptance remains recorded below.

The custom Waveshare application lives here. The verified USB/memory diagnostic stays in `../waveshare-bringup/`; the older Freenove camera stays in the parent firmware project. Do not flash one board's build onto another.

## Responsibilities

| Module | Responsibility |
| --- | --- |
| `include/board_pins.h` | Documented non-C display, touch, card and speaker assignments |
| `include/app_state.h` | Face/expression/brightness state, independent of transport/provider |
| `src/control_protocol.cpp` | Bounded, validated USB commands; no Arduino dependencies |
| `src/status_leds.cpp` | Default-disabled, conditionally verified external capture/playback LED output and cleanup |
| `src/face_renderer.cpp` | CO5300 display and vector face drawing in a single PSRAM buffer |
| `src/main.cpp` | Startup, bounded serial input, swipe navigation and render scheduling |
| `src/image_transfer.cpp` | Bounded RGB565 USB transfer into volatile PSRAM |
| `src/card_inspector.cpp` | Raw SD metadata reads without filesystem or writes |
| `src/touch_input.cpp` | Controller identification and bounded IRQ-driven touch samples |
| `src/audio_output.cpp` | Fixed quiet diagnostic tone or bounded 24 kHz voice playback, TX-only I2S and amplifier cleanup |
| `src/microphone_input.cpp` | Bounded level diagnostic or explicitly triggered 16 kHz MIC1 PCM capture |
| `src/voice_protocol.cpp` | Arduino-independent MRV1 validation, byte bounds and CRC32 |
| `src/voice_transport.cpp` | Voice state, PSRAM clearing, physical tap/cancel and transfer/arming deadlines |
| `lib/es8311_vendor/` | Pinned Apache-2.0 codec driver, provenance and minimal Arduino2 adapter |
| `../../tools/device.py` | Reusable USB client and initial command-line controls |

Display dependency: GFX Library for Arduino **1.5.9**, pinned for the installed Arduino **2.0.17** core. The manufacturer's library version 1.6.4 was tried first but requires the Arduino3 peripheral-manager header; the compiler rejected it before hardware upload. Version1.5.9 includes the same CO5300/QSPI interface and supports this core. Upstream code is not copied into our modules. Board pins, 466×466 geometry and offset6/0 follow the manufacturer example. One RGB565 frame uses 434,312 bytes, with allocation rounded to 434,320 bytes for 16-byte alignment. Full-frame aligned flushes avoid CO5300 odd-window restrictions. This prototype targets a maximum 10 frames/s; measure the actual frame count, not that limit, as performance.

No network, AI service or PMIC driver is started. Version 0.6.0 adds an explicit four-second microphone level measurement with an onscreen indicator; no capture starts at boot. Version 0.4.0 adds an explicit USB `tone` speaker test; no audio starts at boot. Version 0.3.0 adds the documented CST9217 touch driver. Version 0.2.0 initializes SDMMC only for an explicit `card` request, then deinitializes it. No filesystem is mounted, listed, written or formatted. The amplifier stays disabled except during a requested tone or voice playback, and is disabled during cleanup. Expressions are cosmetic. Settings reset to pixel/neutral/brightness 96 on reboot.

## Build and acceptance

```sh
python3 tools/test_assistant.py
python3 firmware/assistant/tests/test_status_leds.py
python3 firmware/assistant/tests/preview_display.py
~/.platformio/penv/bin/python tools/test_device.py
pio run -d firmware/assistant
# Standalone boards only. For the current dual-boot board, see ../muse-evaluation/README.md.
pio run -d firmware/assistant -t upload --upload-port PORT
~/.platformio/penv/bin/python tools/device.py --port PORT status
~/.platformio/penv/bin/python tools/device.py --port PORT face orbit
~/.platformio/penv/bin/python tools/device.py --port PORT expression happy
~/.platformio/penv/bin/python tools/device.py --port PORT brightness 80
~/.platformio/penv/bin/python tools/device.py --port PORT card
~/.platformio/penv/bin/python tools/device.py --port PORT tone
~/.platformio/penv/bin/python tools/device.py --port PORT mic-arm
# Tap once when MIC TEST READY appears; speak during the red indicator.
~/.platformio/penv/bin/python tools/device.py --port PORT mic-cancel
```

Run from the project root. Use a currently enumerated, positively identified PORT. Full factory backup already exists privately; never overwrite it during development.

Acceptance: display initialization returns success, frame counts advance, serial commands change reported state, invalid/oversized commands leave state unchanged, and the owner visually confirms a stable complete face and visible style/expression changes. Software acknowledgments alone do not prove panel pixels. Record actual results in `docs/PROJECT-STATUS.md` at the project root.

Latest acceptance: corrected Classic visually confirmed, USB state/control rejection/recovery passed, card metadata read succeeded and frames continued afterward. GFX 1.5.9 needs the explicit IPS boolean before width/height; do not copy the 1.6.x constructor blindly. Geometry is checked before reporting ready. Other styles have not each received an independent owner visual review.

## Touch slice (0.3.0)

SensorLib 0.3.1 is pinned, matching the manufacturer's CST9217 example. Touch initialization owns the shared Wire bus once; future audio/PMIC modules must reuse it. Physical taps cycle Classic→Pixel→Orbit→Classic, with press/release tracking and 300 ms debounce. Footer says TAP TO CHANGE FACE when initialized. No coordinates are mirrored for location-specific controls; raw orientation needs verification first. Status exposes touch_ready, touch_events and last raw coordinates. Physical acceptance is recorded separately from initialization in PROJECT-STATUS.md.

## Speaker slice (0.4.0)

A fixed generated440Hz/400ms tone uses16kHz stereo16-bit I2S TX, MCLK42/BCLK9/WS45/DOUT8, existing Wire port0 and ES8311 at 0x18. NS4150B enable46 is active-high, commanded LOW at boot and all cleanup paths. The tone test does not enable ES7210 or RX. See [protocol](../../protocol/README.md) for exact amplitude/ramp and retry semantics; see driver README/LICENSE for source provenance. The codec initialization includes internal ADC setup but no microphone samples are read. No media file or SD filesystem is used.

Acceptance:0.3.0 baseline first, successful0.4.0 build/upload, `tone` returns audio_error0/audio_stage complete with tone_tests incremented, frames continue and touch remains responsive, owner hears a short clean quiet tone. I2C/DMA results alone cannot establish acoustic output. Runtime results belong in PROJECT-STATUS.md; owner has now confirmed hearing the replayed beep; post-audio touch also passed.

## Microphone level slice (0.6.0 history)

An explicit `mic` request initializes the documented ES7210 and four-slot TDM RX. It returns only RMS/peak/clipping numbers after a128ms settling interval and four-second measurement. A red MIC LEVEL TEST indicator appears during acquisition; raw application samples are cleared/discarded, never streamed to the PC or saved. ES7210 stop, handle release and I2S release run on every exit. See protocol for exact fields and the vendor README for driver/stop-sequence provenance. No automatic retries, continuous listening, speech recognition or duplex/AEC is implemented.

Acceptance requires actual 64,000-frame measurement/error0, reasonable nonconstant unclipped microphone levels, quiet-versus-speech response, and continuing face/touch after cleanup. Build success alone does not prove usable audio. Slot assignment follows the pinned Waveshare BSP; playback-reference correlation is separate future verification.

Current physical acceptance: owner hears the generated tone, sees the microphone indicator and starts capture with a tap. Speech RMS in slots 0/2 rises 11.9×/15.125× over room levels without clipping; cleanup and mic→speaker initialization pass on the same session.0.6.0 aligns codec analog/global/pair power values with the retained maintained driver. Prior missed timing windows do not establish a standalone-driver defect.
