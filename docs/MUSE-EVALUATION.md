# Muse Evaluation

Researched 2026-10-29. SDK revision: `4737636133c9a0253d0b778333605b16fd2626c1`. Source snapshots and hashes: `assets/sources/2026-10-29/manifest.json`.

## Findings

- The public `facebookincubator/muse-gadget-sdk` is a gadget client SDK. The ESP32 pairs through a phone using BLE, joins Wi-Fi and connects to remote infrastructure. It does not contain a local Muse language-model runtime or downloadable model weights.
- Both Waveshare **1.75** and **1.75C** are listed. This project's ASIN and illustrations match **1.75**, the 16 MB-flash / 8 MB-PSRAM variant. Physical model/memory confirmation is now recorded in PROJECT-STATUS.md. Owner subsequently accepted remote Muse as the intended evaluation path.
- Non-C overlay: `devices/sdkconfig.muse-waveshare-s3-175`; helper alias **`s3n`**. Alias **`s3` is the 1.75C**, with different pins and 32 MB flash. Do not use it for this device.
- Published support includes avatar/UI, push-to-talk, settings and images. Shared driver `board_waveshare_s3_175c.c` has a non-C conditional using reset39, touch reset40 and audio MCLK42. The shared filename does not mean the board profiles are interchangeable.
- The pinned SDK requires **ESP-IDF v6.0.1**. Existing PlatformIO Arduino tools are not a substitute. Manufacturer factory firmware uses a different IDF version; do not mix SDKs or binaries.
- Requires a USB data cable, Muse app/account and a Muse Gadgets SDK token. Account eligibility, regional availability, price and owner sign-in were not verified. Never paste tokens into chat, vault notes or tracked build defaults.
- The SDK permits building without a token, then local serial provisioning into NVS. Prefer this over embedding a token in firmware; NVS still contains a credential and must be treated as private. Provisioning console/logging must avoid exposing the token.

## Evaluation sequence

1. Confirm physical non-C board, preserve factory behavior and private full-flash backup, then pass the USB/memory baseline.
2. Install only the toolchain needed for the pinned SDK. Keep this separate from the camera workspace. No remote `curl | sh` installer is necessary.
3. Obtain a separate checkout pinned to the revision above, review its build/dependency configuration and build the **s3n** profile without a token.
4. Verify build targets `esp32s3`, overlay `CONFIG_MUSE_BOARD_WAVESHARE_S3_175=y`, 16 MB flash and octal PSRAM before flashing.
5. Flash the correct board and confirm display, touch, BOOT push-to-talk, recording and speaker playback. Do not use a 1.75C web-flasher package on this board.
6. Owner signs into Muse and creates/provisions their token privately. Confirm pairing, one conversation, disconnect/reconnect behavior and which data goes to the service.
7. Record measured RAM, response latency, panel/audio behavior and any bugs. Decide whether to customize this SDK or create an independent app with a provider-neutral transport.

Future build command, after prerequisites and source checkout exist, from upstream `esp32/`:

```sh
tools/muse/board.sh build s3n
```

That build helper is read as source evidence in this session; it has **not** been executed. Muse was not installed, built, provisioned or flashed during the initial project reset. See the current status for later updates.

## Local AI path

Do not delay board verification trying to make Muse fit in 8 MB. First validate offline voice commands with Espressif ESP-SR separately. Its documented MultiNet models recognize a limited command vocabulary in English or Chinese, not open-ended dictation or conversation. Benchmarks are from Espressif reference boards; they are not performance guarantees for our board, and must account for simultaneous UI/audio memory.

For rich local conversation, use a model on the Mac or another host and stream only bounded device inputs/outputs. A local computer model is a different deployment from on-ESP32 inference. Portuguese speech support, if desired, requires a separately verified model/provider; it is not promised by the cited English/Chinese command recognizer.

## Sources

- [Muse gadgets site](https://gadgets.muse.ai/)
- [Pinned ESP32 README](https://github.com/facebookincubator/muse-gadget-sdk/blob/4737636133c9a0253d0b778333605b16fd2626c1/esp32/README.md)
- [Pinned board helper, s3n mapping](https://github.com/facebookincubator/muse-gadget-sdk/blob/4737636133c9a0253d0b778333605b16fd2626c1/esp32/tools/muse/board.sh)
- [Pinned non-C overlay](https://github.com/facebookincubator/muse-gadget-sdk/blob/4737636133c9a0253d0b778333605b16fd2626c1/esp32/devices/sdkconfig.muse-waveshare-s3-175)
- [Offline command recognizer](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_command_recognition/README.html), [resource benchmarks](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html)

## Authentication investigation — 2026-10-29 follow-up

Muse does not need an OpenRouter key. It still needs a **Muse Gadgets SDK token** tied to the owner's Muse account, followed by phone-app pairing. Official token page states a gadget cannot pair without it. A token is a credential, even though it is different from a pay-per-request model API key. The phone provisions pairing/network state; the SDK communicates with remote Muse infrastructure using its documented encrypted session. Account access/usage limits are not established by the owner merely having the app; do not promise free/unlimited use.

Current official pages checked: [SDK tokens](https://gadgets.muse.ai/settings/sdk-tokens), [SDK token terms](https://gadgets.muse.ai/sdk-terms), [official web flasher](https://facebookincubator.github.io/muse-gadget-sdk/). No token was created, accepted, copied or provisioned by the agent. Owner was asked only whether token creation is available, never for the secret in chat. Build can precede private provisioning as documented in the pinned SDK README.

Our independent application is not derived from the factory Brookesia demo. Using Muse will reuse its SDK client/transport with an explicit framework migration or isolated evaluation; our current Arduino 2 face application is not a drop-in ESP-IDF 6 SDK build. Keep the verified face application as the working baseline while evaluating this boundary.

## Official site and account choice — revised 2026-10-30

The official SDK repository links gadgets.muse.ai; earlier affiliation evidence remains in SOURCE-REFERENCES.md. A **new project Muse account can be created/used from the laptop**, subject to normal account eligibility. It does not have to be the owner's existing personal phone account. Using one project account for token website and phone app was setup guidance, **not a tested technical requirement that the accounts must match**. The token terms also describe shared devices paired with the recipient's own Muse credentials; do not infer an undocumented binding rule.

The current SDK's documented ESP32 enrollment still uses the **Muse iOS/Android app**, Bluetooth discovery and a physical confirmation on the gadget. Laptop flashing and token entry are different steps from enrollment. No supported laptop-only enrollment flow was found in the current root/ESP32 README. This is a limitation of the documented setup path, not proof that a PC could never implement a pairing client. We have not implemented or verified such a client.

Current primary sources: [root README](https://github.com/facebookincubator/muse-gadget-sdk/blob/1b894f551e64416e2844452ec6056ec56d6a10f1/README.md), [ESP32 setup](https://github.com/facebookincubator/muse-gadget-sdk/blob/1b894f551e64416e2844452ec6056ec56d6a10f1/esp32/README.md), [token terms](https://gadgets.muse.ai/sdk-terms). New pinned snapshots/synthesis: assets/sources/2026-10-30/manifest.json.

## Owner's current direction — revised 2026-10-30

After first selecting Gemini, the owner chose Muse again and emphasized spoken commands/replies. A replacement SDK token is stored only in ignored .env and device NVS after redacted USB provisioning. The earlier token pasted into chat was treated as exposed; no value is retained here. Current source pin 1b894f551e64416e2844452ec6056ec56d6a10f1 and IDF6.0.1 are installed, built and flashed for the non-C board. Config/image hashes and exact board status pass; token provisioning is acknowledged. Phone setup, physical display and spoken conversation remain unverified.

Ordinary SDK voice notes return captions. The isolated evaluation enables experimental live voice for speech replies, with30 s idle / 180 s total bounds. It is a separate image from our Arduino Face Lab/Gemini system, whose source and 0.7.0 compiled recovery artifacts remain available. New face/provider integration is future work. OTA/LAN tunnelling/remote BLE commands and fuse-changing features are disabled. SDK/Wi-Fi credentials are absent from compiled configuration; plaintext device NVS holds provisioned credentials.

Owner will keep Mac USB power for now; Wi-Fi Muse plus an appropriately verified battery is the planned route away from the PC. No external battery is connected. Setup/build/provisioning commands and remaining acceptance: [Muse evaluation guide](../firmware/muse-evaluation/README.md), [voice/power plan](VOICE-AND-POWER-PLAN.md).


## Desktop option checked, owner chooses phone once

The signed-in desktop web Devices panel was inspected on2026-10-30: only “No devices found,” without Add Device/Developer mode controls. The SDK's tools/muse/ble_setup.html supports desktop Chrome Web Bluetooth to configure Wi-Fi and an **existing device/account token**, but does not authenticate the account or mint that token; avatar.py also describes sourcing it from phone setup. Do not treat a Gadgets SDK token as an account token or extract a web session credential. This verifies the available UI/documented path, not an impossibility claim about all future desktop clients.

After this evidence, owner chose phone once for normal enrollment. The avatar and Wi-Fi connection are now confirmed; pairing/audible voice remain pending. Phone is an enrollment tool, while the board's subsequent remote connection is over its own Wi-Fi.
