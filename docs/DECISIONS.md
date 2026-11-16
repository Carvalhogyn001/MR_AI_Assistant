# Architecture Decisions

## ADR 001: Protect the OpenRouter API key

- **Status:** accepted
- **Decision:** Use a backend proxy to call OpenRouter. The ESP32 authenticates to that proxy with device scoped credentials.
- **Reason:** Any long lived key embedded in ESP32 firmware can be extracted from the device or a firmware image.
- **Verification:** Before API integration, confirm the ESP32 firmware contains no OpenRouter key and the proxy rejects unauthenticated requests.

## ADR 002: Use evidence driven hardware integration

- **Status:** accepted
- **Decision:** Do not select drivers or pin assignments until the exact component model and electrical interface are inventoried.
- **Reason:** ESP32 camera, SD, I2S audio, and power requirements vary substantially by module.
- **Verification:** Every implemented peripheral has a completed row in `HARDWARE-INVENTORY.md`.

## ADR 003: Target the physical Wrover board

- **Status:** superseded for the primary role by ADR 005 on 2026-10-29; retained for the camera node
- **Decision:** Treat the Freenove ESP32 Wrover board with ESP32 WROVER E module as the active hardware target.
- **Reason:** Physical photos and prior esptool detection confirm this board. The obsolete WROOM and generic starter packages were removed to prevent accidental configuration drift.
- **Verification:** Firmware configuration uses the Freenove Wrover PlatformIO board definition, and camera and SD functions are validated on this board.

## ADR 004: Isolate the camera and current display during validation

- **Status:** superseded after the previously recorded GPIO33/13 relocation; original decision retained as history
- **Decision:** Keep the currently wired I2C LCD on GPIO 21 and GPIO 22 only for temporary display validation. Do not initialize the camera in the same firmware.
- **Reason:** GPIO 21 and GPIO 22 are reserved by the Wrover camera map. Sharing them would create a bus and timing conflict.
- **Verification:** The display responds at I2C address `0x27`; future combined camera and display firmware may proceed only after the display moves to a verified non camera interface.

## ADR 005: Make the Waveshare 1.75 the primary assistant

- **Status:** accepted, 2026-10-29
- **Evidence:** owner selected ASIN B0F7XTJ1ZL and confirmed the new board is connected, has no case, and includes the supplied but unattached speaker. USB esptool reports ESP32-S3 rev0.2, 16 MB flash, embedded 8 MB PSRAM. Running factory firmware names ESP32-S3-Touch-AMOLED-1.75 and reports CO5300/CST9217 initialization.
- **Decision:** use the non-C Waveshare as the primary screen/voice device; retain Freenove firmware and earlier evidence for an optional camera node. Use the supplied Waveshare speaker at the inventoried SPK connector, with power disconnected for attachment. Battery fitment remains unknown.
- **Reason:** integrated touch, microphone, audio and power hardware removes the unresolved external LCD/audio work from the immediate critical path. A custom 3D-printed enclosure is a later owner goal.
- **Verification:** identity/flash probe and factory boot observed; custom baseline and visual/audio tests recorded separately in PROJECT-STATUS.md. No claim of working custom audio from a build alone.

## ADR 006: Separate Muse connectivity from local inference

- **Status:** accepted, 2026-10-29
- **Evidence:** pinned Muse ESP32 README, board helper and overlay; SDK pairs via phone, connects to remote infrastructure and supplies no local Muse weights. ESP-SR documents offline command recognition on S3.
- **Decision:** evaluate Muse with the non-C `s3n` / `sdkconfig.muse-waveshare-s3-175` profile and ESP-IDF 6.0.1 after bring-up; explore offline commands separately. Rich local chat may run on a separate host. Preserve authenticated backend direction for OpenRouter.
- **Verification:** sources pinned to `4737636133c9a0253d0b778333605b16fd2626c1`; future build must show the correct overlay/flash size. No Muse inference or pairing has been verified here.

## ADR 007: Resolve non-C audio clock source conflict

- **Status:** accepted, 2026-10-29
- **Evidence:** legacy manufacturer Arduino header declares MCLK16 and MCLK42; maintained BSP and Muse non-C implementation use MCLK42. The manufacturer's hardware reference identifies GPIO16 as expansion.
- **Decision:** reserve GPIO42 for audio MCLK and GPIO16 for potential expansion. Use maintained BSP handling of codecs, shared clocks and amplifier power.
- **Verification:** inspect pinned `waveshare-maintained-bsp.h.txt` (`BSP_I2S_MCLK=GPIO_NUM_42`) and Muse driver; future audio loopback/capture still required on hardware.

## ADR 008: Establish a reversible USB/memory baseline first

- **Status:** accepted, 2026-10-29
- **Evidence:** existing Freenove firmware build reproduced before changes; new Waveshare's running factory boot observed before custom upload.
- **Decision:** keep a separate minimal diagnostic, privately back up factory flash before replacement, and record compile results separately from physical observations. No network, SD, battery or codec initialization in the first diagnostic.
- **Verification:** build `pio run -d firmware/waveshare-bringup`; require actual `BASELINE=PASS` and continuing heartbeats. Full private flash backup must have expected size and a recorded SHA-256. Current results in PROJECT-STATUS.md.

## ADR 009: Inspect the new card before selecting a filesystem

- **Status:** accepted, 2026-10-29
- **Evidence:** owner now reports 128 GB; older documentation's 256 GB claim was not backed by a physical test. Manufacturer factory media requires FAT/FAT32; exact new card/firmware support unknown.
- **Decision:** replace the unverified 256 GB plan with the reported 128 GB card and a metadata-first validation plan. Never enable format-on-mount-failure. Storage does not expand inference RAM.
- **Verification:** read raw size/filesystem before writes, then an authorized fresh-file write/read/hash test; full-capacity integrity requires a separate empty/backed-up-card test.

## ADR 010: Measure physical PSRAM separately from usable heap

- **Status:** accepted, 2026-10-29
- **Evidence:** first live diagnostic reported `ESP.getPsramSize()=8386295` while the chip/factory identified 8 MiB and the 64 KiB buffer check passed. Installed Arduino 2.0.17 `Esp.cpp` shows this API sums heap free+allocated bytes; it is not physical capacity. IDF4's S3 `esp_spiram_get_size()` reports the physical size.
- **Decision:** diagnostic version2 reports `PSRAM_PHYSICAL_BYTES` from `esp_spiram_get_size()` separately from `PSRAM_HEAP_BYTES` from Arduino. Compare physical size against 8,388,608 bytes. Add a durable capacity-vs-usable measurement rule to AGENTS.md.
- **Verification:** reproduce initial false failure, rebuild/upload version2, require physical size match plus actual volatile 64 KiB write/read PASS and continuing heartbeats. Record final values in PROJECT-STATUS.md. Source implementations retained with hashes.

## ADR 011: Build a separate custom face application with USB controls

- **Status:** accepted, 2026-10-29 follow-up
- **Evidence:** owner accepts remote Muse, wants other APIs, custom faces and a later PC manager; speaker/card are now physically connected by owner report. USB diagnostic PASS reproduced before firmware changes.
- **Decision:** preserve the diagnostic, add `firmware/assistant/` with separate state/renderer/control modules, and use a bounded versioned USB protocol plus reusable host client. Keep AI provider selection independent of faces. No network/audio/SD initialization in the face slice.
- **Verification:** build and upload succeeded; owner visually confirmed Classic face. USB changes for style/expression/brightness and malformed-line rejection/recovery passed. Parser tests use address/undefined-behavior sanitizers. Detailed results in PROJECT-STATUS.md.

## ADR 012: Pin graphics code compatible with the actual core and verify geometry

- **Status:** accepted, 2026-10-29 follow-up
- **Evidence:** GFX 1.6.4 needs Arduino3's peripheral-manager header and failed under the installed Arduino 2.0.17 core. GFX 1.5.9 supports this core, but its CO5300 constructor has an extra IPS boolean absent in1.6.4. Initial incorrect adaptation initialized a 6-row panel and the owner observed a white screen despite serial success.
- **Decision:** pin GFX 1.5.9 for this prototype, pass the explicit `false` IPS argument and verify width/height equal466 before reporting display ready. Render through one PSRAM canvas and aligned full-panel writes. Prefer a maintained newer framework/BSP when moving into Muse/audio, as a separate verified migration.
- **Verification:** source declaration checked, corrected build uploaded, owner confirmed visible face, and frame counters advanced0→52 over uptime1,065→6,254ms. A successful initialization call alone is not visual acceptance.

## ADR 013: Keep multi-provider AI code on the host

- **Status:** accepted foundation, 2026-10-29 follow-up
- **Decision:** host-side `TextProvider` returns a small normalized reply; mock and compatible chat adapters share that interface. OpenRouter endpoint is fixed; custom service URL is trusted host configuration, never a device-supplied URL. Do not expose a network service until authentication and usage controls exist.
- **Verification:** synthetic adapter tests cover request shape, invalid input, bounded output, error redaction, HTTPS/loopback policy and redirect rejection. No real API key or paid call used; live compatibility and speech integration remain unverified.

## ADR 014: Inspect inserted SD metadata without a filesystem

- **Status:** accepted, 2026-10-29 follow-up
- **Decision:** after display acceptance, add an explicit USB `card` command using 1-bit SDMMC at 400 kHz on the inventoried pins. Read CSD size and at most sector 0 plus one first-MBR-partition boot sector; never mount, enumerate, write or format. Deinitialize the host afterward.
- **Verification:** Face Lab 0.2.0 returned card_error=0,124,383,133,696 raw bytes and exfat_signature; frame count continued 1→22 after the operation. Controller-reported size is distinct from full-capacity validation. Tests and future format decisions remain in SD-CARD-PLAN.md.

## ADR 015: Independent application and optional local factory recovery

- **Status:** accepted, 2026-10-29 follow-up
- **Decision:** develop our own application modules using documented drivers and selected service SDKs. Do not modify or depend on the factory Brookesia application. Preserve its existing local backup only as optional recovery material; no automatic restore or build dependency references it. The owner questioned its need without requesting deletion.
- **Evidence:** current application sources, factory backup file verified at16,777,216 bytes with mode 0600, and owner direction to continue our own firmware.
- **Verification:** custom PlatformIO build/upload and hardware acceptance; backup path documented explicitly in FIRMWARE-TRUST.md. Hardware capabilities are distinct from enabled firmware functions.

## ADR 016: Empty-card formatting authorization

- **Status:** accepted, 2026-10-29 follow-up
- **Decision:** owner authorizes formatting/testing the new empty card when needed. Retain exact-device identification and filesystem choice before destructive operations; no repeat approval is needed within that scope. No formatting is needed for the existing raw-read slice.
- **Verification:** current exFAT signature and capacity remain unchanged until a separately documented filesystem/write slice. This supersedes any earlier statement that the owner has not authorized formatting.

## ADR 017: Add touch as a separate measured input slice

- **Status:** initialization and ordinary physical taps verified, 2026-10-29
- **Decision:** follow the exact manufacturer CST9217 example with SensorLib 0.3.1, one shared Wire bus, two-point storage and IRQ-driven reads. Valid taps cycle cosmetic face only, with press/release gating and 300 ms debounce; no recording/service action is triggered. Preserve raw coordinates until orientation is calibrated.
- **Verification:**0.2.0 baseline reproduced; 0.3.0 build/upload passed (20,660 static RAM / 380,697 app bytes). Runtime model/resolution checks pass. After the initial monitoring window, the owner confirms the face changes with each physical tap. Mark ordinary tap/release cycling complete; keep coordinate orientation, edge targets, holds and multitouch unverified. A later USB check after restart has a fresh zero counter and does not invalidate the owner observation.

## ADR 018: Verify speaker output with an explicit bounded diagnostic

- **Status:** software transfer, audible output and post-audio touch verified, 2026-10-29
- **Evidence:** manufacturer speaker specification and pinned maintained BSP establish 3.3 V active-high PA46, ES8311 and TX clock/data assignments. Existing0.3.0 baseline was reproduced; 0.4.0 builds/uploads and codec/DMA transfer/cleanup succeed.
- **Decision:** generate one fixed quiet440Hz/400ms tone in memory on explicit USB `tone`. Reuse Wire0, enable TX-only I2S temporarily, ramp amplitude, then command amplifier LOW, mute and release I2S on every exit. Vendor only the small attributed Apache-2.0 codec driver with documented compatibility/robustness edits. Do not initialize ES7210/RX, change charging settings or use SD media for this slice.
- **Retry policy:** physical sound is not an idempotent setter. The host must not automatically resend a tone after a lost reply; retry only reads/setters. A synthetic lost-reply test verifies this distinction.
- **Verification:** parser sanitizers, host retry test, pinned-source checks and actual `tone` result error0/stage complete/counter increment; advancing frames and ready touch afterward. Owner heard the requested replay. A subsequent real tap changed Classic→Pixel, counter 0→1, with continuing frames and no reboot. Results are recorded in PROJECT-STATUS.md.

## ADR 019: Measure microphone levels before speech streaming

- **Status:** codec/capture/cleanup verified in 0.5.0; sound response accepted in 0.6.0, 2026-10-29
- **Evidence:** exact Waveshare non-C BSP identifies four serialized slots MIC1/reference/MIC2/unused. Espressif's pinned standalone ES7210 driver supports IDF4 and the16kHz/256× coefficient; codec-dev source supplies3.3V/2.87V bias context and shutdown sequence.0.4.0 baseline reproduced before change.
- **Decision:** explicit `mic` takes a two-second RX-only level measurement with a red onscreen indicator. Return only aggregate RMS/peak/clipped counts, never raw audio; clear the application sample block and release DMA/codec resources. Run the attributed ADC shutdown sequence on every exit, with PA46 LOW and no network/SD files. Do not automatically retry a lost microphone-test reply. Bounded blocking diagnostics do not replace future press-to-talk/cancel/duplex design.
- **Verification:**0.5.0 builds/uploads (20,764 RAM / 409,953 app bytes), parser sanitizers and no-retry host checks pass; 40 retained references match hashes. Actual32,000-frame room sample returns error0/stage complete, RMS `[11,3,9,1]`, peaks `[59,34,75,17]`, no clipping, elapsed 2.317seconds. Frames continue after cleanup. Second timing window was missed by the owner and is not evidence of speech rejection. Later0.6.0 owner-triggered comparison verifies speech response; results are in PROJECT-STATUS.md.

## ADR 020: Correct analog enable and let the owner start a mic test

- **Status:** arm/cancel, tap trigger, indicator, expiry and acoustic response verified, 2026-10-29
- **Evidence:**0.5.0 returned valid DMA/noise-floor numbers, but speech response was unverified because the owner repeatedly missed fixed timing windows. Retained maintained codec-dev analog/global/pair power values differ from standalone esp-bsp initialization; see inventory. This difference is a source-based hypothesis, not an isolated-bit fault finding. Owner subsequently confirmed missing the prior windows; do not claim the standalone driver caused a demonstrated speech failure.
- **Decision:** align those four codec power values with the maintained driver. Keep clock, bias, gain and TDM unchanged. Add `mic-arm`/`mic-cancel`, a visible MIC TEST READY/TAP THEN SPEAK state, 60-second arming expiry and a four-second measurement. Only the next valid tap after explicit arming starts capture; normal taps continue changing faces. Disarm before capturing and clear the indicator after ADC/RX cleanup. Direct `mic` remains available for diagnostics, with no automatic retry.
- **Verification:**0.6.0 parser sanitizer/build PASS (20,772 RAM / 410,209 application bytes); hardware arm/cancel, one-tap disarm, owner-visible indicator,64,000-frame voice response and sequential mic→speaker recovery pass. Unused arming expired at 60.19 seconds without capture, with continuing frames and no reboot.0.5.1 power-only code built but was not flashed separately; no result isolates the four changes individually.

## ADR021: Gemini through the laptop is the first live provider

- Status: accepted and live-verified, 2026-10-30.
- Initial owner preference was no phone enrollment and Google Gemini's free tier. ADR023 records the later decision to evaluate Muse for voice. Separate project-account signup on PC is possible, while documented gadget enrollment uses the phone app. Same personal phone account was not a verified binding rule.
- Keep an independent firmware, host-held provider keys and a provider-neutral boundary. Implement native generateContent plus optional mock/OpenRouter/compatible adapters. Record Google Free-tier status as owner attestation; do not infer billing from the key or enable billing. No automatic fallback/retry.
- Verify actual Gemini 3.1 Flash-Lite text through the local authenticated browser service, then deliver a bounded preview over USB. The owner confirms the greeting on the round screen. Voice is a later slice.

## ADR022: Explicit host trust/limits and a restricted USB caption

- Status: implemented and tested, 2026-10-30.
- Portable Python had no CA bundle; use pinned certifi with certificate/hostname verification. Keep dependency need/provenance explicit. Separate manager/device bearer scopes, reject unexpected Host/Origin, bound bodies/workers/upstream I/O and reserve persistent UTC attempts before inference. Failed attempts count. Provider keys are local mode 0600 files, not device/vault data.
- A browser test exposed a local unlock credential; revoke/rotate it, handle both initial/hash-change fragments and remove the fragment before inspection. No Gemini key was exposed. Production LAN/TLS and stronger OS secret storage remain separate work.
- Extend the bounded USB frame to256 bytes for an ASCII hex caption, max96 decoded bytes, fixed source labels and 60-second expiry. Never execute response text or return it in status. An unplugged/unsupported device preserves the model reply without regeneration. Original0.6.0 binaries remain private recovery artifacts.
- Verification:26 backend tests, two USB-client tests, parser sanitizers,0.7.0 build/upload, real Gemini/browser/USB response and owner screen confirmation. Expiry passed at 60.54 seconds with continuing frames and no restart. An anonymous nonce/HMAC proof lets the launcher verify an existing local manager before reopening it; no second service or unlock credential is sent to an unrelated listener.


## ADR023: Voice first, with an isolated Muse evaluation

- Status: build/flash/token provisioning verified, 2026-10-30; phone enrollment/audio conversation pending.
- Owner selected Muse again, provided a local replacement token and clarified that speaking/hearing is the main goal. Continue Mac USB power now; eventual operation away from the PC is the target. Screen captions support the experience.
- Keep Face Lab/Gemini source and compiled 0.7.0 recovery files. Evaluate Muse as a separate pinned ESP-IDF 6 application, using the exact non-C profile. Ordinary Muse voice notes return captions; enable experimental live voice for audible replies, 30-second idle/180-second total limits. Use onboard BOOT before adding wiring. A custom wake phrase is a separate model/benchmark milestone.
- The token pasted in chat was treated as exposed. Owner confirms replacement; the saved replacement passes format checks and is normalized into the ignored mode-0600 .env assignment. Never copy values or prefixes into notes. Build without SDK/Wi-Fi credentials, then provision once over serial, after exact board identity; suppress all raw echoes. NVS remains plaintext. Disable OTA, LAN tunnel, remote BLE commands, Secure Boot, flash encryption, manufacturer eFuse auth and NVS encryption.
- Verification: pinned IDF6.0.1 tools installed in ignored external/. Image 2,166,784 bytes fits 4 MiB; config guard passes; flash hashes verified. Exact non-C status and chat capability respond; observed startup has no panic/NVS-recovery message. Token ACK succeeds. Six synthetic helper tests cover private parsing, wrong-board refusal, echo suppression/single-send and flash guards. Source/host tests and physical pairing results are recorded in PROJECT-STATUS.md.
- The retained kit explicitly lists a 2× AA holder. No compatible converter/chemistry/polarity is established; BAT is a rechargeable 3.7 V lithium interface. Do not connect AA/9 V cables directly. Future power plan separates regulated USB power, verified 1S battery and a converter route; no battery connected or runtime promised.

## ADR024: Update Gemini text model support and separate Live audio

- Status: accepted, live text check verified, 2026-10-30.
- Official Google catalog/pricing lists newer models. Add low-thinking requests for 3.8/3.6 Flash, retain minimal for 3.5/3.1 Flash-Lite, suggest these text models in the local form, and reject known Live models on the text adapter before network access.
- One bounded Gemini 3.8 Flash greeting succeeds with the existing private host key and existing owner-confirmed Free project; only after success save 3.8 Flash as the text model. The gateway still counts attempts, never enables billing and makes no silent model fallback. 3.8 Live is a future speech route, not implemented by changing a text model name. Google project quotas and pricing still apply.
- Verification: 28 backend tests pass, including model-specific request shape and Live rejection. The successful 3.8 check is host-only, without a second ESP32 caption claim. A stale browser connection recovered after resetting the client; the refreshed UI visibly selects 3.8 Flash with an empty key field and disconnected USB manager. Screenshot retained.


## ADR025: USB status checks preserve runtime state

- Status: implemented and physically verified for Muse, 2026-10-30.
- The first helpers deasserted DTR/RTS on open; native USB checks repeatedly reported uptime1 second and Wi-Fi reconnecting. Match the pinned SDK console's asserted DTR/RTS and clear POSIX HUPCL so close does not toggle a reset condition.
- Separate connections now show Wi-Fi connected and uptime82→85 seconds, reset reason usb from the earlier deliberate reset; no reset occurred between those observations. Shared handling is used by Muse and Face Lab clients; Face Lab firmware itself is not changed/reflashed by this host fix.
- Six helper tests include preserving other termios flags and redacting private status fields; two original client tests retain bounded validation/no-retry behavior. Update AGENTS rule12 and the architecture/guide so future debugging distinguishes host-induced resets from firmware failure.

## ADR026: Separate advertising state, reception and account enrollment

- Status: accepted diagnostic approach, 2026-10-31; phone discovery/enrollment still pending.
- Evidence: owner reports intermittent Android discovery even after a Muse force-stop; Nearby Devices is allowed. A read-only built-in JTAG capture finds advertising enabled/active, BLE synced, quiet mode off and no connected client. The board is resumed and debugger closed. These flags do not establish over-the-air reception or Muse app compatibility.
- Decision: preserve firmware/credentials and avoid assigning a radio/app cause without independent evidence. An independent Nordic Android scan was proposed; owner declines installing it, so it is deferred. Owner reports Android 17 and authorizes one final Muse attempt, then Google AI if unsuccessful. Add one bounded redacted USB monitor rather than retaining raw UART logs or simulating physical confirmation.
- Verification: nine helper tests cover bounded parsing, exact board checks, label allowlists, credential redaction, distinct standalone/Link credentials and read-only watch behavior. A 10-second physical watch completes with Wi-Fi connected and paired=false. Phone Link success, audible reply and retry reliability remain unchecked.

## ADR027: Use Gemini voice after the final Muse discovery failure

- Status: implemented, physical spoken round trip accepted by owner, 2026-10-31.
- Owner declines a diagnostic phone app. One final normal board restart/phone Bluetooth toggle still leaves the gadget undiscovered. Stop Muse enrollment work and use the existing privately configured Google API connection. Android 17 is owner-reported; do not assign an app/radio cause without evidence.
- Restore our independent application as Face Lab 0.8.0. Before installing its different flash layout, erase retired Muse flash/NVS credentials; keep the ignored host SDK-token file and token-free pinned evaluation sources for optional future work. No SD operation is involved. Existing 0.7.0/factory recovery files remain private.
- First voice slice: physical tap after explicit host arming records eight seconds on MIC1, transfers bounded PCM with offsets/CRC over native USB, sends one stateless Gemini 3.8 Live request through the Mac, and plays at most twenty seconds of 24 kHz PCM. Recording/playback are cancellable by a second physical screen tap. No background capture, SD recording, action execution or automatic API retry. The host holds the API key and applies the existing persistent attempt limits; Google Free status remains owner attestation.
- Verified before flash: existing Muse exact-board/Wi-Fi status responds with paired=false; initial 0.8 build passes. Backend suite now passes 34 tests; command/audio parser sanitizer checks and two USB-client tests pass. Subsequent physical observations and final build size belong in PROJECT-STATUS.md. Voice-mode arming is bounded to 60 seconds; mode lasts at most ten minutes/ten replies, and network generation is bounded to 45 seconds. USB loss/timeouts release device buffers and leave its amplifier off.
- Final verification: 37 backend tests pass. First generated greeting is heard but choppy; a source-based display/TX scheduling adjustment is built/uploaded, then owner confirms a clear answer to physical speech. USB verifies a completed turn, 128,000 capture frames, clean audio/mic status and advancing frames after Stop. Host cancellation of a later generation does not retry. Watchdogs are evaluated between bounded operations; extended idle/reconnect/physical-cancel reliability remains explicit future acceptance. See PROJECT-STATUS.md.

## ADR028 · Run the wake phrase on the Mac and finish speech on a pause

- Implemented and uploaded 2026-11-06. Keep the Waveshare microphone, face and speaker. Run the pinned Sherpa Zipformer detector on the Mac during explicit wake mode. Allow tap or a debounced IO16-to-GND switch as other triggers. Stop capture on roughly 640 ms of quiet, with an eight-second limit.
- Use Gemini 3.8 Live and Charon for single-turn audio. Use the generation-complete event and send validated binary audio to the speaker. Finish with verified buffer playback and rearm wake after playback. Idle wake audio stays local and buffered audio is held in RAM. The USB gateway remains necessary.
- A separate USB process was refused with exclusive ownership. A missing trigger ACK occurred while the board had already entered recording, so use the next PCM phase to confirm it. For uploads and playback, query accepted state after a missing ACK without resending the operation. See AGENTS rule 12 and the protocol reference.
- Verify with the build, 41 backend tests, two USB client tests, parser sanitizers and a hardware wake-only reply. A subsequent reply timed out before the host readback change. Repeat reliability and the physical switch remain acceptance items. [Project status](PROJECT-STATUS.md) · [Wiring](BREADBOARD-CAMERA-DISPLAYS.md)

## ADR029 · Refine the interface around actual device states

- Decision: 2026-11-06. Retain the three expressive Face Lab styles while simplifying Control Room and distinguishing idle, armed, local wake, command capture, thinking, reply transfer, speaking and recovery. Keep the existing local HTML/CSS/JavaScript application and host-held credentials. No frontend framework or new runtime dependency is needed.
- The round display shows microphone state explicitly. Listening/speaking bars are status symbols, not measured audio levels. Preserve the established suspension of full-frame display writes during streamed capture/playback; only safe existing render periods animate. An error/cancel state points to Control Room because transport does not distinguish every cause.
- Use annotated retained product/board images plus code-generated breadboard drawings, editable Canvas and Excalidraw in the vault. The round Waveshare is already a complete screen/ESP32 device; the Freenove keeps its camera ribbon. H2 references disagree about ordering, so match actual IO16/GND labels rather than counting socket contacts. Breadboard coordinates remain a continuity-checked example until the physical switch is accepted.
- Verification: reproduce 0.9.2 baseline, build 0.9.3, check the actual renderer on the host with sanitizers/circular text bounds, exercise browser states using isolated fixtures, independently audit the integrated changes, and record post-upload evidence in [Project Status](PROJECT-STATUS.md). Reference photo hashes remain unchanged. [Device UI](DEVICE-INTERFACE.md) · [Wiring guide](BREADBOARD-CAMERA-DISPLAYS.md)

## ADR030 · Add appearance preferences and prepare gated power/status-LED work

- Decision: 2026-11-06. The owner requested dark mode and clarified that the Codex screenshots are a reference for colors, typography, spacing and controls; a sidebar is optional. Preserve the existing three functional sections and explicit voice controls. Offer System, Light and Dark; persist only an allowlisted appearance choice, never manager access or provider credentials.
- The owner confirms the existing two-AA holder and two AA cells. Their chemistry, loaded voltage and polarity remain unverified; no suitable regulator has been identified. Show a conditional regulated-power route in the vault. Do not connect the AA holder to the Waveshare lithium charging socket, 3V3 or GPIO. Power conversion and removal of the current USB audio-data link are separate work.
- Reserve GPIO17/18 only conditionally for green command-capture/red reply-playback LEDs, after inventory evidence and with outputs disabled in the ordinary build. Optional GPS can share these pins. Require unit identification, actual LED/resistor checks and a verified circuit before enabling. The green light means command capture after a trigger, not ambient wake monitoring or measured speech; red means reply playback. Existing press/release-to-start and cancel semantics remain unchanged.
- Verification: sixteen web regressions and desktop/390 × 844 browser checks pass, including Dark persistence with auth lock after reload and shared Stop. The 0.9.4 default build and default-off/fake-GPIO LED sanitizer checks pass; no LED firmware was uploaded. Drawings separate conditional branch placement from the current occupied Freenove breadboard. Actual results and remaining physical checks are in [Project Status](PROJECT-STATUS.md).


## ADR031 · Make the Control Room a terminal workspace

- Decision: 2026-11-13. Use the owner's terminal references for color and typography, with an original MR. Robot mascot. Move text chat into the main terminal; keep voice controls shared across tabs and pin Stop in the status strip while voice is active. Default to Dark for new sessions and keep existing appearance preferences. The owner chose blue accents for the controls and mascot.
- Scope: browser UI only. The launcher, credential storage, host API, USB ownership and firmware are unchanged.
- Verification: `node --test manager/tests/app.test.cjs` passes; Chromium checks on the local server used synthetic API responses to verify layout at 320–1440 px, keyboard input, themes and shared Stop. See [Control Room interface](CONTROL-ROOM-DESIGN.md).

## ADR032 · Isolate the talk button and move voice to the LAN in stages

- Decision (2026-11-13). Put the owner-selected green switch between Waveshare H2 IO16 and GND on isolated strips. Keep the photographed Freenove and AA-fed rails separate. Use regulated USB-C for AA power and Wi-Fi for the future Mac voice link.
- Evidence and acceptance are in the [wiring guide](BATTERY-WIFI-WIRING.md). Check open/closed/open continuity, a physical button turn and cancel over USB, an authenticated button event over the LAN, then one battery-powered spoken turn with USB data removed. The physical and network checks are pending.

## ADR033 · Carry voice context across hands-free follow-ups

- Decision (2026-11-13). Keep one authenticated Gemini Live connection per armed conversation once the first question is captured. After playback, listen locally for speech within a 15-second window. A weak follow-up is discarded locally without consuming a request or extending the window. The existing button or screen tap can stop follow-up listening, as can Control Room.
- Face Lab defaults to a blue pixel robot with phase and reply expressions. Only a fixed reaction value crosses USB. The host uses output transcription briefly in memory and retains no local transcript. Full-screen updates stay suspended during active recording and playback.
- Verification is recorded in [Project Status](PROJECT-STATUS.md). The provider event sequence follows the [Gemini Live API reference](https://ai.google.dev/api/live).

## ADR034 · Arm Gemini voice on the Mac and add a local provider

- Decision (2026-11-13). The manager owns automatic USB and wake arming, so opening or closing a browser tab does not control the microphone. Pause suspends automatic voice for the current process and releases USB for diagnostics, text and provider changes. A quiet follow-up timeout returns to local wake listening.
- Ollama starts with local text and display captions. Keep the Gemini profile private when switching providers. Muse appears as pending until a paired service can be verified. The three existing face styles share pixel art, and each offers eight expressions.
- Verification: owner confirmed both triggers. Hardware state and provider round-trip results are recorded in [Project Status](PROJECT-STATUS.md) and [Voice and text providers](VOICE-PROVIDERS.md).

## ADR035 · Check Android Location before troubleshooting Muse discovery

- Evidence (2026-11-13). Muse on the owner's Android 17 phone failed to list the gadget with Bluetooth and Developer mode on. The Mac independently detected the advertisement and discovered the pairing service. After the owner enabled system Location, Muse found and paired with the ESP32.
- Decision. Check system Location first when this phone misses the board during setup. Include this step in the pairing guide.
- Verification. The owner reported pairing success and `tools/muse.py status --port PORT` confirmed Wi-Fi connected, `paired=true`, link **Online**, and voice **Connected**. The standalone device credential flag stayed false. [Muse pairing guide](MUSE-PAIRING.md)

## ADR036 · Use IO16 for Muse talk and keep BOOT for pairing

- The non-C Waveshare patch uses the existing active-low green switch and SDK debounce for conversation. BOOT handles physical pairing confirmation. The board uses the documented Muse live-call identity.
- A paired baseline was checked before writing only the application. The rebuilt image and flash hash passed, Wi-Fi and pairing survived, and USB recorded green-button edges and a held voice-note caption. Live-call requests returned `backend_unavailable` with zero queued audio even though the phone app could speak on the same account. [Muse pairing and voice results](MUSE-PAIRING.md)

## ADR037 · Switch between resident Muse and Face Lab apps

- Decision (2026-11-14). Retain the Muse bootloader and app in OTA slot 0. Put Face Lab in OTA slot 1, use its private NVS at 0x9000, and share the OTA selection data. Use the pinned SDK development key to sign the second image because the existing Muse config verifies signatures on app selection.
- Verification. Both builds passed. USB switched both directions, Muse pairing survived, actual Muse and Ollama replies completed, and Gemini's saved key remained configured. One physical green-button Muse call produced an audible reply. The earlier server error could no longer be reproduced and its cause is unknown. [Provider switching](VOICE-PROVIDERS.md)

## ADR038 · Preserve Gemini arming and route local media by model

- Preserve the Free-tier confirmation with its corresponding saved key. Show the local arming blocker in Control Room. The owner authorized 500 local attempts per UTC day and confirmed both Gemini triggers worked again.
- Use the OpenAI-compatible reasoning option for Ollama audio and allow about one second between phrases. Gemma 4 12B answered a synthetic two-sentence Proxima Centauri question. For Qwen and Z-Image, Gemma transcribes the ESP32 speech locally and the selected model consumes the text.
- Ollama 0.40.16 returned HTTP 400 for the installed Z-Image model. A separate loopback Ollama 0.32.5 runtime generated a 512 × 512 PNG using the existing weights. The owner verified the spoken-prompt result in Conversation. Test requests and images remain local. [Ollama guide](OLLAMA-DEVICE.md)

## 2026-11-14 — Local conversation and board previews

Control Room stores browser history in IndexedDB, including the full generated PNG. The change reuses loopback HTTP, the existing launcher and its in-memory authorization. The board receives a fixed-size RGB565 preview over its exclusively owned native USB connection. The main browser controls retain the CSS pixel fallback, and the 3D view uses a pinned local Three.js build. No GPIO assignments change. The verified scope and remaining physical checks are in [the system audit](SYSTEM-AUDIT-2026-11-14.md).
