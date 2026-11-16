# Firmware Trust and Recovery

Current transition, 2026-10-31: owner selects Gemini after the final Muse discovery failure. A successful explicit full-chip erase clears retired Muse device flash/NVS before Face Lab 0.8.0's different layout is uploaded and hash-verified. No eFuse or SD operation occurs. The private host SDK token/recovery files remain optional; no new credential-bearing flash dump is made. The board transfers indicated, tap-triggered audio over USB to the Mac; provider credentials stay on the Mac. Google receives speech after a physically triggered voice turn. See [voice data/limits](GEMINI-VOICE.md). The factory backup remains unused optional recovery material.

2026-10-29: the owner asked whether the preinstalled system is safe and whether to install our own.

## What is established

The device runs firmware on an ESP32-S3, including an RTOS and drivers; we choose the application image. The original running firmware identified itself as Waveshare's Brookesia demo, version `v1.0.1-9-gec7380d`, built with ESP-IDF5.5.4. The manufacturer publishes source and a complete recovery image. Identity strings and published source do not certify the flashed binary or the security of every enabled feature.

The complete original flash was preserved privately before our first upload. Its full-image hash differs from the published recovery-image hash; flash contains mutable per-device settings, so that comparison alone neither authenticates all code nor establishes malicious modification. No forensic or comprehensive security audit was performed. Do not label the factory demo malicious or certified secure from this evidence.

The board was subsequently replaced with our compiled USB/memory diagnostic. Our custom Face Lab now builds on selected display drivers. The diagnostic enables no network/audio. Face Lab 0.4.0 permits an explicit short generated speaker tone, now heard by the owner. The 0.6.0 code adds an explicit four-second transient microphone level test, optionally armed for one owner tap with a visible indicator and aggregate-only results; no raw audio is saved or sent. Networking stays disabled. Face Lab 0.2.0 offers on-demand raw SD metadata reads; it never mounts or accesses personal files. Check PROJECT-STATUS.md for which image was actually uploaded and observed, rather than assuming the factory demo is still running.

## Decision

Use source-controlled project firmware as the development direction, with small reviewed modules and pinned dependencies, while retaining recovery options. Reuse documented vendor/chip drivers instead of rewriting power, display and audio initialization from guesses. Custom source is easier for us to inspect and restrict, but does not automatically make all dependencies or future features secure. This folder currently has no Git repository; ignore rules and a clear source/dependency structure are in place, but no commit history should be claimed.

Keep prototype USB controls local. Before adding internet/AI: authenticate the backend, validate TLS certificates, keep provider keys on the host, bound input/output and costs, and make recording/upload behavior explicit. Later network management and firmware updates need a separate authenticated design. Do not burn eFuses or turn on irreversible secure-boot/encryption settings during initial board validation.

## Recovery boundary

The verified private backup is in `private/backups/` with its local SHA-256 sidecar. It can contain credentials; do not copy it to the vault or share it. Never overwrite the original backup with a new development image. Recovery uses the correct non-C board, flash size and matching complete image. Review the existing backup or manufacturer recovery instructions before a restore; no restore or full-chip erase is needed for this display milestone.

Sources: [manufacturer firmware delivery guide](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/e4344e70c2fa78a13e8a06566507f1ba8af6672a/firmware/README.md), retained factory boot observations, private-backup size/hash check, and current application sources. See [architecture](ARCHITECTURE.md) and [device protocol](../protocol/README.md).

## Backup location and meaning

The original16 MiB image is `./private/backups/waveshare-factory-2026-10-29.bin`; its size/hash sidecar is the adjacent `.json` file. Both are local mode 0600 files, not an uploaded cloud backup. The directory is ignored by version-control rules. Our application does not read, execute or build from this image. It is optional recovery material, retained rather than deleted because the owner questioned its need but did not explicitly request deletion.

Our development direction is a new application using documented hardware drivers and selected SDKs. We are not modifying the factory-demo application. “No Wi-Fi/audio/SD access” described the earlier diagnostic program's enabled behavior, not missing board hardware. Current firmware capabilities are separately recorded in PROJECT-STATUS.md.

## API host and caption boundary — 2026-10-30

Current Face Lab 0.7.0 adds only a bounded volatile host-caption preview. The board holds no Gemini/provider key and opens no Wi-Fi session; the laptop makes the native Gemini request, returns full text to the browser and sends a short ASCII preview over USB. The owner confirms it is readable; expiry is observed at 60.54 seconds. Caption text is not interpreted as a command, echoed in status or written to NVS/SD. No raw microphone data was sent to an AI provider in this milestone.

Before0.7.0 compilation, verified 0.6.0 compiled artifacts were saved locally at `./private/backups/face-lab-0.6.0/`, with flash addresses/sizes/hashes in manifest.json. This is a compiled application recovery set, not a complete NVS/full-flash backup. The original factory image remains separately unchanged at the path above. Neither recovery set is copied into the vault or used by the running application.

Provider configuration/credentials remain in ignored mode 0600 files under private/host/. This is local plaintext storage, not Keychain encryption. Host certificate validation is enabled through a pinned CA bundle. Authentication, role/body/Origin checks and persistent limits are implemented, but the local HTTP server is not a production LAN deployment. Google Free-tier status is owner-attested and was not independently verified from billing APIs.


## Muse voice evaluation — 2026-10-30

The owner now chose a separate pinned Muse SDK image for live-voice testing, rather than the factory demo. It is built/flashed and its replacement SDK token is stored through redacted serial provisioning, not embedded in the binary. Phone pairing and physical voice acceptance remain pending. Credentials in device NVS are plaintext in this evaluation; they must not be exported into notes, raw console logs or flash dumps. OTA, LAN tunnel, remote BLE commands, Secure Boot, flash encryption, eFuse auth and NVS encryption are disabled. No fuse-writing feature is enabled by the reviewed generated configuration.

Face Lab 0.7 compiled recovery files remain in private/backups/face-lab-0.7.0/ with address/size/hash manifest. They are not a full NVS backup. Muse's partition/app offsets differ from Face Lab; do not mix layouts. Returning to our firmware is not proof that old Muse account/Wi-Fi credentials were erased or revoked. Details: firmware/muse-evaluation/README.md.
