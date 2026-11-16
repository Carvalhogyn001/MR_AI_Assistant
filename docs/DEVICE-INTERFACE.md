# Device interface

Face Lab **0.10.0** has four screens on the existing 466 × 466 round AMOLED. Swipe left or right to cycle through Face, Settings, Device Status and Gallery. Tap the Face screen to change face, or advance an Ollama reply. Tap the left or right side of Settings to adjust brightness by 16 within the range 16–160. The Device tab in Control Room also selects any screen after pausing voice.

Classic, Pixel and Orbit remain available. The new Side-eye, Blush and Dizzy expressions are selectable in Device. Typed requests trigger Thinking or Drawing, followed by a bounded success or error reaction. Voice capture and playback take priority. Gemini Live chooses a reaction from the completed reply transcript and applies it as playback starts. Recording and playback avoid repeated full-frame transfers to protect the audio path.

Gallery displays the latest 300 × 300 RGB565 preview in volatile PSRAM. The browser saves the full 512 × 512 image. Wake detection still runs when Gallery is visible and updates the page's microphone indicator. Rebooting clears Gallery and resets the device's display settings.

Current firmware and USB verification are in [the November 14 audit](SYSTEM-AUDIT-2026-11-14.md). The following entries document earlier revisions.

Face Lab **0.9.3** refines the existing 466 × 466 round AMOLED display. It preserves Classic, Pixel and Orbit faces and the existing expressions, brightness, touch behavior and optional talk button. It changes drawing and labels only; audio, USB framing, timeouts, physical pin assignments and provider behavior remain unchanged.

Rendered state sheet (editable SVG) uses the actual `face_renderer.cpp` geometry and the pinned GFX 1.5.9 bitmap font. Host SVG rounded edges approximate the panel rasterizer. This is a source preview, not a photograph or proof of panel pixels.

## What the screen tells you

| Device state | Visual and action | Microphone meaning |
| - | - | - |
| Idle | Familiar robot eyes; tap changes face | Off; voice not armed. Does not claim that the Mac is disconnected. |
| Ready | Eyes; READY TO TALK; tap begins the question | Off until a tap or optional button press. |
| Wake | Eyes, coral dot, WAKE LISTENING; say “Hey Mr. Robot” or tap | On; the existing Mac-local wake detector is active. Stop wake mode in Control Room. |
| Listening | Coral bars, LISTENING, pause-to-finish hint, tap-to-cancel | On; this is the explicit question capture. Legacy fixed-length capture shows its bounded countdown. |
| Thinking | Three lavender dots, THINKING, tap-to-cancel | Off; the host is preparing the reply. |
| Receiving | Lavender download symbol, GETTING REPLY, tap-to-cancel | Off; reply audio is transferring. |
| Speaking | Teal outlined bars, SPEAKING, tap-to-cancel | Off; reply audio is playing. |
| Stopped | Coral stop indicator, VOICE STOPPED, CHECK CONTROL ROOM | Off. The existing transport shares one state for cancellation and errors, so no specific cause or invented tap-to-retry action is shown. |
| Host caption | Eyes and up to four short lines, provider source | Off; full response remains in Control Room. |
| Microphone diagnostic | Distinct local-test label and existing L/R values | Active capture takes priority over stale captions or an earlier voice error. |

The repeated title and secondary mode label stay quiet; the action and current state carry the visual emphasis. Text cells remain inside a 222-pixel-radius safe circle, leaving at least an 11-pixel inset on this 466-pixel display. Text uses the existing built-in font, without a new font or graphics dependency.

Listening and speaking bars are status symbols, **not an audio meter**. The firmware deliberately avoids full-frame display writes during streamed capture and playback because those writes can starve the audio DMA queue. Idle eyes blink/drift and thinking dots change at the existing render cadence. This change does not add rendering load during audio streaming.

## Verification — 2026-11-06

Before edits, the original 0.9.2 firmware compiled and both parser suites passed ASan/UBSan. Baseline build output: 22,004 static RAM bytes and 417,157 application flash bytes. Root-agent metadata observations found display/touch ready, microphone inactive and advancing uptime across separate USB connections (3,707,201 → 3,707,306 ms). This establishes continuity of the prior firmware, not acceptance of revised pixels.

The 0.9.3 build passes with **22,004 static RAM bytes** and **416,245 application flash bytes**. These are build-time section sizes, not free heap or physical memory capacities. Existing command/audio parser suites pass ASan/UBSan. The renderer itself also compiles under ASan/UBSan against a host vector recorder and the installed, pinned font. Checks cover microphone-label priority, cancelled/error guidance, worst-case 96-character caption geometry, circular text bounds, and all 12 face/expression combinations. The state sheet was generated from that renderer.

Run from the project root:

```sh
python3 tools/test_assistant.py
~/.platformio/penv/bin/pio run -d firmware/assistant
python3 firmware/assistant/tests/preview_display.py
# Curated source preview, only when intentionally updating documentation:
python3 firmware/assistant/tests/preview_display.py docs/visuals/device-interface.svg
```

By default the preview writes to ignored `private/previews/`. The host recorder does not simulate hardware timing, touch, SPI, or actual colors/brightness. Physical acceptance after upload must confirm a stable full face, ordinary tap face changes, clear labels on the round screen and continuing uptime/frames; active voice states require a user-started voice turn. Do not infer microphone or playback acceptance from an SVG preview. Root-agent integration results belong in [Project Status](PROJECT-STATUS.md).


Owner physical acceptance — 2026-11-06: after the 0.9.3 upload, the owner confirmed **“Yes, it looks clear and the tap works.”** This verifies the revised idle face and “TAP TO CHANGE FACE” label are clear and an ordinary screen tap changes the face. Active listening/thinking/speaking readability, cancellation, repeated-turn reliability and the external talk switch still need their own physical checks. No new firmware build, microphone activation or provider request was needed to record this confirmation.
