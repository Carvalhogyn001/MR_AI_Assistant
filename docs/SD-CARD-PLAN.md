# New 128 GB microSD Plan

2026-10-29: the owner reports a new 128 GB card. Brand/model remain unknown. Subsequent Face Lab 0.2.0 raw reads reported **124,383,133,696 bytes** (124.38 decimal GB / 115.84 GiB), an **exFAT boot signature**, and card_error=0. No filesystem was mounted, no files listed and no writes/format performed. Reported capacity and a signature do not establish full-block reliability or filesystem integrity. Prior cards measured near 64 MB and 1 GB; do not carry their results forward or keep the old unsupported 256 GB claim as current equipment.

## Compatibility

The Waveshare has an onboard TF/microSD slot using SDMMC **CMD1, CLK2, D0=3** in 1-bit mode. GPIO41 is D3/CS, not card detect. Do not use the Freenove's pin map or add an SPI SD adapter.

A nominal 128 GB card is normally SDXC and commonly ships exFAT; that expectation does not establish this card's actual format. The pinned manufacturer factory package requires **FAT/FAT32 and explicitly excludes exFAT/NTFS**. ESP-IDF exFAT support depends on version and configuration, so do not assume the installed Arduino or Muse build can mount it. FAT32 may be usable on a larger card, but the exact card/firmware combination must be tested; no maximum supported card capacity is established here.

128 decimal GB is about 119.2 GiB before filesystem overhead. A display using binary units is not alone evidence of a fake card. A filesystem reporting 128 GB also does not prove every block is real.

## Sequence

1. Read the physical label/model and inspect capacity/filesystem through a Mac card reader with read-only commands. Identify the external disk by capacity and device before doing anything to it. Do not display file names/content from an existing personal card in shared logs.
2. If data is present, preserve it. The owner has now authorized formatting and testing this new empty card when needed (see authorization below). Identify the exact card/device before any destructive step; do not transfer that authorization to another disk.
3. After USB/memory and board support verification, build an SD slice with automatic formatting disabled. Mount **read-only** where supported; otherwise make no filesystem writes. Read card type/raw size, partition/filesystem metadata and free space. A mount failure must not trigger format-on-failure.
4. For write validation, use an explicitly selected project directory and fresh filenames. Write a small generated file, close, reopen and compare SHA-256, then repeat after reboot. Record throughput and mount failures.
5. Before trusting large media storage, plan an owner-approved full capacity write/read integrity test on an empty/backed-up card. A small-file test alone cannot prove 128 GB capacity. Never run a destructive or bulk-write test against an unidentified disk.

## Planned content after acceptance

```text
/mr-robot/assets/       curated faces, UI assets, short sounds
/mr-robot/notes/        explicitly saved notes
/mr-robot/recordings/   optional user-started recordings with retention limits
/mr-robot/diagnostics/ bounded non-sensitive diagnostic summaries
```

The card is not RAM, a model accelerator or credential storage. Keep recordings off by default until retention is chosen. Do not auto-index personal files.

Sources: [manufacturer hardware reference](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/e4344e70c2fa78a13e8a06566507f1ba8af6672a/HARDWARE_REFERENCE.md), [manufacturer firmware delivery guide](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/e4344e70c2fa78a13e8a06566507f1ba8af6672a/firmware/README.md), [ESP-IDF filesystem documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/storage/fatfs.html). The last link is version-dependent; inspect the version actually used before enabling options.

## Owner authorization —2026-10-29 follow-up

Owner states the new card is empty and explicitly authorizes formatting/initialization when needed for this project. This replaces the earlier lack of formatting authorization; a second permission request is not required for this identified card. Do not apply that authorization to a Mac system disk, another card or an unidentified device. Current raw inspection does not need formatting; choose the filesystem before the first write/mount slice. No formatting has been performed yet.
