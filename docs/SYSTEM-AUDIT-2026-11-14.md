# MR. Robot system audit

November 14, 2026, America/Los_Angeles

## Skill review

| Package | Pinned snapshot | Scope reviewed and used |
| --- | --- | --- |
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/commit/d643997c82e94742dd3bee43210b0198e8bbba3d) | `d643997c82e94742dd3bee43210b0198e8bbba3d` | Installed only `.claude/skills/ui-ux-pro-max` under `~/.codex/skills` using the pinned GitHub archive. The installed directory matched the reviewed copy. Reviewed its instructions, local catalogs and Python search path. The design and Three.js searches ran with an empty inherited environment and generic product terms. The search reads bundled data and can write design documents when explicitly requested. The npm CLI and plugin hooks were outside the install. |
| [Taste Skill](https://github.com/Leonxlnx/taste-skill/commit/f6b76575f949707b4e3c37cd86cb44b0b98643e8) | `f6b76575f949707b4e3c37cd86cb44b0b98643e8` | The installed skill matched the upstream skill directory with a recursive comparison. Reviewed its instructions and command entry points. It includes remote photo/icon helpers and browser subprocesses. Used the layout guidance and its local screenshot helper with a separate Chrome profile. |

The reviewed workflows showed no credential collection or unexpected data destination. The assessment covers these snapshots and the workflows above. Upstream updates and tools outside that scope need separate review.

## Provider checks

| Route | Result |
| --- | --- |
| Mock | Live Control Room text round trip. |
| Ollama text | `gemma4:12b`, `gemma4:e4b`, and `qwen3.6:latest` each returned the requested short reply through the native adapter. |
| Ollama audio adapters | Synthetic 16 kHz mono PCM reached Gemma 4 12B and received a direct answer. The Qwen and Z-Image audio routes transcribed the synthetic prompt through Gemma. Qwen then answered the resulting text. |
| Ollama image | `x/z-image-turbo:latest` produced a valid 512 × 512 PNG via the pinned local image runtime. A live browser request returned `image_sent`, the board reported Gallery with the image available, and Chrome restored the image after reloading. |
| Compatible | Live OpenAI-style `/v1/chat/completions` through local Ollama with `gemma4:12b`. |
| Gemini text | `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` passed using the saved Free-tier profile. The advertised `gemini-3.8-flash` and `gemini-3.6-flash` returned upstream 503 or timed out across two attempts each. The saved model is still owner-selected. |
| Gemini 3.8 Live | A short synthetic text input returned 125,762 bytes of 24 kHz PCM. USB playback acknowledged that audio. From the start of the USB audio transfer, the host reached the play command in 0.54 s and received playback acknowledgement 2.86 s later. The test supplied a reaction before playback. Physical speaker audibility and the combined spoken turn remain visual/acoustic checks. |
| Muse | The installed app reported paired and resumed its Wi-Fi link. It replied `OK` through USB once the link reported Online. A request immediately after switching failed while the link was reconnecting. Control Room now waits for Online before sending. Switching back restored Face Lab. |
| OpenRouter | Adapter tests passed for request formatting, bounded responses, verified TLS, no redirect and provider-side spend-cap checks. No OpenRouter key or capped model profile was configured for a live request. |
| Physical voice triggers | The ESP32 initialized its microphone, captured a checksum-verified 2,048-byte wake block and completed a level test with 64,000 frames and no driver error. Spoken wake, green-button capture across each voice-enabled model, and image generation by voice require an in-person run. |

The model matrix covers installed and advertised choices on this host. Additional compatible endpoints and provider catalogs can vary by account and are outside these observations.

## Web and board checks

- Chrome exercised the redesigned controls at 1440, 1024, 768 and 390 px, including reduced motion, keyboard tabs, theme changes and text/PNG history restored after reload. A separate Chrome run verified the CSS robot with WebGL disabled. Clearing local history kept the previous cached image from coming back.
- The baseline Face Lab 0.9.8 reported advancing uptime from 2,039,843 to 2,040,891 ms across separate exclusive USB connections. It accepted wink and neutral. After the Face Lab 0.10.0 build and slot-only flash, the board acknowledged Face, Settings, Status and Gallery, plus Side-eye, Blush and Dizzy. The transient end reaction returned to idle at the programmed timeout. Display and touch initialized.
- A real PNG was converted to 180,000 bytes of RGB565. The board accepted the frame, passed its CRC check and selected Gallery. A separate USB open retained the image and reported uptime advancing from 65,269 to 65,375 ms. Under repeated testing, a lost chunk acknowledgement interrupted a transfer. Bounded retries now accept duplicate data and commit acknowledgements without advancing the buffer twice. The integrated browser-to-board test passed after the retry change.
- The direct renderer passed 33 face/expression combinations, screen layouts, circular text bounds, microphone priority, and activity timing labels. Firmware parser and image transfer tests passed with ASan/UBSan. PlatformIO reported 22,436 bytes of static RAM and a 421,169-byte application estimate for the final build. These are linker measurements. The signed app was flash-verified at `0x420000` only. The prior signed Face Lab slot is preserved in ignored recovery storage. The two apps and pairing were checked across switches. The hardware wiring and pin map stayed as inventoried.

The host can read display readiness and acknowledged state. Physical swipe direction, colors, legibility and acoustic results require observing the board.

## Nice to have

- A searchable, exportable local conversation archive for moving between browsers.
- An installed-model picker with capability and availability checks before switching providers.
- A board option to keep the last generated image across reboot, backed by an explicit SD retention setting.
- A voice timing inspector showing capture, inference, USB transfer and playback start for each turn.

## Repeatable checks

```sh
node --test manager/tests/app.test.cjs
PYTHONPATH=backend:. ~/.platformio/penv/bin/python -m unittest discover -s backend/tests
python3 tools/test_assistant.py
python3 firmware/assistant/tests/preview_display.py
python3 firmware/assistant/tests/test_status_leds.py
pio run -d firmware/assistant
```

Use the [dual-boot update procedure](../firmware/muse-evaluation/README.md) for this board. For a quick hardware check, pause voice and disconnect USB in Control Room, then run `~/.platformio/penv/bin/python tools/device.py status` twice before reconnecting. `screen gallery` or `expression blush` can be substituted. Use the same board with only one USB client at a time.
