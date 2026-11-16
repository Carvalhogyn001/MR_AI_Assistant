# MR. Robot Roadmap

The interface refresh now includes System/Light/Dark themes, accepted idle/tap behavior on Face Lab 0.9.3, and power/status-LED drawings. Optional LED source is built as 0.9.4 but remains disabled and uninstalled. Next are physical talk-switch acceptance, LED/AA hardware checks, repeated voice-turn reliability, a separate camera node and operation away from the Mac. See [voice and power plan](VOICE-AND-POWER-PLAN.md).

Updated 2026-11-06. **[X] = completed with the evidence stated. [ ] = still pending.** Each hardware slice requires inventory → minimal code → measured observation → documentation.

## 1. Foundation and recovery

- [X] Identify the primary board as Waveshare ESP32-S3-Touch-AMOLED-1.75, not 1.75C; record pins/voltage/source evidence.
- [X] Confirm 16 MB flash, 8 MB physical PSRAM, 64 KiB memory write/read and continuing USB heartbeats.
- [X] Preserve the original full flash as a local, ignored recovery file; verify 16,777,216-byte size and SHA-256. It is not part of our application build.
- [X] Preserve the separate Freenove camera project and earlier hardware observations.
- [X] Save source manifests, original product images, decisions and vault context.
- [X] Confirm owner direction: independent application using documented drivers/SDKs, not modifications of the factory demo.

## 2. Our application and face controls

- [X] Create separate board, state, renderer, protocol and card-inspector modules under `firmware/assistant/`.
- [X] Draw the Classic face and obtain owner visual confirmation after correcting the library constructor mismatch.
- [X] Implement three face IDs, four cosmetic expressions and brightness controls through USB.
- [X] Verify USB state changes, malformed/oversized input rejection and recovery on hardware; run parser sanitizer checks.
- [X] Create a reusable PC USB client in `tools/device.py`.
- [X] Initialize and identify actual CST9217 at 466×466 through the documented I2C bus; Face Lab 0.3.0 build/upload/status verified.
- [X] Owner physically tapped/released the screen and confirmed the face changes on each tap. Long holds, multitouch and coordinate calibration remain separate tests.
- [ ] Verify coordinate orientation across center and edge positions before location-specific buttons/gestures.

## 3. Audio

- [X] Owner reports supplied speaker connected to SPK.
- [X] Record manufacturer supplied-speaker specification 8 Ω / 2 W and maintained BSP amplifier supply 3.3 V/GPIO46 active-high. Physical speaker markings are not independently read.
- [X] Initialize ES7210 and measure 32,000 frames/slot with RMS/peak/clipping results, visible-indicator code and successful shutdown; no persistent/raw recording.
- [X] Owner confirmed the red indicator and speaking during tap-triggered capture; mic slots 0/2 increased11.9×/15.125× over room levels, with zero clipping.
- [X] Initialize ES8311 and TX-only I2S for an explicit quiet generated tone; verify error0, completed transfer/cleanup, continuing frames and no automatic replay.
- [X] Owner heard the replayed beep; a real tap afterward changed Classic→Pixel, with touch counter1 and continuing frames.
- [X] Record published four-slot mapping; measure voice response in slots 0/2 and verify sequential RX cleanup→speaker TX on one session, with continuing frames and no reboot.
- [ ] Verify playback-reference correlation, simultaneous TX/RX clocks and AEC/feedback behavior.
- [X] Verify unused 60-second arming expiry: observed 60.19 seconds, no capture, continuing frames. USB arm/cancel and one-tap disarming also pass.
- [X] Add explicit tap/button-to-talk, cancel and recording indication in Face Lab; physical talk-switch acceptance remains separate below.

## 4. SD storage

- [X] Read raw controller capacity and boot-sector signature without filesystem mount/writes:124,383,133,696 bytes, exFAT signature.
- [X] Verify display frame counters continue after raw inspection.
- [X] Record owner confirmation that the card is new/empty and authorization to format it when needed. Target only this positively identified card.
- [ ] Select a supported filesystem for the file-storage slice. Current card remains exFAT; formatting is not needed for raw identification.
- [ ] Format the identified empty card if the selected firmware/filesystem requires it; verify resulting filesystem/capacity.
- [ ] Write a fresh project test file, close/reopen, compare hash and repeat after reboot.
- [ ] Run an appropriate full-capacity write/read integrity test before trusting large media storage; raw advertised capacity alone is insufficient.
- [ ] Define retention and maximum space before storing personal audio/images/notes.

## 5. Muse service integration — deferred after final discovery failure

- [X] Verify the SDK connects to remote Muse; it does not supply local model weights.
- [X] Verify the non-C `s3n` profile and ESP-IDF 6.0.1 requirement.
- [X] Verify pairing requires a Muse Gadgets SDK token and Muse account/app; it does not use an OpenRouter key.
- [X] Owner obtained/replaced a token; validate its private local format and provision into device NVS with an ACK. No secret values in notes.
- [X] Verify board Wi-Fi connected and owner-visible Muse face/Settings; display recovers after USB reconnection on2026-10-31. No permanent display fix established.
- [ ] Complete phone account enrollment and physical BOOT confirmation during an active request.
- [X] Inspect live BLE flags without reflashing: advertising active, no client; add/test a bounded redacted USB pairing monitor (nine helper tests, 10-second hardware watch).
- Independent Android scanner check deferred: owner declines installing another phone app; Android 17 is owner-reported, Muse version unknown. Final restart/Bluetooth-toggle retry still cannot discover the gadget. Owner selects Gemini voice; Muse pairing/audio acceptance remain uncompleted.
- [ ] Verify rediscovery/retry after an expired pairing request without requiring a USB power cycle.
- [X] Retain SDK pin 1b894f5 and install isolated ESP-IDF 6.0.1/toolchain plus recommended CMake/Ninja.
- [X] Owner selected Muse again; build/validate/flash non-C live-voice image,2,166,784 bytes, hashes verified; token ACK passes.
- [ ] Verify audible conversation, BOOT start/hang-up and30 s idle / 180 s total call bounds on the paired device.
- [X] Isolate Muse ESP-IDF 6 from Face Lab Arduino 2; retain our source and 0.7.0 compiled recovery artifacts.
- [ ] Integrate a shared Mr. Robot face/interaction design across provider firmware routes.
- [ ] Verify BLE pairing, Wi-Fi provisioning and one remote conversation with the owner's account.
- [ ] Verify reconnect, cancellation, data handling and actual account/service limits; document measured latency/memory.

## 6. Other AI providers and host service

- [X] Create host text adapters: native Google Gemini first, explicit mock, OpenRouter and compatible services.
- [X] Pass 26 backend tests for native/compatible requests, TLS, secret redaction, auth/scope, limits/restarts/concurrency and failed USB delivery. Fixtures use no real keys.
- [X] Build an authenticated loopback host service, bounded requests/responses, persistent attempt limits and output-token ceilings; verify OpenRouter key-cap checks synthetically.
- [ ] Complete direct device-request/audio transport and production LAN/TLS design. Gemini billing is owner-attested; generic remote monetary caps are not independently verified.
- [X] Verify native Gemini 3.1 Flash-Lite using a privately configured host key and owner-confirmed Free project; browser reply and round-screen greeting accepted.
- [X] Add bounded USB caption previews with provider labels, no text echo in status and explicit clear/disconnect behavior.
- [X] Verify caption expiry at 60.54 seconds:816→1416 frames, caption absent/provider none, no restart.
- [X] Verify Gemini 3.8 Flash host text; add model suggestions and supported low/minimal thinking settings, with 28 backend tests.
- [X] Implement/build/upload independent Face Lab 0.8 USB capture/playback and Gemini Live host route; explicit arming/tap, bounds, checksums, no automatic retry, keys on Mac; 37 backend tests and parser sanitizers pass.
- [X] Receive a real five-second Gemini Live greeting and complete device playback; owner hears it, with choppiness in the first build.
- [X] Verify clean playback after display scheduling adjustment and one physical spoken question/reply; owner confirms clear speech, metadata completed turns=1 and audio/mic error0.
- [X] Verify host Stop during a later generation cancels without retry; device returns idle/mic inactive and frames/uptime continue. Cancelled attempt remains counted.
- [X] Verify manager USB disconnect/reconnect while idle preserves runtime: uptime 291364→291471 ms, display/touch ready and microphone inactive.
- [X] Add explicit “Hey Mr. Robot” mode with local Mac keyword spotting. Exact synthetic phrase matched and “Hey Robert” did not.
- [X] Select Charon in Gemini 3.8 Live and play a reply to synthetic speech on the Waveshare.
- [X] Stop capture on a short pause and add verified binary USB playback uploads. The 48 KB transfer improved from 0.683 s to 0.209 s in the bench test.
- [X] Complete one wake-mode reply in Control Room with no screen taps or physical button presses. Host measured 2.378 s from request start to playback command.
- [ ] Confirm the owner's impression of Charon and measure repeated conversational turns after the USB acknowledgement recovery fix.
- [X] Assign and implement the debounced IO16 talk switch input and draw the breadboard wiring.
- [ ] Fit and test the physical talk switch using the labeled H2 contacts.
- [ ] Verify physical cancel, unused arming expiry, disconnect cleanup and repeated voice-turn reliability on hardware.
- [ ] Add a local-host model route after inventorying host compute/models; no silent cloud fallback.
- [ ] Optionally benchmark a small offline ESP-SR command vocabulary on the ESP32.

## 7. PC device manager

- [X] Define separate firmware, USB protocol/client and provider layers.
- [X] Save the manager architecture and supported/current capability boundaries in DEVICE-MANAGER-PLAN.md.
- [X] Create and inspect Control Room for device state, face/expression/brightness preview/selection and explicit hardware tests; native USB controls pass.
- [X] Refresh Control Room with responsive Conversation/Device/Connection tabs and explicit voice/recovery states; browser checks use isolated mock hardware and provider data.
- [X] Build/upload Face Lab 0.9.3 display refinement; verify display/touch readiness and advancing uptime across USB reconnects. Preserve a private 0.9.2 rollback set.
- [X] Complete independent interface audit, reproduce/fix Stop visibility and stalled-status defects, and pass 11 web regressions plus existing firmware/backend checks. See [audit](INTERFACE-AUDIT.md).
- [X] Obtain owner visual/tap acceptance of the revised 0.9.3 screen: on 2026-11-06 the owner confirms the face/label look clear and a tap changes the face.
- [X] Add System/Light/Dark appearances throughout Control Room; check desktop/mobile layout, preference persistence, authentication lock after reload and shared Stop using an isolated browser fixture.
- [X] Complete an independent follow-up audit after the three agents: no new code defect in scope; theme tests, LED/parser/renderer sanitizers, build and guide checks pass.
- [ ] Recheck active voice-state readability, cancellation and repeated voice turns on 0.9.3 hardware.
- [ ] Add validated profiles/assets and persistence after storage verification.
- [X] Add provider/model/key setup and actual usage/device state, explicit mock mode and live Gemini text; keys stay on host.
- [ ] Design authenticated LAN management/update/recovery separately before exposing those capabilities.

## 8. Optional camera, battery and enclosure

- [X] Identify the Freenove camera, GPIO extension and separate LCD/LED matrix in the retained photos. Save the two-board layout.
- [ ] Reconnect Freenove by its own USB-C cable and verify a still capture. Then add the authenticated local Wi-Fi path through the Mac.
- [ ] Resolve the 1602A contrast, supply and pull-up checks and identify the 8 × 8 matrix pinout and current limits before wiring either display.

- [X] Record the owner's choice of the existing two-AA holder/cells and save the new breadboard photo unchanged. Draw the conditional converter route and LED branches in project and vault.
- [X] Build and host-test optional 0.9.4 LED support: green question capture, red reply PCM playback, cleanup off, and no GPIO use in the ordinary build. Installed firmware remains 0.9.3.
- [ ] Establish actual GPS fitment/free GPIO17/18, verify kit LEDs and series resistors, and accept the assembled circuit before enabling/uploading LED support.
- [ ] Identify a suitable regulated converter/USB source interface for the two-AA cells after chemistry, polarity, discharge range and peak demand are established.
- [ ] Measure USB/display/audio/Wi-Fi peak current and choose a verified battery/protection/charge configuration. Do not connect AA cells directly to BAT.
- [ ] Measure the actual board, speaker and connectors, then design the owner's3D-printed enclosure.
- [ ] Validate airflow, microphone/speaker openings, USB access, mounting and safe battery placement.

Actual results and commands: [status](PROJECT-STATUS.md). Hardware facts: [inventory](HARDWARE-INVENTORY.md). Architecture changes: [decisions](DECISIONS.md).

## Screen direction

Implemented source preview: Face Lab 0.9.3 states and [rendering/acceptance details](DEVICE-INTERFACE.md). The original screen concept sheet is retained as historical design context, not installed behavior.

- **Idle/ready:** retain the expressive face, distinguish cosmetic face changes from an explicitly armed voice turn, and show whether the microphone is on.
- **Wake/listening:** distinguish Mac-local wake detection from captured questions. Coral status graphics and explicit microphone labels; listening bars are symbols, not a measured waveform.
- **Thinking/receiving:** distinguish generation from reply transfer, with a cancel hint and no invented progress percentage.
- **Speaking/stopped:** show speaker activity or recovery in Control Room. Keep the established audio scheduling and cancellation behavior.
- **Host reply:** fit bounded text inside the round display; the full reply remains on the Mac.
- **Future only:** audio volume controls, on-screen caption pagination, clock/timer and location-specific gestures need separate implementation and verification.

Use partial screen buffers and simple vector faces before full-screen animations; a 466 × 466 RGB565 frame is 434,312 bytes (~424 KiB), and double buffering costs about twice that before audio, network and models. Published 16.7M display colors do not require a 24-bit framebuffer in our application.

## Nice to have, after the core conversation works

Touch expressions, tilt-to-wake using the built-in IMU, focus timer, push-to-save notes, SD photo faces, explicit voice memo recording, optional camera questions and a charging dock. A local-host model can provide private richer conversation. The implemented Mac-local “Hey Mr. Robot” detector still needs longer false-trigger and repeated-turn checks. Autonomous actions and motors remain separate future scope. No additional purchase is justified for the first USB/display/audio milestones.
