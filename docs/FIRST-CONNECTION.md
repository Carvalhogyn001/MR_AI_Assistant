# First Connection — Beginner Guide

Goal: identify the new board, preserve the factory demonstration, then verify USB, flash and PSRAM. No loose wiring is needed for this step.



Speaker reference: annotated SPK/BAT guide. Editable SVGs and Obsidian drawings are in `docs/visuals/`.

## What you do

1. Put the new round board on a dry, nonconductive surface. Leave the Freenove, loose audio board, LCD and sensors disconnected.
2. Leave battery and speaker wiring as supplied. Do not add an unknown battery. Leave the new SD card out until we inspect it separately.
3. Connect a **USB data cable** from the Mac to the board's **USB-C** port. A charge-only cable can light a display without exposing a serial port. If using a hub, it must carry USB data.
4. Before any upload, observe the factory screen: does it boot, does touch work, is there already a speaker/battery? Record the physical label/variant and the behavior. Serial chip detection proves the chip family, not the complete board model.
5. Leave the device connected. The coding agent can identify the port, read chip/flash information, create a private flash backup and upload the compiled diagnostic. Credentials, account sign-in and physical connection still need you.

Do not insert jumpers into the 8-pin header for this milestone. USB supplies both power and data. The board already connects its display, touch and audio internally.

## What the agent does after the board appears

```sh
pio device list
```

Use the new USB port, compare its USB identity to the physical board, and read current serial output first when available. Before upload, use the installed esptool version to read chip identity and actual flash ID. With the existing PlatformIO esptool 4.11 and **the actual PORT**, the commands are:

```sh
~/.platformio/penv/bin/python ~/.platformio/packages/tool-esptoolpy/esptool.py -c esp32s3 -p PORT chip_id
~/.platformio/penv/bin/python ~/.platformio/packages/tool-esptoolpy/esptool.py -c esp32s3 -p PORT flash_id
```

Only after 16 MB is confirmed, save a full backup in ignored private storage. This may include factory settings or credentials: never attach it to the vault or commit it.

```sh
mkdir -p private/backups
~/.platformio/penv/bin/python ~/.platformio/packages/tool-esptoolpy/esptool.py -c esp32s3 -p PORT read_flash 0x0 0x1000000 private/backups/waveshare-factory-2026-10-29.bin
shasum -a 256 private/backups/waveshare-factory-2026-10-29.bin
```

Choose a fresh backup filename when one already exists. Check file size is 16,777,216 bytes and record the digest privately. Do not restore a dump to another device. Stop if secure-boot/encryption state or flash layout prevents a normal read; do not burn eFuses or erase the device to bypass it.

The prepared diagnostic build/upload/monitor commands are in [its README](../firmware/waveshare-bringup/README.md). A successful hardware result requires actual `FLASH_BYTES=16777216`, `PSRAM_PHYSICAL_BYTES=8388608`, `PSRAM_BUFFER_CHECK=PASS`, `BASELINE=PASS`, plus ongoing heartbeats. Do not label expected text as observed output.

After flash, USB can re-enumerate under a new port. Re-list ports. If connection fails, first check cable/data/hub, close other serial monitors and observe the board. Follow the exact board's recovery procedure; do not assume its PWR button is RESET. Vendor documentation describes BOOT-held USB reconnection for entering download mode. Avoid repeated blind uploads.

## Visual tools for future steps

| Tool | Best use here | Verified limit |
| - | - | - |
| Obsidian Canvas / Excalidraw | Editable project plan, real-board photos with numbered callouts, one verified wiring step per drawing | Diagrams do not simulate electrical behavior. An editable setup drawing and architecture canvas are supplied. |
| [Tinkered](https://tinkered.ai/) | Learning breadboards and generic ESP32 circuits | Advertises ESP32 support and a free entry point. Exact 1.75 board, CO5300, PMIC, audio chain and full Muse compatibility not established. |
| [EnhancedDiode](https://enhancediode.com/) | Breadboard layout and basic circuit concepts | Site advertises SPICE and ATmega328P code simulation; ESP32 picture does not establish ESP32-S3 firmware simulation. Some export features are marked coming soon. |

Recommended method: annotated photos of **your actual board**, a small pin/voltage table checked against the schematic, and a matching observable test. For the present step, a USB connection drawing is sufficient. For future external wiring, make a breadboard illustration only after model, voltage and orientation are verified. Simulation is useful for learning, but it cannot establish this physical board's power, audio or SD compatibility.
