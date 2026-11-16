# Project Status

Latest update 2026-11-14, America/Los_Angeles. Dated follow-ups preserve earlier verification.

## Current firmware — Muse and Face Lab

Both firmware images are installed on the Waveshare. Control Room's **Providers → Save & apply** switches the boot mode over USB. Tests switched between Muse and Face Lab, retained Muse pairing, restored the Gemini key profile, and received real text replies from Muse and Ollama. Face Lab acknowledged Ollama's display caption. The owner confirmed that a quick green-button tap started a Muse live call and the ESP32 spoke its reply. The cause of the earlier backend error remains unknown. [Provider switching](VOICE-PROVIDERS.md) · [Muse pairing and voice results](MUSE-PAIRING.md)

Face Lab 0.9.8 recovery images are saved. This Control Room firmware has larger Ollama captions and local button capture for Gemma 4 12B. With Gemini selected, Control Room arms automatically over USB. The owner verified both the IO16 green button and the wake phrase. [Voice guide](GEMINI-VOICE.md) · [Wiring guide](BREADBOARD-CAMERA-DISPLAYS.md) · [Device UI](DEVICE-INTERFACE.md)

On November 14, Gemini had exhausted the 20-attempt local cap and lost its saved Free-tier confirmation during provider switching. The owner authorized a cap of 500, the confirmation was restored from its saved profile, and the owner reverified both triggers. Gemma 4 12B answered the two-sentence Proxima Centauri recording using the corrected OpenAI-compatible reasoning option in about 11 seconds. Qwen 3.6 answered the typed question. The owner saw the generated PNG after requesting an image through the ESP32's microphone. [Ollama model and runtime guide](OLLAMA-DEVICE.md)

On October 31 the owner confirmed a clear spoken reply on Face Lab 0.8.0. The older firmware used a fixed eight-second recording. The November bench tests below distinguish local wake detection, generated reply playback and physical accessory acceptance.

## Direction confirmed by the owner

- Use the new Waveshare round-screen board as the primary assistant, replacing the Freenove in that role.
- Owner confirms no fitted enclosure; a custom 3D-printed case is a future goal.
- Owner confirms the supplied speaker is connected, the card is inserted and USB reconnected. Audio software transfer/cleanup passes; owner confirms the replayed beep is audible. Battery fitment is unknown. Owner accepts remote Muse and wants other APIs plus a later PC face/device manager.
- Reported 128 GB card now identifies as 124,383,133,696 raw bytes (124.38 decimal GB / 115.84 GiB), with an exFAT boot signature. Brand/model and full-capacity integrity remain unverified.

## Observed before changing firmware

1. `pio run -d firmware` succeeded for the existing Freenove camera application: 56,028 bytes static RAM and 853,357 bytes application flash. Earlier camera/SD physical observations remain historical, not retested on the disconnected Freenove today.
2. `python3 tools/run_host_tests.py` passed all four existing C++ helper tests.
3. Initial `pio device list` found no ESP32. After the owner connected the new board, one native Espressif USB Serial/JTAG port appeared.
4. esptool4.11 `flash_id` reported ESP32-S3 rev0.2, embedded 8 MB PSRAM, 40 MHz crystal, **16 MB detected flash**, quad flash, 3.3 V flash. This operation read configuration; no eFuses were changed.
5. The running factory serial log identifies **ESP32-S3-Touch-AMOLED-1.75**, project `esp32-s3-touch-amoled-brookesia`, app `v1.0.1-9-gec7380d`, ESP-IDF5.5.4. It found 8 MB octal PSRAM at 80 MHz and reported `SPI SRAM memory test OK`.
6. Factory log reported successful CO5300 panel creation and CST9217 detection at 466 × 466. Visual display/touch behavior and actual audio have not been independently observed by the agent. A generic I2C pull-up warning was logged; touch initialization proceeded. Revisit if actual bus/peripheral failures appear; do not add pull-ups by guesswork.

The USB chip identity alone does not identify a board model; here it is corroborated by the running board-specific factory firmware and the owner's supplied listing.

## Implementation and verification

| Work | Actual result |
| --- | --- |
| Isolated Waveshare USB/PSRAM diagnostic | Version2 build **PASS**. Platform 7.0.1 / Arduino 2.0.17; no application library dependencies. Static RAM 18,860 bytes; application 266,529 bytes. |
| Factory preservation | **COMPLETE**: full 16,777,216-byte read saved under ignored `private/backups/`, file size checked, SHA-256 recorded in a mode 0600 private sidecar. No backup copied into vault. |
| Custom diagnostic on physical board | **PASS**: version2 uploaded with all write hashes verified. Actual serial reports 16,777,216 flash bytes, 8,388,608 physical PSRAM bytes, 8,386,295 usable PSRAM heap bytes, 65,536-byte buffer PASS, `BASELINE=PASS`, and heartbeats at 5,003/10,003 ms. |
| Reference preservation | Eight Amazon gallery images, two supplied PNGs, manufacturer schematic and pinned source snapshots saved. SHA-256 verification utility supplied. |
| Visual guides | USB diagram, annotated SPK/BAT reference, four proposed screen states; editable Excalidraw setup and architecture Canvas. Rendered PNGs inspected for layout and correct callout positions. |
| Documentation/vault | Primary-target change, local-vs-remote inference distinction, SD plan, roadmap, source provenance and final hardware acceptance reconciled in project and Obsidian hub. |

## Next acceptance steps

The first physical spoken round trip is accepted and local wake detection is implemented. Extend physical cancel, unused arming expiry, reconnect and repeated-turn reliability checks; measure latency and improve the interaction. External Control Room provides voice start/stop. Muse enrollment is deferred after the final failure. The physical talk switch, camera integration, independent Wi-Fi gateway, SD filesystem, battery and enclosure remain separate slices.

## Follow-up acceptance: face, USB, card and provider foundation

- Reconnected board reproduced version2 memory/buffer PASS before changes.
- Latest Face Lab 0.2.0 build/upload PASS: 19,660 static RAM bytes, 352,001 application flash bytes; pinned GFX 1.5.9 / Arduino 2.0.17.
- Initial display adaptation failed visually (owner reported white blank). GFX 1.5.9 has an extra IPS boolean; omitting it shifted height to 6 rows. Explicit argument and geometry guard fixed it. Owner then replied: **“Yes, the face looks correct.”**
- USB hardware tests passed all three face IDs, expression changes and brightness 80→96. Brightness 161 and a 500-byte oversized line were rejected without state mutation; valid commands recovered. RX buffer is 1024 bytes; parsed frames remain capped at 96. Parser ASan/UBSan checks passed.
- Before card work, frames advanced 0→52 over uptime 1,065→6,254 ms. Classic's appearance is owner-confirmed; other styles have command/state/render-path acceptance, not a separate owner review of every expression.
- Version 0.2.0 raw card query returned `card_error=0`, 124,383,133,696 bytes and `exfat_signature`. Controller metadata and at most two boot-related sectors were read. No filesystem mount, file listing, write, format or full-capacity test occurred. Frames advanced 1→22 afterward without restart.
- Backend adapter foundation: 8 unittest methods PASS using synthetic, in-memory upstream responses. Mock, OpenRouter and configured compatible text services share one interface. No real key, provider call, cost or device AI connection was used. This is not yet an authenticated running backend.
- Factory trust is documented in FIRMWARE-TRUST.md. The original demo was not audited or certified secure; the board now runs our restricted compiled application.

## Learning captured during this slice

Version1 incorrectly compared Arduino's usable PSRAM heap (`8,386,295` bytes) to physical capacity. Its buffer passed but the overall comparison falsely failed. Source inspection reproduced the cause: Arduino 2.0.17 `ESP.getPsramSize()` sums heap free+allocated bytes. Version2 uses IDF4 `esp_spiram_get_size()` for physical capacity and reports heap separately. The corrected build was uploaded and the physical test above passed. ADR010 and AGENTS rule11 preserve this finding; no hardware fault was inferred from heap overhead.

Actual accepted serial excerpt (curated, no device identifiers or credentials):

```text
MR_ROBOT_WAVESHARE_BASELINE version=2
FLASH_BYTES=16777216 expected=16777216
PSRAM_PHYSICAL_BYTES=8388608 expected=8388608
PSRAM_HEAP_BYTES=8386295
PSRAM_BUFFER_CHECK=PASS bytes=65536
BASELINE=PASS
HEARTBEAT baseline=PASS uptime_ms=5003 free_heap=371108 free_psram=8386295
HEARTBEAT baseline=PASS uptime_ms=10003 free_heap=371108 free_psram=8386295
```

Acceptance command: `pio run -d firmware/waveshare-bringup -t upload --upload-port PORT`, followed by a 115200-baud serial read, lowercase `i` to repeat the report, and observation of two continuing PASS heartbeats. The current session's actual port was identified by enumeration; do not assume its name in a future session. Detailed silicon rev0.2 came from esptool; `sdk_revision=0` is the older SDK field.

At the end of the initial diagnostic slice, these were pending: touch coordinate/hold/multitouch validation, duplex/AEC audio and speech handling, SD filesystem/write/integrity tests, offline commands, Muse build/pairing, authenticated AI service, graphical PC manager, camera network link, power/battery work and enclosure CAD. The October 30 milestone below completes the host service, initial PC manager and Gemini text path. No real tokens, Wi-Fi credentials, recordings or personal SD files were added to documentation.

## Research and storage

See [sources](SOURCE-REFERENCES.md), [hardware inventory](HARDWARE-INVENTORY.md), [decisions](DECISIONS.md), [architecture](ARCHITECTURE.md), [roadmap](ROADMAP.md), [Muse evaluation](MUSE-EVALUATION.md), [first connection](FIRST-CONNECTION.md) and [SD plan](SD-CARD-PLAN.md).

The project folder was not a Git repository during this session; no commit or remote push was made. Ignore rules are prepared for private backups, secrets, logs, raw captures and build artifacts.

## Follow-up: roadmap, ownership, SD authorization and touch

Owner confirmed independent application development, authorized formatting the new empty card when needed, and deferred Muse account creation. Backup path was rechecked: `private/backups/waveshare-factory-2026-10-29.bin`,16,777,216 bytes, local mode 0600 with adjacent checksum sidecar. It is unused recovery data, not application source or a cloud upload.

Version 0.2.0 display/USB baseline was reproduced before changes. Version 0.3.0 built and uploaded successfully: 20,660 static RAM bytes and 380,697 application flash bytes. SensorLib 0.3.1 initializes actual CST9217 at 466×466 via SDA15/SCL14, RESET40/INT11. Runtime status reports display_ready=true and touch_ready=true. The owner subsequently confirmed: “Yes, the face changes with each tap.” This verifies ordinary tap/release face cycling. Coordinate orientation, edge targets, long holds and multitouch remain unverified. A subsequent USB baseline check reported display/touch ready and advancing frames; uptime was about2 seconds and the volatile touch counter was0 after restart, so it does not preserve the earlier taps.

The roadmap now uses explicit `[X]` completed / `[ ]` pending items. Muse's official-site chain and SDK-token requirement were investigated. Using one Muse project account across phone/site was setup guidance, not a verified technical account-binding rule; the October 30 clarification below supersedes that advice. No account login/token/terms action occurred. SDK integration still requires an explicit framework/client boundary; current application is independent of the factory demo.

## Follow-up: output-only speaker test (0.4.0)

Before changing firmware, 0.3.0 again reported display/touch ready and advancing frames. The owner's tap confirmation verifies ordinary tap/release face cycling; coordinate, hold and multitouch checks remain pending.

Manufacturer evidence was recorded before coding: supplied speaker specification 8 Ω / 2 W, NS4150B supply 3.3 V and PA46 active-high, codec 0x18 on the existing Wire bus, TX pins 42/9/45/8. The application vendors only the small Apache-2.0 ES8311 driver with documented Arduino 2 compatibility and allocation/short-read guards. No factory-demo code or music sample is used. No PMIC charging/power configuration was changed.

- 0.4.0 build and upload **PASS**, with all upload hashes verified: 20,700 static RAM bytes, 400,245 application flash bytes. Added missing FreeRTOS task declaration before final build; no implicit-declaration warning remains.
- Parser ASan/UBSan checks **PASS**, including extra tone-argument rejection. Host lost-reply test **PASS**: status may retry, tone sends once. Source hashes: 35 reference files **PASS**.
- First explicit `tone` completed in 0.634 seconds, `audio_error=0`, `audio_stage=complete`, `tone_tests=1`. Parameters:440Hz/400ms,16kHz stereo16-bit,20ms ramps, digital peak2048 and codec setting85. These settings do not measure acoustic loudness.
- After cleanup, frames advanced31→52 and uptime4776→6840ms, touch remained ready and no reboot occurred during the observed interval. Code commands PA46 LOW, mutes codec and releases I2S on success/failure; the GPIO voltage was not independently measured.
- Owner missed the first sound and requested replay. Replay again returned error0/stage complete. Owner then confirmed: “Yes, I heard the beep.” A real tap after playback changed Classic→Pixel, touch_events0→1 at raw 204/65; frames advanced51→92, uptime 6784→10857ms. This verifies audible output and post-audio touch/face interaction. Raw coordinate orientation is still uncalibrated.

`tone` briefly blocks rendering, and is an explicit diagnostic rather than a production speech stream. No RX/microphone capture, network or filesystem access is added. A subsequent connection/reboot resets volatile counters; this document preserves the observed results.

## Follow-up: transient microphone levels (0.5.0)

The 0.4.0 display/touch baseline was reproduced before changes. Updated inventory records ES7210 at 0x40, RX GPIO10 and shared 42/9/45 clocks, four 16-bit TDM slots at 16 kHz,256×MCLK,24dB PGA,0dB digital volume and2.87V bias. Manufacturer slot order is MIC1/reference/MIC2/unused. Pinned Espressif esp-bsp1.0.1~1 supports the installed IDF4; its small attributed driver reuses Arduino HAL Wire0. The attributed esp_codec_dev shutdown sequence is included; no bus is recreated/deleted.

- 0.5.0 build/upload **PASS**: 20,764 static RAM bytes, 409,953 application flash bytes; upload hashes verified.
- Parser ASan/UBSan and host lost-reply checks **PASS**. Both physical actions (`tone`, `mic`) send once.40 retained-source/image hashes **PASS**. Reply reader is bounded1536 bytes; command input remains96.
- First actual room-level sample: 32,000 frames/slot, `mic_error=0`, `mic_stage=complete`, elapsed 2.317 seconds. RMS counts `[11,3,9,1]`, peaks `[59,34,75,17]`, clipped samples `[0,0,0,0]` in raw TDM order. These are PCM counts, not calibrated sound-pressure values.
- Sampling stopped before reply (`microphone_active=false`), shutdown sequence and RX release returned success. The application sample block is explicitly cleared; IDF DMA resources are released. Only aggregate levels are returned; no recording/transcript/file is retained.
- Frames continued15→36 and uptime 3453→5519ms after the room sample, without restart; touch stayed ready. Cued speech and visible-indicator acceptance were pending at0.5.0; accepted below in0.6.0.

Two seconds of input plus128ms settling is an explicit diagnostic. It is not continuous listening, recognition, transcription, duplex playback/capture, AEC or a cancellable production conversation.

## Follow-up: owner-triggered microphone test (0.6.0)

The owner missed the fixed timing windows in 0.5.0, including the readiness-cued pair; those noise-floor values are not failed speech tests. We found a source-level analog-enable difference between standalone esp-bsp and maintained codec-dev, recorded it before changing code and aligned four codec power values with the maintained sequence.0.5.1 power-only code built but was not flashed separately.0.6.0 combines that correction with a four-second sample and owner-controlled arming; this does **not** isolate the cause of the earlier low values.

- 0.6.0 build/upload **PASS**: 20,772 static RAM bytes, 410,209 application flash bytes; upload hashes verified. Parser ASan/UBSan passes new arm/cancel and extra-argument rejection cases.
- `mic-arm`/`mic-cancel` status checks **PASS**. Arming does not capture; the screen shows MIC TEST READY/TAP THEN SPEAK. The next valid tap starts one measurement and disarms. Normal unarmed taps still select faces. Active diagnostics end automatically; USB cannot cancel a running blocking capture.
- Corrected room sample: 64,000 frames/slot in 4.269seconds, RMS `[10,2,8,1]`, peaks `[281,28,173,13]`, no clipping, error0/stage complete.
- Owner confirms tapping and speaking during the red indicator. Actual triggered sample: 64,000 frames/slot, RMS `[119,2,121,1]`, peaks `[746,26,724,13]`, no clipping, error0/stage complete. Microphone slots 0/2 rose 11.9×/15.125× above the preceding room sample; other slots remained near their noise floors. This is measured acoustic response, not intelligible-speech/ASR quality or calibrated sound pressure.
- Physical trigger counter 0→1 at raw 274/154. Capture/arming both false after completion. A subsequent `tone` passed on the same USB session, verifying RX teardown→speaker TX initialization; owner previously confirmed the identical generated tone audibly. Frames84→105 and uptime 12569→15225ms after mic/tone cleanup, with touch ready and no restart.
- Unused-arm expiry **PASS** at 60.19 seconds: microphone_armed=false, microphone_active=false, mic_tests=0 and frames 602 / uptime 61,401 ms. No capture or reboot occurred. No raw samples, transcript, SD files, credentials or network request are retained by these tests.

Remaining audio work: calibrated gain/voice quality, playback-reference correlation, simultaneous TX/RX clocks, AEC, streaming, press-to-talk/cancel and one service conversation. Hardware input/output diagnostics now have actual physical observations.

## API/Control Room milestone — 2026-10-30

Owner preferred a route without phone setup and selected Google Gemini's free tier. Muse is optional. Existing personal Muse phone account is not a requirement we verified; one account across phone/site was guidance. The official Muse enrollment flow still requires the iOS/Android app; laptop token entry/flashing does not replace it.

Implemented separate host provider, TLS, private settings, persistent usage, gateway, HTTP and USB modules, plus a local HTML/CSS/JS manager. 26 synthetic backend tests, two USB tests and parser ASan/UBSan pass. Tests cover secret/auth boundaries, scope, request/response bounds, concurrency/restarts/UTC rate limits, native Google formatting, optional OpenRouter caps, TLS and preserving an AI reply after USB failure. No test fixture uses the real key. The actual key was entered by the owner only through the private local form, saved mode 0600 under ignored private/host/; it is not returned by status or copied into firmware/vault.

Initial live HTTPS failed because the portable Python's default CA path did not exist. Pinned certifi 2026.7.22 supplies a trusted root bundle; certificate and hostname verification stay enabled. Google model metadata and countTokens checks succeed. Early generation attempts returned an HTTP error or timed out; explicit minimal-thinking Flash-Lite request settings produced a real response and were verified through the browser adapter. No hidden model fallback was used. Native generation timeout is bounded 30 seconds. The app's Free-tier flag records owner confirmation, not independent Google billing verification. Local limits default 20 attempts/day UTC, 4/minute, 256 output tokens; failed attempts remain counted. OpenRouter/compatible live calls were not tested.

During UI testing the browser tool exposed a local manager unlock credential in a fragment URL; that credential was immediately revoked/rotated before the Gemini key was entered. The corrected flow consumes initial/hash-change fragments, removes the fragment before inspection and never places the provider key in a URL. No Gemini key was exposed. The service binds only 127.0.0.1, rejects unexpected Host/Origin and does not log request content. This is a local prototype, not a deployed LAN service.

Before firmware changes, 0.6.0 display/touch readiness and advancing frames were reproduced, and USB face commands worked through the manager. Compiled 0.6.0 recovery artifacts were preserved privately in private/backups/face-lab-0.6.0/ with addresses/sizes/hashes, separately from the original full-flash factory backup. 0.7.0 build/upload PASS: 21,036 static RAM bytes, 411,405 application bytes, all upload hashes verified. No pin/partition/PMIC/credential changes on the board.

Successful Control Room generation: “Hello, Mr. Robot, it's a pleasure to meet you!” The host delivered its short preview to 0.7.0; owner confirmed readable HOST REPLY/gemini-LAPTOP display. Firmware status reports caption_supported/available and provider, without echoing response text. Requests now allow 256 bytes for at most 96 printable-ASCII preview characters encoded as hex; malformed/control/oversized payload tests pass. The laptop retains the full visible reply; the device preview is RAM-only and expires 60 seconds after receipt. Voice indicators take priority. A USB error never triggers a second inference.

Caption metadata acknowledgement, continuing frames/touch readiness and owner pixels pass. Unused caption expiry passed at 60.54 seconds, with frames 816→1416 and caption_provider=none, without restart. No speech-to-Gemini, audio response, camera, autonomous actions, Muse pairing or SD filesystem operation occurred. Optional Muse/IDF source checkouts were downloaded but no Muse build/toolchain installation or flash was performed.

Final launcher acceptance: an existing local service passes the nonce/HMAC identity check, and a wrong local key fails it. This allows --open to reuse the current manager without exposing an unlock credential to an unrelated listener. Final ignored host key/config files retain mode 0600; key values were not printed.


## Voice-first Muse evaluation and Gemini model update — 2026-10-30

Owner reversed the earlier no-phone preference and supplied a Muse token, then confirmed a replacement after its chat exposure. The replacement was validated/normalized from the private file without printing it; .env is mode 0600. SDK/Wi-Fi build values remain empty. USB provision sends once after exact board status, suppresses raw echoes, receives @sdk_token ok and allows restart. Device NVS is plaintext. No raw audio or account/network credentials were retained in logs or notes.

Installed pinned ESP-IDF 6.0.1 tools in ignored external/esp-idf-tools/. The first installer attempt hit the portable PlatformIO Python's missing lzma extension; using the system Python 3.12 completed installation with TLS verification intact. CMake 4.0.3/Ninja 1.12.1 are the IDF-recommended versions. No global Homebrew install or factory-demo dependency was introduced.

Before changing firmware, Face Lab 0.7.0 reported display/touch ready, frames 6132→6142, uptime 615416→616424ms, microphone inactive/unarmed. Four compiled recovery artifacts with addresses/hashes were preserved under private/backups/face-lab-0.7.0/. Muse overlay enables experimental live voice (30 s idle / 180 s maximum), disables OTA/tunnel/remote BLE commands and leaves Secure Boot, flash encryption, eFuse auth and NVS encryption off. The image is 2,166,784 bytes in a 4 MiB slot, 48% free. Build/config guards and upload hashes pass. Exact non-C board status and chat support respond. A 6-second startup sample shows one boot, expected board, no panic or NVS-recovery requirement; this is not yet an extended reliability test. Token ACK passes; phone pairing/display/audio are pending owner action.

Gemini 3.8 Flash returned “Hello, friend.” in one bounded host-only request; model was saved only after success. No caption delivery is claimed for that check. Newer text-model request settings and separate Live rejection pass 28 backend tests. Four Muse-helper tests cover private env parsing, wrong-board refusal, echo suppression/single-send and flash guards. Control Room reload now visibly selects 3.8 Flash, with key field empty and USB disconnected for Muse; screenshot saved as docs/visuals/control-room-gemini-3.8-2026-10-30.jpg. An initially stale browser connection recovered after resetting the automation client.

Owner chooses Mac USB power for now and wants eventual PC-independent operation. Retained kit illustrations identify the 2× AA holder/buttons/breadboard; AA chemistry, polarity and converter remain unverified. No battery was connected. Voice/power plan records regulated USB, verified 1S lithium and converter options plus a proposed GPIO16-to-GND talk switch, not wired/enabled. Full upstream Muse host-test results are recorded separately when complete.


## Desktop enrollment check and USB stability — 2026-10-30

Owner confirms the Muse avatar is visible and entered Wi-Fi on the device. The signed-in Firefox web Settings → Devices panel was inspected: it shows “No devices found” with no Add Device/Developer mode control. SDK Web Bluetooth helper can configure an existing device/account token; it does not issue account credentials. SDK token and Wi-Fi alone are insufficient. The owner then chose **phone once for initial Muse pairing**; waiting for pairing confirmation. No web chat message, account settings, credential extraction or account terms acceptance was performed.

The serial helper initially reset the board when opening/deasserting modem lines. Match the pinned SDK console's asserted DTR/RTS and clear POSIX HUPCL. Hardware status now remains Wi-Fi connected across separate opens, uptime82→85 seconds without reset, paired=false/account credential=false. Shared hangup handling is reused by the Face Lab client; its software tests pass, but it was not reflashed just for this host change. Public Muse status prints only exact board identity and connection/configuration booleans, not raw SSID/IP/account/VM fields. Six helper tests and two USB-client tests pass.

The first upstream full test run exposed missing host CMake/FreeInk inputs and Darwin-only compiler/linker assumptions. Resolve through isolated test environment and the pinned FreeInk checkout, retaining sanitizers/assertions and leaving SDK source unchanged. A subsequent914-case run had one simulator incremental-avatar failure under Makefiles; its three tests pass with Ninja. The complete prepared suite is rerun with the IDF Python environment and Ninja; final result will be recorded below.


Pairing discovery follow-up: owner chose phone once, then reported that the phone cannot find the gadget. The SDK keeps unpaired advertising always on, so a setup-window expiry is not established. A deliberate normal reset (no erase) verified Muse/expected board startup, advertising_started=true, ble_error_codes=[], wifi_ip_observed=true, panic=false. Developer/community mode, phone permission, scanning location and app compatibility are the next checks. Do not claim account/voice acceptance yet. The owner's app/OS result is pending; guide saved as MUSE-PAIRING.md.


## Android discovery advances to physical confirmation — 2026-10-30

Owner later reports that Android now finds the gadget and requests a button press. The cause of the discovery change is not isolated. The correct non-C confirmation input is physical BOOT/GPIO0, identified in the supplied board illustration as item5 near the lower-left mounting hole when USB-C faces right. A brief press/release confirms the active session; the owner is guided to retry the app selection if the confirmation prompt expired. Account-pairing success and voice remain unverified until the subsequent status/owner check.

The complete prepared upstream SDK host suite now passes:914 tests in327.206seconds, four optional prerequisite skips. The earlier environment and simulator-generator failures were resolved through the isolated host environment/Ninja, without patching SDK source or disabling sanitizers/assertions. Current project checks:28 backend tests, six Muse/private-console tests, two USB-client tests;47 curated reference files match size/SHA256. No further firmware changes were needed for the pairing-confirmation guidance.


Screen report during confirmation: owner located BOOT but reported a frozen-looking screen. Read-only USB checks still respond, with Wi-Fi connected, no completed account pairing and uptime446→447seconds. A wake/happy animation probe returns subsequent status, without observed panic/watchdog/display-timeout markers; owner visual result remains pending. Latest link state is Ready to pair, rather than Confirm pairing. Source defines a60-second confirmation window; an expired request is possible but not assigned as the cause of the display report. Do not reset/erase/reflash merely from the frozen-looking appearance. Reopen phone selection after display acceptance to obtain a fresh confirmation request.


## Resumed pairing — 2026-10-31

Owner reconnected the Waveshare and confirmed the screen now responds normally. Exact non-C USB status responds with Wi-Fi connected, paired=false and no standalone account credential; uptime127→128 seconds, so status reads preserve runtime. Link state is Error at the initial check. Screen recovery followed reconnection; no display-driver fix or new firmware upload is claimed.

A redacted live UART monitor was started before a fresh phone attempt. Owner reports Android no longer discovers the gadget. Force-stopping/reopening Muse and scanning with its Developer mode did not restore discovery. Do not mark enrollment or voice complete, and do not erase stored setup to bypass the failure.

Built-in USB JTAG briefly halted/read/resumed the running CPU: BLE started=true, synced=true, advertising enabled=true, active=true, quiet=false, connection handle=65535 (no client). Debug processes were closed afterward. This rules out a connected client or disabled advertising for that observation; it is not independent over-the-air reception proof. Only static radio flags were read; no firmware, flash, eFuse or credential change occurred. Redacted diagnostic logs stay ignored under private/logs/.

Added `tools/muse.py watch`: a bounded metadata-only pairing monitor, retaining the current USB modem-line safeguards. It queries status every two seconds and prints fixed states/physical-confirmation acknowledgement, never raw logs or simulated confirmation. Nine synthetic Muse-helper tests pass; two original USB-client tests also pass using their script entry point. A 10-second hardware watch finishes normally with Wi-Fi connected, paired=false and link Connecting. Link Connecting alone is not pairing success. The standalone Settings credential flag is now named explicitly, since it is separate from app Link enrollment.

Requested phone model/Android/Muse versions and an independent same-phone nRF Connect scan. Owner reports Android 17, cannot locate Muse version and declines another phone app. The scanner check is deferred, not a prerequisite. Owner authorizes one final Muse attempt and then Google AI if it fails.

For that final attempt, the installed IDF esptool successfully performs a deliberate normal restart (`run`, no stub/flash/credential write). An initial invocation with PlatformIO's Python did not execute because that environment lacks the esptool module; the existing IDF Python/tool is used instead. A redacted watch sees Wi-Fi disconnected→connected and paired=false. Owner reports the gadget still does not appear after the requested Bluetooth toggle/fresh in-app scan; the monitor is stopped. Proceed with the authorized Google route, without assigning an unverified radio/app cause.

## Gemini voice implementation — 2026-10-31

Reproduced exact Muse board/Wi-Fi status with paired=false before replacement. Full-chip erase succeeds (14.7 seconds); Face Lab 0.8 build/upload hashes pass. Final scheduling build uses 21,980 static RAM bytes / 415,229 application bytes (binary 415,600 bytes). No SD operation or eFuse change. Exact Face Lab status reports display_ready=true, touch_ready=true, voice_supported=true and idle. Existing host provider key/Free confirmation stay private on the Mac.

Added modular MRV1 validation, PSRAM audio ownership/timeouts, MIC1 eight-second capture, strict-offset/CRC USB transfer and bounded 24 kHz output. Native Gemini Live uses verified WSS, a header-only key, no tools/history/automatic retry, 45-second generation deadline and twenty-second output cap. The existing persistent attempt ledger counts failed calls. One explicit tap is required per recorded turn after host arming. Second physical tap cancels capture/playback; mode stops on errors. No raw audio/transcripts are saved to files or logs.

First real Live greeting returns five seconds of PCM; board reports idle/played_turns=1 afterward. Owner hears the greeting but reports broken/choppy output. This proves the API/audio delivery path, not clean playback. Full-frame display flush during TX is a source-based contributor; a second build/upload pauses redraw during playback and increases the serial processing budget/reduces redraw during receive. No clean-playback conclusion is made before the next owner result.

37 backend tests pass, including Live handshake/format/redaction/no-retry, cumulative audio bounds, quota refusal before connection, audio cleanup and exclusive USB ownership. Both command/audio parser suites pass ASan/UBSan; two original USB-client tests pass. External Firefox Control Room visibly shows connected face-lab-0.8.0, an empty key field and new voice controls. First tap-to-talk test is armed and observed through metadata-only status.

Owner acceptance: **“I heard a clear reply.”** Metadata advances waiting_for_tap → thinking → speaking → waiting_for_tap, completed turns=1. The first earlier capture stopped after 118,272 frames with cancel/error259 and no API attempt. Subsequent full captures reach 128,000 frames, mic_error=0. After the clear reply, another physical turn starts; host Stop cancels its cloud generation, leaves it counted and does not retry. Total attempts at this checkpoint: 3 (greeting, accepted spoken turn, cancelled later turn).

Post-stop hardware: voice_phase=idle, microphone_active=false, voice_turns=1, mic_frames=128000, mic_error=0, audio_error=0/audio_stage=complete. Display frames advance 1706→1717 over uptime 202254→203368 ms without reset. No raw audio/transcript file was created. Clear speech is accepted for this test; long-run reliability, latency/quality benchmarking and all edge-case cancellation/expiry paths remain separate acceptance.

Explicit manager USB disconnect/reconnect also passes while voice is off: uptime 291364→291471 ms, display/touch ready, voice idle and microphone inactive. This connection change does not restart the board. Control Room remains running/open in external Firefox; enable tap-to-talk for the next physical turn. No microphone is armed automatically at handoff.

## 2026-11-06 — Local wake, Charon and USB latency

- Pre-change USB status verified Face Lab 0.8.0 with a completed turn, working display/touch and zero mic errors. Saved a private application-only rollback image before upload. The board now runs 0.9.2 with 22,004 bytes static RAM and 417,157 bytes application image. No credential, SD or wiring change was needed.
- The Mac's pinned Sherpa keyword model matched a synthesized “Hey Mr. Robot” and rejected “Hey Robert”. Hardware verified ordered 64 ms PCM blocks with CRC and automatic microphone stop on host inactivity. The host keeps up to 320 ms of rolling lead-in audio in RAM and sends audio to Gemini only for a triggered turn. A pause of about 640 ms ends speech capture.
- A synthesized spoken question produced 0.710 s of Gemini 3.8 Live Charon audio. The service took 2.381 s and the host issued playback 2.581 s after starting the API turn. A separate 48,000-byte upload took 0.209 s using binary chunks and 0.683 s using hex. These figures exclude time spent speaking and the pause used to detect the end.
- In Control Room wake mode, the device completed one reply with `voice_turns=1`, `touch_events=0`, `talk_button_presses=0`, and both mic and audio error codes at zero. The host measured 2.378 s from request start to the first playback command. A later turn reached Gemini and then hit a USB timeout. Host readback now checks whether the board accepted a transfer when its acknowledgement is missed. Repeat-turn and subjective voice acceptance are pending.
- 41 backend tests, two USB client tests, parser sanitizers and Control Room JavaScript syntax pass. A concurrent USB client was refused by the exclusive port lock. Control Room was reopened with the recovery change, connected to the Waveshare and left with voice off.
- The IO16 talk switch is implemented and its wiring is drawn. Its physical press, current Freenove connection and accessory displays are pending. [Button and camera sketches](BREADBOARD-CAMERA-DISPLAYS.md)

## 2026-11-06 — Interface and wiring refresh

- Read the shared conversation through its final wake/Charon/button milestone and reconciled stale current-state documentation. The moved workspace is `.`. The older manager process returned HTTP 500 from `/api/status`; restarting it from this workspace restored the service. No firmware reset was needed for that service recovery.
- Before edits, 0.9.2 compiled and parser checks passed. Hardware reproduced display/touch ready, microphone inactive and idle voice. Separate connections advanced uptime 3,707,201 → 3,707,306 ms and frames 30,636 → 30,637. Retained a private compiled 0.9.2 rollback set with addresses, sizes and SHA-256 under `private/backups/face-lab-0.9.2-ui-baseline/`.
- Face Lab 0.9.3 build and upload pass; all four write hashes verified. Build-time sections are 22,004 static RAM bytes and 416,245 application flash bytes, not physical capacity or free heap. The actual renderer passes sanitizer, microphone-priority, caption and circular text-bound checks. Display/USB/audio scheduling and pin assignments are unchanged.
- Post-upload metadata reports `face-lab-0.9.3`, display/touch ready, voice idle, microphone inactive and audio/microphone error 0. Separate connections advance uptime 7,450 → 7,550 ms and frames 63 → 64 without a reconnect reset. The upload itself intentionally restarted the board. Owner subsequently confirmed on 2026-11-06: **“Yes, it looks clear and the tap works.”** The revised idle face and “TAP TO CHANGE FACE” label are readable, and an ordinary screen tap changes the face. Active voice-state readability, cancellation and repeated-turn reliability remain separate acceptance checks. The rendered state sheet remains a host preview, not a photograph or voice acceptance.
- Control Room has a restrained light interface, keyboard-accessible tabs, responsive controls, explicit microphone status and distinct voice phases. Isolated browser checks at desktop and 390-pixel viewport cover mock text submission, keyboard navigation, listening display, service loss and recovery. Test hardware/voice state is simulated; the real microphone and provider were not invoked. Screenshot provenance is recorded in [Control Room design](CONTROL-ROOM-DESIGN.md).
- Wiring guides use retained photos and clearly illustrative breadboard coordinates. New SVG/PNG, Canvas and Excalidraw files are mirrored into Obsidian, alongside the renderer preview. Original photo/source hashes pass. The external switch, accessory displays and combined camera route remain physically unverified. [Assembly guide](BREADBOARD-CAMERA-DISPLAYS.md)
- Independent final audit reproduced and fixed two web defects: switching tabs hid Stop, and stalled status responses could retain stale indicators. Stop now lives in the shared device stage; read-only GETs have a ten-second deadline covering headers and body. No action retry or POST timeout was added. Eleven web tests, 41 backend tests, two USB-client tests, four firmware helpers, parser/renderer sanitizers, firmware build and all 47 source hashes pass. [Audit evidence](INTERFACE-AUDIT.md)
- Final external Firefox readback on the real service shows `USB · face-lab-0.9.3`, Google Gemini configured, microphone off, zero replies and 0/20 attempts for the current UTC day. The redesigned interface is open and ready; no live voice or provider request was started during the redesign. The isolated browser preview is separate from this real service.


## 2026-11-06 — Appearance, AA power and optional LED follow-up

- The owner clarified that the Codex screenshots are a reference for the entire visual style. Control Room now has System/Light/Dark appearances, neutral surfaces, system typography, subtle separators and compact controls. Only an allowlisted appearance preference persists; access credentials do not. Sixteen web regressions and JavaScript syntax checks pass. Desktop and 390 × 844 browser checks pass, including no horizontal overflow, retained Dark after reload with authentication locked, and shared Stop on Device and Connection. Tests use an isolated mock provider and simulated board/voice state. [Design and screenshots](CONTROL-ROOM-DESIGN.md)
- Before firmware changes, the physical board reported 0.9.3, display/touch ready, microphone inactive and idle voice; 0.9.3 source built and parser checks passed. Its compiled recovery images were preserved under ignored `private/backups/face-lab-0.9.3-led-baseline/`. This is a compiled recovery set, not a full flash/NVS backup.
- **0.9.4 source only** adds optional green question-capture and red reply-playback outputs. The ordinary build leaves GPIO17/18 entirely untouched. Normal build passes at 22,004 static RAM bytes / 416,689 application flash bytes; default-off and fake-GPIO opt-in tests pass under ASan/UBSan, along with existing parser/renderer checks. No upload or physical LED activation occurred. Installed firmware remains **0.9.3**. [LED behavior and verification](STATUS-LEDS-FIRMWARE.md)
- The owner chose the existing two-AA holder/cells and identified the LEDs as the retained kit parts. The new original breadboard JPEG is saved unchanged with provenance and SHA-256. The kit lists green/red LEDs and 220 Ω, 1 kΩ and 10 kΩ resistors; two 1 kΩ parts are the provisional low-current project choice. Guides distinguish kit identification from measurements of actual parts. The optional GPS variant can use the candidate GPIO17/18, and no external attachment does not establish absence of an onboard GPS chip. [Hardware and circuit evidence](HARDWARE-INVENTORY.md)
- The AA route needs an identified regulated converter and proper USB source interface; cell chemistry, polarity, discharge range and board peak demand remain unmeasured. AA cells must not connect directly to BAT/3V3/GPIO. Replacing USB power alone does not replace the current USB voice-data link. Drawings show these boundaries and the separate compatible-lithium alternative. [Power and status-LED guide](POWER-AND-STATUS-LEDS.md)
- The real Firefox Control Room is open in Dark, connected to `face-lab-0.9.3`, with voice stopped. Its existing status records one reply and a later device-rejected turn; this was already present before this appearance work. No cause is inferred from that metadata, and no fresh live voice, cloud request or device reset was initiated during this follow-up. Repeated-turn acceptance remains pending.

- The independent follow-up audit completed after all implementation agents. No new code defect was found in scope; sixteen web tests, both LED sanitizer branches, parser/renderer checks and the default 0.9.4 build pass. It traced capture/playback cleanup and checked breadboard nodes, AA boundaries, four SVG/PNG mirror pairs, Canvas, links and the original photo hash. Obsidian's plugin-normalized Excalidraw retains the same 19 elements semantically; the vault wording now distinguishes this from byte identity. The lead opened the note/drawing in Obsidian and verified their rendering. [Follow-up audit](INTERFACE-AUDIT.md#follow-up-audit-appearance-optional-leds-and-aa-power)


## 2026-11-13 · Button conversation and blue pixel face

The owner confirmed the green switch worked after routing ground directly from the Waveshare to the button strip. Before upload, Face Lab 0.9.3 reported 13 presses, one reply and a later USB timeout. Face Lab 0.9.5 builds at 22,004 static RAM bytes and 417,949 application flash bytes. The configured USB upload verified all write hashes. The installed board reports Pixel, display and touch ready, and optional LEDs disabled.

The new host arms the first turn on a button press and listens locally for speech for up to 15 seconds after every reply. It keeps one Gemini Live connection for the question and follow-ups. The blue Pixel face blinks, shifts its gaze while thinking and uses fixed expression cues from the spoken reply. Capture and playback use phase-specific still poses because full-screen transfers can disrupt audio. The host-rendered display checks, protocol checks, 43 backend tests and 15 web tests passed. The hardware returned a checksum-verified 2048-byte follow-up block and reported the microphone off after Stop. The first live test played a reply and then stopped on a quiet follow-up. The host now discards weak audio, ignores the first three microphone blocks after playback, and waits within the same 15-second window. The retest completed two spoken replies after one button press. The owner confirmed that the second reply remembered “blueberry” from the first question. The face geometry and state labels passed host rendering checks. Physical appearance has not been independently reviewed. [Voice guide](GEMINI-VOICE.md)

## 2026-11-13 · Automatic Gemini voice, larger faces and Ollama

Face Lab 0.9.5 USB baseline reported 5 presses and 3 completed voice replies. Face Lab 0.9.6 builds at 22,004 static RAM bytes and 416,361 application flash bytes. The upload verified all four hashes. The display and touch reported ready and the device accepted Classic, Orbit and Pixel commands and two of the new expressions. The host-rendered check exercised all 24 face and expression combinations. Physical screen appearance was not reviewed through a camera.

The Mac automatically connected to the single Waveshare and entered local wake listening on startup. Pause returned the board to idle with the microphone off. The owner confirmed both the green button and “Hey Mr. Robot” triggered voice without a web click. The real Control Room served an Ollama Gemma 4 12B text reply and sent its caption to the display. Switching back restored the private Gemini key and Free-tier confirmation and automatically rearmed voice. An isolated mobile browser check passed for Pause, the removed manual enable controls, the Ollama form and the pending Muse entry. Muse passed 77 SDK host tests using the pinned checkout and a macOS compiler flag for the SDK's dependency deprecation warnings. A paired end-to-end Muse test is pending. [Provider plan](VOICE-PROVIDERS.md)

## 2026-11-13 · Ollama audio input and round-screen text

Baseline 0.9.6 answered on USB with the mic off before the build. Face Lab 0.9.7 builds at 22,388 static RAM bytes and 417,601 application flash bytes. USB upload verified all four hashes. An authenticated typed question to gemma4:12b returned “Seven plus five is twelve” and the Waveshare acknowledged the Ollama caption. The physical green-button test advanced the press counter to one, moved through listening and thinking, completed one Ollama turn, and left a reply caption with the microphone off. The round renderer passed page and circular text-bound checks. A local synthetic WAV independently elicited “Twelve” from the installed Gemma 4 12B. [Ollama device guide](OLLAMA-DEVICE.md)

The reviewed non-C Muse build and private SDK token passed local validation. The Face Lab 0.9.7 rollback images and hashes were saved. A Muse phone pairing session is required to verify the token against the service and accept a real reply. [Muse trial runbook](../firmware/muse-evaluation/README.md)

## 2026-11-13 · Larger Ollama replies and Muse pairing trial

The owner saw the Ollama button reply and requested larger text without “OLLAMA REPLY.” Face Lab 0.9.8 doubles the caption font scale, centers each page, and shows a page count only for longer answers. The circular text bounds and firmware build passed. The physical board reported 0.9.8, display ready and a successful Ollama caption acknowledgement before its replacement with the reviewed Muse image. Optical acceptance of the larger fonts is pending.

Four 0.9.8 rollback images and hashes are stored in ignored `private/backups/face-lab-0.9.8-ollama/`. The existing ESP-IDF virtualenv pointed at a missing Python installation, so the installed esptool used the reviewed build's four explicit flash offsets and verified all four write hashes. The Muse booted on the expected non-C board. USB provisioning acknowledged the saved SDK token. After restart the board reported Ready to pair and paired=false. The owner has opened the Muse phone app for the pairing attempt. [Muse pairing guide](MUSE-PAIRING.md)

### Control Room and Face Lab 0.10.0 — 2026-11-14

The Three.js Control Room and local browser conversation history are live on port 18765. The Waveshare runs Face Lab 0.10.0 with the dual-boot Muse app preserved. See the [system audit](SYSTEM-AUDIT-2026-11-14.md) for the current provider matrix, display results and remaining physical checks.
