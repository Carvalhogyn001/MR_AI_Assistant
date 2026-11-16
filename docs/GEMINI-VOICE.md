# Gemini Voice on Mr. Robot

Updated 2026-11-13 for Face Lab 0.9.6. Control Room automatically arms both the green IO16 button and local wake phrase when Gemini is selected and one compatible USB board is available. After each spoken reply, the microphone reopens for a follow-up and Gemini carries the earlier turns in the same session.

## Run and use

From the project root:

```sh
~/.platformio/penv/bin/python -m pip install -r backend/requirements.txt
~/.platformio/penv/bin/python tools/manager.py --open
```

Keep Control Room running on the Mac, connect the Waveshare by USB, and select a configured Gemini connection with its Free-tier confirmation. The Mac arms voice even if the browser is closed. Wait for **WAKE LISTENING**, then say “Hey Mr. Robot” or press and release the green IO16-to-GND button. Speak when **LISTENING** appears. The microphone is on locally while waiting for the wake phrase. Idle audio stays on the Mac.

On 2026-11-14, the owner verified both triggers after the manager restored the saved key's Free-tier confirmation and raised the local daily attempt limit to 500 at the owner's request. The limit resets at midnight UTC and is independent of Google's quota. The companion panel reports a limit or missing confirmation if it prevents arming.

After each reply, speak again when **LISTENING / ASK A FOLLOW-UP** appears. You have up to 15 seconds to start a follow-up. When that window ends, Control Room closes the conversation and rearms for the next button press or wake phrase. Each conversation allows up to ten replies or ten minutes and uses one Gemini Live connection. Pressing the button during a follow-up ends that conversation. **Pause voice** turns off the microphone and frees the board for settings or diagnostics. **Resume voice** brings both triggers back. The board's 2.5-second microphone watchdog still protects against a lost host connection. [Talk button wiring](BATTERY-WIFI-WIRING.md)

An explicit greeting test is also available while Control Room USB is disconnected:

```sh
~/.platformio/penv/bin/python tools/voice.py greet
```

This uses one counted API attempt and plays through the board. It prints timing/result metadata only. It does not record the microphone.

## Local wake and response timing

The Waveshare microphone supplies 64 ms PCM blocks over USB. Sherpa-ONNX recognizes the exact phrase on the Mac. While waiting, the Mac keeps up to 320 ms of rolling audio in RAM to avoid clipping the start of the question. That lead-in can be included in the command after a trigger. Idle audio stays local and the microphone is off during the reply.

The recording ends after about 640 ms of quiet following speech, with an eight-second ceiling. The backend requests the prebuilt **Charon** voice using **Gemini 3.8 Live**, with no extended thinking setting. It waits for the service’s turn-complete event before sending another question. The board receives the reply in verified binary chunks and checks the full CRC before playback. The reply is still buffered before playback. Delays depend on question length, the Gemini service and USB transfer time. [Gemini Live model](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live) · [Live protocol](https://ai.google.dev/api/live) · [Voice options](https://ai.google.dev/gemini-api/docs/speech-generation)

The wake model uses the upstream Zipformer English phoneme dictionary. It runs locally and takes no credentials. Restore it on another Mac from the project root:

```sh
~/.platformio/penv/bin/python -m pip install -r backend/requirements-wake.txt
~/.platformio/penv/bin/python tools/setup_wake_model.py
~/.platformio/penv/bin/python tools/manager.py --open
```

The installer checks the release archive checksum before extracting the selected model files under ignored `private/wake-model/`. The pinned dependency is optional for tap-to-talk. [Sherpa keyword spotting](https://k2-fsa.github.io/sherpa/onnx/kws/index.html)

## Data and limits

- ESP32: verified existing ES7210 MIC1/slot0, signed little-endian PCM16, 16 kHz mono. Up to eight seconds of captured speech is 256,000 bytes. The red LISTENING indicator marks command capture.
- USB: separate MRV1 frames, 2048-byte input blocks with sequence and CRC, ordered output blocks up to 4096 bytes with a whole-reply CRC before amplifier enable. Bounded RAM buffers clear on completion, cancellation or expiry. [Protocol](../protocol/README.md)
- Host: rejects near-silence, bounds digital normalization to 16×, then uses fixed `gemini-3.8-live` over certificate-verified WSS. The existing private host key travels in a header, never a URL or firmware. `websockets==17.3` handles the WebSocket transport.
- Cloud: one bounded conversation per session, with no tools or automatic reconnect, model fallback or retry. The host uses the reply transcription briefly in memory to select a display expression and sends only that fixed expression to the board. Generation deadline 45 seconds, output at most 960,000 PCM bytes (20 seconds at 24 kHz). Existing persistent daily/per-minute attempt limits apply; failed upstream attempts count. Free-project confirmation is the owner's attestation, not independent billing inspection.
- Playback: ES8311 at 24 kHz/256× MCLK, mono duplicated to stereo, attenuated initially. Full-screen redraw is suspended during playback so SPI transfer cannot starve the short I2S queue; the face is rendered before speaking. Physical cancel polling remains active.

Google currently lists free-tier input/output for Gemini 3.8 Live, subject to project quotas. Free-tier content may be used to improve Google's products. The cloud receives bounded questions after the initial trigger and local speech detection on follow-ups. Idle follow-up audio stays on the Mac. [Pricing](https://ai.google.dev/gemini-api/docs/pricing), [Live transport/audio formats](https://ai.google.dev/gemini-api/docs/live-api), [WebSocket protocol](https://ai.google.dev/api/live).

The Mac must remain running and USB-connected. Wi-Fi transport, production LAN authentication/TLS, shared provider voices, richer memory and portable operation are future slices.

## Code and checks

`firmware/assistant/src/voice_protocol.cpp` validates frames; `voice_transport.cpp` owns device buffers/state/deadlines. Existing microphone/output drivers perform capture/playback/cleanup. `tools/voice_device.py` handles the serialized host USB transport. `backend/mr_robot_backend/gemini_live.py` owns the WSS turn; `voice.py` coordinates explicit mode, usage limits and exclusive device ownership. Control Room exposes manager-authenticated start/stop endpoints.

```sh
PYTHONPATH=backend ~/.platformio/penv/bin/python -m unittest discover -s backend/tests -q
~/.platformio/penv/bin/python tools/test_assistant.py
~/.platformio/penv/bin/python tools/test_device.py
~/.platformio/penv/bin/pio run -d firmware/assistant
```

Use [inventory](HARDWARE-INVENTORY.md), [decisions](DECISIONS.md) and [roadmap](ROADMAP.md) for hardware evidence and remaining acceptance. The factory recovery files and Face Lab 0.7 compiled recovery set remain private; Muse's retired flash/NVS was explicitly erased before this different layout was uploaded. No SD formatting occurred.
