# Waveshare 1.75 USB and memory baseline

First slice only. No Wi-Fi, Bluetooth, SD mount, display, codec, GPIO output or battery configuration. It contains no credentials. The panel may be blank while this firmware runs.

Board evidence and USB pins are recorded in `../../docs/HARDWARE-INVENTORY.md`. The generic DevKitC recipe is only a compiler base; it does not identify the physical board. DIO flash follows the manufacturer recovery command; octal PSRAM and 16 MB flash follow the non-C model specification. Arduino core 2.0.17 is sufficient for this diagnostic; Muse needs its own ESP-IDF 6.0.1 project. Do not add Muse to this PlatformIO project.

## Build

From the MR. Robot root:

```sh
pio run -d firmware/waveshare-bringup
```

Hardware acceptance, after identifying the physical board and backing up its factory flash:

```sh
PLATFORMIO_UPLOAD_PORT=PORT pio run -d firmware/waveshare-bringup -t upload
pio device monitor -p PORT -b 115200
```

`PORT` must be the newly detected ESP32-S3 device, not a guessed example. Do not use `erase_flash`. Upload overwrites the running firmware and partition table.

Expected actual serial values:

```text
MR_ROBOT_WAVESHARE_BASELINE version=2
CHIP=ESP32-S3 ...
FLASH_BYTES=16777216 expected=16777216
PSRAM_PHYSICAL_BYTES=8388608 expected=8388608
PSRAM_HEAP_BYTES=...
PSRAM_BUFFER_CHECK=PASS bytes=65536
BASELINE=PASS
HEARTBEAT baseline=PASS ...
```

Send lowercase `i` to repeat the report. A heartbeat alone proves the application runs, not the physical board model. A mismatch stops further peripheral work until documented. The buffer check covers 64 KiB, not all PSRAM. Record results in `../../docs/PROJECT-STATUS.md`; build success alone does not verify hardware.

Version2 uses IDF4 `esp_spiram_get_size()` for physical capacity. Arduino2.0.17 `ESP.getPsramSize()` reports usable heap and can be slightly smaller (initial observed 8,386,295 bytes). The first live version1 falsely failed the capacity comparison despite its buffer passing; this was reproduced and corrected. `sdk_revision` is the legacy SDK field; detailed silicon revision comes from esptool.
