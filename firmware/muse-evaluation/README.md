# Muse Voice Evaluation

Current status, 2026-11-14: Muse and Face Lab are installed in separate app slots. Control Room switches the resident images with **Providers → Save & apply**. The owner heard the reply from a green-button Muse call. [Pairing guide](../../docs/MUSE-PAIRING.md)

## Shared boot layout

The Muse bootloader reads its table at `0x10000`. Muse stays at `0x20000` and keeps its paired NVS at `0x11000`. Face Lab sits at `0x420000`. Its Arduino libraries read the [Face Lab partition map](face-lab-partitions.csv) flashed at `0x8000`, with separate NVS at `0x9000` and shared OTA selection data at `0x1D000`. The existing bootloader and Muse table were retained. [The boot-selection patch](dual-boot.patch) and Face Lab console command use the SDK's OTA validation before switching.

For a rebuild on this layout, build Muse with `tools/muse.py build` and Face Lab with `pio run -d firmware/assistant`. Use the pinned IDF's `components/partition_table/gen_esp32part.py --offset 0x8000` to turn the Face Lab CSV into a binary table. Sign Face Lab with `python -m espsecure sign-data --version 2 --keyfile external/muse-gadget-sdk/esp32/dev_signing_key.pem --output FACE_SIGNED FACE_BIN` and verify the signature with `espsecure verify-signature`. On the already configured board, write the changed app to its slot without flashing OTA initialization or erasing NVS. A normal Face Lab PlatformIO upload uses the standalone layout and overwrites the shared setup.

Separate ESP-IDF application for the **Waveshare ESP32-S3-Touch-AMOLED-1.75 non-C**, not an Arduino Face Lab provider plugin. Owner selected Muse again on 2026-10-30 to prioritize spoken interaction. SDK pin: `1b894f551e64416e2844452ec6056ec56d6a10f1`; ESP-IDF v6.0.1: `8c19b156084a0753687347cca1f5355782893533`.

From the project root:

```sh
~/.platformio/penv/bin/python tools/muse.py build
~/.platformio/penv/bin/python tools/muse.py flash --port PORT
~/.platformio/penv/bin/python tools/muse.py provision --port PORT
~/.platformio/penv/bin/python tools/muse.py status --port PORT
~/.platformio/penv/bin/python tools/muse.py watch --port PORT --seconds 180
```

The compiler/runtime is isolated in ignored `external/esp-idf-tools/`. On this Mac, add `external/esp-idf-tools/python312/bin` to PATH before invoking the wrapper to select the restored Python 3.12 runtime. Build files are in `external/muse-gadget-sdk/esp32/build-mr-robot-s3n/`. The wrapper checks source pins, applies [the IO16 patch](io16-talk.patch), and validates the non-C target, voice settings and empty compiled credentials. The original component lock is retained in `dependencies.lock.reference`. SDK defaults, Muse UI, non-C board and the local overlay load in that order.

Save a **replacement** SDK token as `MUSE_GADGET_SDK_TOKEN=...` in ignored root `.env` (mode 0600). Never source that file as a shell script, put the token in command arguments, or paste it into chat. Provisioning accepts the documented token shape, asks the running board for its exact identity, sends once, drops raw serial echoes/logs, and prints only its acknowledgement. The token is stored in device NVS, not compiled into the image. NVS is plaintext here; no eFuse key is created. Do not distribute a post-provisioning flash dump.

The intentionally token-free build prints an SDK warning. USB provisioning after flash completes token setup. Phone account/Wi-Fi enrollment remains separate.

Live voice is experimental. A short press on the green IO16 switch attempts a call, and a second press hangs up. Hold the switch to speak, then release it to send a voice note with a text reply. BOOT confirms pairing. The live call allows 30 seconds idle and 180 seconds total. OTA, LAN tunnelling and remote BLE commands are disabled. SDK signing uses its development key without enabling Secure Boot.

The Muse image fits its 4 MiB slot with 48% free. Both app flash hashes verified, both directions of switching worked, and the existing Muse pairing survived. USB verified the live call and the owner heard its reply.

The IO16 rebuild resolved five public component updates within the SDK's declared version ranges: LV decoder 0.5.1, FreeType 2.15.0, libpng 1.6.59~1, USB 1.6.1 and zlib 1.4.0. The generated lock is in the SDK build checkout.

Recovery material for our independent firmware is in ignored `private/backups/face-lab-0.7.0/`, with four compiled artifacts and a manifest of addresses, sizes and hashes. This does not include NVS. Muse uses a different partition table offset (0x10000) and app offset (0x20000); Face Lab's partition table/app offsets are 0x8000/0x10000. Never mix the two flash layouts. Returning to Face Lab does not erase all Muse credentials automatically; account unpairing/targeted credential cleanup must be considered separately.

See [voice/power plan](../../docs/VOICE-AND-POWER-PLAN.md), [Muse research](../../docs/MUSE-EVALUATION.md) and [roadmap](../../docs/ROADMAP.md). Keep USB power for now; autonomous battery operation remains the goal after conversation works.


Host suite: run `external/esp-idf-tools/python_env/idf6.0_py3.12_env/bin/python tools/test_muse_upstream.py` from the project root. It supplies pinned FreeInk test sources, CMake/Ninja and Darwin-compatible host linker flags, retaining ASan/UBSan/assertions. Optional video/PPK2/host-PSA prerequisites may skip; report the actual result/skip count. This test runner does not operate physical hardware.

The USB helper uses the SDK console's asserted modem lines and clears POSIX HUPCL. This avoids repeated USB-open resets; actual separate opens retained Wi-Fi connected and advanced uptime82→85 seconds. Public status is redacted. The bounded `watch` command queries status every two seconds and prints only allowlisted state changes/physical pairing confirmation; no raw logs, credential writes or simulated button presses. `standalone_account_credential_configured` is separate from the phone's `paired` flag. See [pairing/discovery checks](../../docs/MUSE-PAIRING.md). Reflashing Face Lab should consider old Muse NVS credentials separately, as above.
