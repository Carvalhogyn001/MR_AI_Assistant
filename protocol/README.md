# Device Control Protocol v1

Voice in Face Lab uses separate `MRV1` frames on the same exclusive USB connection. Existing `MRR1` command limits remain unchanged. See [voice setup/data limits](../docs/GEMINI-VOICE.md).

`MRV1 SESSION arm|status|clear|thinking|play`; `MRV1 SESSION read OFFSET`; `MRV1 SESSION begin BYTES CRC32`; `MRV1 SESSION write OFFSET HEX`. Session is 1–65535. Voice lines cap at 1152 characters; data chunks at 512 bytes. PCM lengths/offsets are bounded and uploads require ordered offsets. Replies are `MRV1 {JSON}` with session id and `ok`, metadata or requested PCM hex. Only a read reply contains capture data. CRC32 matches standard zlib/IEEE (test vector `123456789` → `cbf43926`).

Legacy `arm` waits for a screen tap before capture. One physical screen tap starts eight seconds; another tap cancels. Full input checksum must pass before cloud use; full output checksum must pass before playback. Buffers clear on completion/cancel/error expiry. Arm watchdog: 60 seconds; processing: 60 seconds; upload idle: 15 seconds; device-turn watchdog: 180 seconds, evaluated between bounded operations. Status polling does not extend deadlines. Never retain raw voice-console logs. The host has one outstanding voice operation and no automatic retries; regular controls are excluded during voice ownership.

Face Lab 0.9 adds `MRV1 SESSION watch|arm-fast|trigger|sample|finish`. `watch` starts the microphone in wake phase. `arm-fast` waits for a tap or IO16 press. `trigger` moves wake to recording and the next sample header confirms the transition. A `sample` reply is a JSON header with session, phase, sequence, byte count and CRC32, followed by 2048 raw PCM16 bytes (64 ms at 16 kHz). `finish` shuts off the mic and enters thinking. If the host stops sampling for 2.5 seconds, the board closes the stream.

After `begin`, send `MRV1 SESSION bulk OFFSET BYTES` followed by the exact binary bytes (even length, at most 4096). The board reads each block with a one-second deadline and reports the accepted offset. The host validates the size, CRC and offsets and can read status to confirm a missed acknowledgement. Playback begins only with a complete verified buffer. All voice and regular controls share the exclusive USB owner.

The custom firmware exposes a narrow USB interface for the planned desktop manager. Current implementation: `firmware/assistant/src/control_protocol.cpp` and `tools/device.py`. No HTTP server, Wi-Fi provisioning, AI routing or firmware upload command exists in this protocol.

## Framing and commands

115200-baud USB serial, printable ASCII, newline-terminated, at most 256 bytes excluding CR/LF in0.7.0 (96 in earlier builds). Request IDs are integers 1–65535. Unknown commands/values, extra arguments, control characters, overflowed IDs and oversized lines are rejected without changing state. Oversized lines are discarded through the next newline, then the receiver recovers.

```text
MRR1 1 status
MRR1 2 face classic
MRR1 3 expression happy
MRR1 4 brightness 96
MRR1 5 card
MRR1 6 tone
MRR1 7 mic
MRR1 8 mic-arm
MRR1 9 mic-cancel
```

| Command | Allowed values |
| - | - |
| `status` | No argument |
| `card` | No argument; raw card metadata without mount/write/format |
| `tone` | No argument; one 440 Hz / 400 ms low-level generated speaker test |
| `mic` | No argument; one four-second level measurement, no raw audio output |
| `mic-arm` | No argument; wait up to 60 seconds for one tap to start measurement |
| `mic-cancel` | No argument; cancel a pending armed measurement |
| `face` | `classic`, `pixel`, `orbit` |
| `expression` | `neutral`, `happy`, `curious`, `sleepy` |
| `brightness` | Integer 16–160 on the panel's 0–255 scale |

Replies start `MRR1 ` followed by a single JSON object. The same request ID correlates success/error. Malformed framing may return ID 0. Boot messages and heartbeat lines have other prefixes and are not protocol replies.

Success contains current configuration, firmware/protocol version, display initialization result, frame counter, uptime and explicit capability flags. `display_ready` confirms the initialization call returned successfully; it cannot confirm physical pixels. `ai_connected`, `network_enabled` and `sd_mounted` are false in Face Lab. The amplifier is commanded off before replying, so `speaker_enabled` is false in replies, including after a tone test. Face expression alone never means the microphone is active.

```text
MRR1 {"id":3,"ok":false,"error":"invalid_value"}
```

Reads/setters may be retried with the same request ID during boot. The `tone` and `mic` actions are not idempotent: every explicit command can play a tone or start a measurement. The host sends each once and never automatically retries it after a lost reply. Initialization uses a retryable status request before any action. Settings are not persisted. Only one request may be outstanding on a connection. There are no arbitrary paths, shell commands, credential fields, raw media or executable uploads.

Version 0.2.0 also reports `card_inspected`, `card_raw_bytes`, `card_filesystem`, `card_error`. `ok=true` means the command was processed; inspect `card_error` for hardware failure. Filesystem strings identify boot-sector signatures only; they do not prove integrity. `sd_mounted` remains false. The host may use a longer timeout for card initialization.

## Future desktop system

Keep these responsibilities separate:

- Desktop UI: preview and select supported faces, expressions and brightness; display actual connection/capability/error state.
- Device client: framing, timeouts and capability negotiation; reuse the Python `Device` boundary initially.
- Asset service: later validated manifests/dimensions/size/hash, selected project assets and explicit transfer commands. No arbitrary SD paths.
- AI backend: server-side provider configuration and secrets, bounded request/response interface, selected model and rate/cost limits.
- Device firmware: actual hardware operations and UI state. It must reject unsupported features rather than presenting them as active.

Muse integration has a different provisioning/session protocol and remains a separate SDK evaluation. A future custom backend can offer multiple providers through one application interface, but the first USB control protocol is not a Muse replacement or a network API.

Version 0.3.0 adds touch_ready, touch_events, touch_x and touch_y. Readiness means controller identity/resolution initialization succeeded; only observed physical events verify taps. Touch changes cosmetic face state without a USB command. The existing request limit 96 bytes and bounded reply reader remain unchanged.

## Speaker diagnostic (0.4.0)

`tone_tests` counts completed software transfers/cleanup, `audio_error` is the last ESP error integer, and `audio_stage` identifies the last completed/failed stage. `ok=true` means command processing; require `audio_error=0` and a counter increment for software success. Hearing the tone requires owner confirmation. Initial `audio_stage=untested` distinguishes no test from success. No microphone/RX is started.

Tone parameters are fixed in firmware:16kHz stereo16-bit, identical channels,440Hz for400ms,20ms amplitude ramps, peak2048/32767 and ES8311 volume setting85. The codec setting is not a measured loudness percentage. TX I2S exists only during the operation; cleanup mutes the codec, commands PA46 LOW and releases I2S on success or failure. Rendering may pause briefly during this blocking diagnostic; production streaming/cancellation requires a separate design. No boot sound, automatic replay, media path or adjustable-volume command exists.

## Microphone level diagnostic (current 0.6.0)

`mic` enables RX-only four-slot 16-bit TDM at 16 kHz, discards 128 ms for settling, and measures 64,000 frames per slot. There is no speech recognition, transcription, playback loopback or network upload. The panel displays MIC LEVEL TEST with a red dot and current L/R levels while acquiring. Sampling stops and the indicator clears before the reply. The serial client uses a bounded 1536-byte reply reader; input stays 96 bytes. This prototype measurement is bounded but blocking and cannot be cancelled by another USB command; production press-to-talk/cancel remains a separate task.

Reply fields: `microphone_active` (false after cleanup), `mic_tests` (completed measurements), `mic_frames` (per slot), `mic_error`, `mic_stage`, four-element `mic_rms`, `mic_peak`, `mic_clips`. Values are raw 16-bit PCM counts, not calibrated dB SPL. Slot order follows the manufacturer:0=MIC1,1=playback reference,2=MIC2,3=unused. Reference routing is still unverified by a playback/capture correlation test. `ok=true` only acknowledges command processing; inspect mic_error, stage and frame count.

The application keeps only one temporary 256-frame block, clears that application buffer explicitly and releases IDF DMA resources. Only aggregate numbers leave the device; no audio file, transcript or individual sample is transmitted or saved. ES7210 shutdown follows the attributed Espressif stop sequence; all shutdown writes are attempted, the first error is reported, and RX is released on every exit. PA46 remains LOW. Audio tests use the bus sequentially; simultaneous speaker/mic streaming and AEC are not implemented.

Arming is separate from capture. `mic-arm` sets `microphone_armed=true` only if touch is ready, and the screen shows MIC TEST READY/TAP THEN SPEAK. The next valid tap disarms and starts one four-second measurement. No tap within 60 seconds clears arming. `mic-cancel` clears pending arming; it cannot interrupt a running blocking diagnostic. Direct `mic` also clears arming before sampling. These setters may retry; `mic`/`tone` physical actions never retry automatically. Normal unarmed taps keep selecting faces; arming never persists over reboot.

## Host caption preview (0.7.0)

`MRR1 ID caption PROVIDER HEX_TEXT` accepts source mock/gemini/openrouter/compatible and 1–96 printable ASCII characters encoded as 2–192 hex digits. The entire frame is bounded 256 bytes. Odd/invalid hex, nonprintable decoded bytes, extra fields, unknown providers and excessive payloads are rejected without state mutation. `MRR1 ID caption-clear` clears it. Earlier commands remain compatible; the host gates caption delivery on `caption_supported`.

Status adds caption_supported, caption_available, caption_provider and max_command_bytes. It deliberately does not echo response text. Acknowledgement means state processing; only owner observation verifies panel text. Direct board ai_connected/network_enabled remain false: the caption is the last reply from a laptop provider, not a direct ESP32 network session. Captions have no executable meaning.

Preview text is normalized by the host into bounded ASCII, word-wrapped on four 24-column rows and may end with an ellipsis; the full response remains in Control Room. Source is labelled as coming from the laptop. Mic-arm/active indications take priority. Text is volatile, explicitly cleared on supported disconnect and expires 60 seconds after receipt, without a filesystem/NVS write. Reads of status do not extend expiry. Settings/face selection remain independent from provider choice.


Face Lab 0.9.5 advertises `voice_conversation_supported` in MRR1 status. In a current MRV1 streaming session, `follow` can start local follow-up capture from idle and returns the recording phase. The Mac detects speech before sending a bounded utterance to the provider. `react 0..3` selects neutral, happy, curious or soft during thinking. Both commands require the existing session ID and the correct device phase. No transcript is sent to the device.

Face Lab 0.9.7 adds local Ollama display and recording capability flags. When advertised, MRR1 `caption ollama` and `caption ollama-prompt` accept up to 480 printable ASCII bytes as hex. The screen pages the volatile text and clears it after 60 seconds without a screen tap. The MRV1 `local` command starts a bounded recording without waiting for a second press. The Mac calls it only after detecting a new physical button event with a supported local model selected. The result is sent as a caption after microphone cleanup.

## Face Lab 0.10.0 display commands

`screen face|settings|status|gallery` selects a page. `activity idle|thinking|drawing|done|error` reports host inference and selects Face for an active reaction. Done and error expire after 3.5 seconds. Thinking and drawing have a 200-second watchdog. Voice and mic diagnostics own the active capture/playback display.

Status advertises `screens_supported`, `activity_supported`, `image_supported`, `screen`, `host_activity` and `image_available`. New expression values are `squint`, `blush` and `dizzy`.

An exclusive host session sends `image-begin CRC32`, then `image-chunk OFFSET HEX` in sequential, even-sized blocks up to 240 bytes, then `image-end`. All use the existing MRR1 request ID envelope. The frame is exactly 180,000 bytes of little-endian RGB565 (300 × 300), with decimal standard CRC32. Firmware rejects incomplete, invalid or out-of-order transfers. It keeps the previous frame until verification completes and abandons an incomplete transfer after five seconds without data. Identical retries of the last chunk or final acknowledgement are idempotent. The host checks the final acknowledgement. The board selects Gallery after commit and keeps its most recent frame in volatile PSRAM.
