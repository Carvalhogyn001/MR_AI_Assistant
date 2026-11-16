# Interface audit

2026-11-06, America/Los_Angeles. Performed after the web, device-interface and hardware-guide agents completed their implementation. This is a focused review of the interface refresh, not a certification of the whole firmware or external AI services.

## Findings and fixes

Two integration findings were independently reproduced by new failing regression checks before being fixed. The original nine web tests passed during that reproduction; the two new checks failed.

| Severity | Reproduction and impact | Fix and evidence |
| --- | --- | --- |
| P2 | Enable a voice session, then select Device or Connection. Stop lived inside the now-hidden Conversation panel, removing the web cancellation control from that view. | Moved the existing button and handler into the shared device stage. The visibility check traverses hidden ancestors and verifies Stop remains enabled in all three tabs. |
| P2 | Leave a status response waiting indefinitely, either before headers or during its JSON body. The previous microphone/connection state remained visible, and the in-flight poll prevented recovery polling. | Added a ten-second abort deadline to read-only GETs, covering headers and body. A timeout clears the live-state claim, retains Stop for the last active voice session and releases the poll for recovery. Action POSTs receive no deadline or automatic retry from this change. |

The earlier microphone-diagnostic priority fix was also reviewed and its regression test passed: actual diagnostics override a retained voice error only when host voice is inactive. Cached device diagnostics cannot override active host voice.

Changed during audit: `manager/app.js`, `manager/index.html`, `manager/style.css`, `manager/tests/app.test.cjs`, and the interface documentation. No firmware or hardware pin changes were needed. No remaining release-blocking defect was found within the reviewed scope.

## Verification

| Check | Result |
| --- | --- |
| `node --check manager/app.js` and `node --test manager/tests/app.test.cjs` | PASS; 11 web regression tests, including both reproduced defects and no deadline on in-flight text POSTs. |
| `python3 tools/test_assistant.py` | PASS; command and audio parser suites under ASan/UBSan. |
| `python3 firmware/assistant/tests/preview_display.py` | PASS; actual renderer, microphone-label priority, caption bounds, circular text geometry, 12 face/expression combinations under ASan/UBSan. |
| `~/.platformio/penv/bin/pio run -d firmware/assistant` | PASS; Face Lab 0.9.3, 22,004 static RAM bytes / 416,245 application flash bytes. These are section sizes, not physical capacity or free heap. |
| `PYTHONPATH=backend ~/.platformio/penv/bin/python -m unittest discover -s backend/tests -q` | PASS; 41 tests with synthetic provider/transport fixtures. |
| `~/.platformio/penv/bin/python tools/test_device.py` | PASS; two USB-client tests. No serial device was opened by this audit. |
| `python3 tools/run_host_tests.py` | PASS; four existing firmware-helper tests. |
| `python3 tools/verify_sources.py` | PASS; 47 retained references match size and SHA-256. |
| Wiring artifacts | SVG XML, Canvas node/edge references, Excalidraw element IDs, relative guide/asset links and expected PNG presence pass. Photo map visually inspected. |

Source review confirms credentials remain host-held; browser access stays in memory and is removed from the URL; provider text is inserted using text content rather than executable markup. The existing authenticated loopback endpoints, output bounds, USB ownership and modem-line protections remain in place.

The firmware renderer preserves the existing audio scheduling: capture/playback do not acquire animated full-frame redraws. The preview uses the actual renderer and installed bitmap font, while its vector rasterization is only an approximation of the physical panel. Listening/speaking bars are labeled as status symbols, not measured audio.

Wiring guidance matches the recorded IO16-to-GND assignment and explicitly requires checking actual printed labels and switch continuity. It does not infer physical header order from conflicting references. The Freenove retains its camera ribbon; camera integration, LCD electrical checks and the bare matrix pinout remain pending. No 5 V GPIO connection is prescribed.

## Integration and limits

The technical lead reported desktop/mobile layout, keyboard tabs, mock text requests and disconnected/recovery behavior passing in an isolated browser preview. After the audit fixes, Stop remained visible exactly once on Device and Connection during simulated listening, the 390 px mobile viewport had no horizontal overflow, and a fresh console check had no warnings/errors. The [design document](CONTROL-ROOM-DESIGN.md) links the final synthetic desktop/mobile screenshots. The final hardware acceptance record belongs in [Project Status](PROJECT-STATUS.md).

After firmware review cleared, the technical lead uploaded 0.9.3 with all four image hashes verified. Metadata showed display/touch ready, microphone inactive, voice idle and zero audio/microphone errors. Separate connections advanced uptime 7,450 → 7,550 ms and frames 63 → 64. These are lead-reported hardware observations, not an independent physical inspection by the auditor.

Post-audit owner follow-up on 2026-11-06 confirms: “Yes, it looks clear and the tap works.” This accepts the revised idle face/label and ordinary tap-to-change-face behavior; it is owner-reported evidence, not an independent inspection by the auditor. Active voice-state readability, repeated-turn reliability, cancellation and the external switch remain separate physical acceptance checks. The audit did not record audio, call a real provider, operate USB, wire accessories or test the camera.

## Follow-up audit: appearance, optional LEDs and AA power

2026-11-06. Performed independently after all three follow-up implementation agents completed. Scope: System/Light/Dark in `manager/`, optional status LEDs and their audio lifecycle hooks in `firmware/assistant/`, and the power/LED/breadboard drawings and Obsidian mirrors. **No new code defect was found within this scope, and no application or firmware code was changed by this audit.** The prior two fixes remain covered by the current web tests.

The theme choice is allowlisted before use and is the only value written to local storage. Invalid or unavailable storage does not block startup. OS appearance changes apply only in System mode; neither theme changes nor responsive navigation initiate a request. Access remains in memory, so an ordinary reload retains appearance but requires a fresh authorized launch. The sixteen tests pass, including existing pending-request, authentication, microphone-state, timeout and Stop regressions.

The default LED branch contains no Arduino GPIO access and reports both outputs off. Opt-in startup sets both inactive latches before configuring outputs, suppresses repeated unchanged writes and turns an old output off before another on. The candidate pins do not overlap the current display, touch, USB, audio or IO16 assignments. Actual GPS fitment still gates their use: the manufacturer identifies possible LC76G sharing on IO17/18. [Waveshare hardware reference, rechecked during this audit](https://raw.githubusercontent.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/main/HARDWARE_REFERENCE.md)

Source tracing covered the actual microphone, speaker and voice-transport call paths. Green begins only after capture setup succeeds, including the existing wake-to-question stream transition. Blocking capture has scoped cleanup; stream failure, completion, physical cancel, explicit Clear and stream expiry reach the stop path. Red begins after output setup and the first accepted reply PCM buffer, with scoped cleanup on completion, write error or physical cancel. Setup failures leave outputs off; amplifier shutdown clears them again. Wake monitoring, thinking/receiving and ordinary diagnostics keep both off. Host checks test the actual LED module and cleanup scope; they do **not** exercise real codecs, inject faults into physical I2S, measure emitted light or establish cancellation latency on the board.

The breadboard guide has separate resistor-input, LED-anode and LED-cathode nodes: green rows 6/10/12 and red rows 18/22/24, with separate returns joining row 26. Each branch has its own resistor; no rail or cross-gap connection is required. Contact labels and placement are illustrative, with actual part spacing/continuity explicitly pending. The AA drawing requires a suitable regulated power stage and USB source interface; it neither assigns BAT polarity nor treats battery power as a replacement for USB voice data. The project’s proposed 1 kΩ parts are distinguished from the manufacturer’s 220 Ω example and from measured component values. [Freenove LED lesson, rechecked during this audit](https://docs.freenove.com/projects/fnk0047/en/latest/fnk0047/codes/C/1_LED.html)

| Follow-up check | Result |
| --- | --- |
| `node --check manager/app.js`; `node --test manager/tests/app.test.cjs` | PASS; 16 tests. |
| `python3 firmware/assistant/tests/test_status_leds.py` | PASS under ASan/UBSan; default build has zero GPIO operations, fake-GPIO opt-in covers phase/activity policy, startup ordering, break-before-make and cleanup. |
| `python3 tools/test_assistant.py`; `python3 firmware/assistant/tests/preview_display.py` | PASS; command/audio parsers and actual renderer under ASan/UBSan. |
| `~/.platformio/penv/bin/pio run -d firmware/assistant` | PASS; default-disabled **0.9.4 build**, 22,004 static RAM bytes / 416,689 application flash bytes. No upload. |
| New artifact checks | PASS; three generator sources parse, four SVG/PNG pairs match their vault mirrors, Canvas node/edge references and local links/embeds resolve, original JPEG size/SHA-256 matches provenance. LED/breadboard/AA PNGs visually inspected. |
| Plugin-normalized Excalidraw | PASS; decoded the installed plugin’s compressed format and verified all 19 elements retain their order, positions, text, line points and colors. The plugin normalized text IDs/widths and compression; the vault note now describes this accurately instead of claiming byte identity. The drawing itself was preserved. |

No backend behavior changed or new backend concern emerged, so the unchanged backend suite was not repeated in this follow-up. The earlier results above remain historical evidence.

The technical lead separately reports desktop and 390 × 844 Light/Dark browser acceptance, Dark persistence with authentication locked after reload, working Stop in Device/Connection against an isolated synthetic fixture, and no console warnings. The lead also opened the power note and editable Excalidraw in Obsidian and observed rendered embeds/shapes/text without load errors. These are lead-reported UI checks; [screenshots and provenance](CONTROL-ROOM-DESIGN.md) remain separate from hardware acceptance.

README, Project Status, inventory, LED documentation and the vault note distinguish **installed 0.9.3** from **built, unflashed 0.9.4**. The lead’s real-browser readback remains 0.9.3 with voice stopped; no fresh audio/provider acceptance is inferred. Actual GPS fitment, LED polarity/rating, resistor values, unpowered circuit continuity, LED current and start/cleanup behavior remain unverified. AA chemistry/polarity, converter/source interface, peak demand and battery operation remain unresolved. This audit performed no serial operation, firmware upload, microphone capture, provider request, wiring or charging change.
