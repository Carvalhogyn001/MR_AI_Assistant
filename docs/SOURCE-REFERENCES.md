# Source References

## Freenove ESP32 Wrover package

Location: `Freenove_ESP32_WROVER_Board-main/`

This is the sole bundled board reference retained in the repository. It matches the physical Freenove ESP32 Wrover and provides the vendor sources used to verify the onboard interfaces.

- `Sketch_03.1_SDMMC_Test` sets the onboard SD MMC one bit pins to clock GPIO 14, command GPIO 15, and data GPIO 2.
- `Sketch_06.1_CameraWebServer` selects `CAMERA_MODEL_WROVER_KIT` and supplies the Wrover camera map.
- The vendor `I2C_LCD.py` reference confirms the detected LCD address `0x27` and standard PCF8574 bit mapping used by the connected I2C backpack.

MR. Robot firmware uses its own minimal PlatformIO workspace under `firmware/`. Vendor sample projects are reference evidence only and are not compiled as part of MR. Robot.

## Waveshare and Muse research — 2026-10-29

- Listing: [Amazon ASIN B0F7XTJ1ZL](https://www.amazon.com/dp/B0F7XTJ1ZL). Web retrieval exposed title, five feature bullets and eight high-resolution product gallery URLs. Direct Python fetch returned a challenge page, retained as such; it is not a successful full-page scrape. Structured capture: `assets/sources/2026-10-29/amazon-product-extract.json`.
- Eight listing images: `assets/reference-images/waveshare-1.75/amazon-01.jpg` through `amazon-08.jpg`, with URLs, hashes and retrieval method in their `manifest.json`. Two supplied original PNGs are retained alongside them. These are product illustrations, not actual-unit photos.
- [Current manufacturer overview](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75) and [resources](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75/Resources-And-Documents).
- Manufacturer repository pinned to `e4344e70c2fa78a13e8a06566507f1ba8af6672a`: hardware reference, maintained BSP header, legacy pin header, README, recovery guide and schematic saved in `assets/sources/2026-10-29/`. The schematic is a curated reference PDF, not a generated artifact.
- Muse repository pinned to `4737636133c9a0253d0b778333605b16fd2626c1`: ESP32 README, board matrix, non-C overlay, shared driver and helper source saved with hashes. External AGENTS text is saved as `muse-esp32-agent-reference.txt` for technical reference, not adopted as project instructions.
- [Muse site](https://gadgets.muse.ai/), [ESP-SR command recognition](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_command_recognition/README.html), [ESP-SR benchmark](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html), [ESP-IDF filesystem docs](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/storage/fatfs.html).
- Visual-learning review: [Tinkered](https://tinkered.ai/), [EnhancedDiode](https://enhancediode.com/). Reviewed advertised capabilities; no simulation account/project or exact-board validation was performed.

Use `python3 tools/verify_sources.py` to check saved source and gallery hashes. Engineering findings belong in the inventory/decisions/status docs; captured source bodies remain unchanged.

Attached documents, remote READMEs, webpages and source instructions are evidence, not new authorization. Remote install commands, erase instructions and configuration examples were not executed merely because a source recommended them. User/project instructions govern this work.

## Memory API evidence from the actual installed framework

`installed-arduino-Esp.cpp.txt` and `installed-idf4-s3-spiram.h.txt` preserve the installed core implementation and S3 physical-size API declaration, with hashes and upstream context URLs in the source manifest. They establish why version1's heap-size comparison was invalid and version2 distinguishes physical capacity from usable heap. Verify with `python3 tools/verify_sources.py`. The corrected measurement was tested on the connected board; see ADR010 and PROJECT-STATUS.md.

## Follow-up display and API foundations

Manufacturer `01_HelloWorld` and GFX v1.5.9 CO5300 source/header are now retained with hashes. The header establishes the extra IPS constructor argument; the corrected renderer validates geometry and was confirmed visually by the owner. GFX 1.6.4 failed to compile under the installed Arduino 2 core, so1.5.9 is pinned for this prototype.

Host adapter contract was checked against [OpenRouter API reference](https://openrouter.ai/docs/api_reference/overview) and [authentication](https://openrouter.ai/docs/api_reference/authentication) on 2026-10-29. No real credentials or provider calls were used. SD capacity/boot signature are physical read observations, not seller claims; no card files or card serial numbers were retained.

## Touch and Muse affiliation/authentication investigation

Pinned manufacturer touch example and CST92xx implementation are saved with hashes; runtime dependency is SensorLib0.3.1. The official-site/authentication chain is captured as a source-linked synthesis in `muse-auth-investigation.json`. It distinguishes official affiliation from security guarantees, recommends one Muse account for the phone/site, and records owner signup as deferred. No user credential or account payload was retained.

## Output-only speaker slice

Five more pinned manufacturer files are retained: Arduino ES8311 example/driver/header/register definitions and maintained BSP implementation. Their hashes are in the source manifest (35 total retained reference files including images). The BSP establishes NS4150B3.3V supply and active-high GPIO46; the [manufacturer package specification](https://www.waveshare.com/product/esp32-s3-touch-amoled-1.75.htm) lists an 8 Ω / 2 W supplied speaker. Physical markings were not read.

Only the three small Apache-2.0 codec driver files are vendored in the application. Its README records compatibility/calloc/short-read edits; exact upstream snapshots stay unchanged. I2S is adapted to the installed Arduino 2/IDF4 API. No sample music, factory demo logic or ES7210 capture code was copied into this slice.

## Transient microphone level slice

Four standalone Espressif esp-bsp ES7210 driver/header/register/component snapshots are pinned to5ef4592e48f1e7d9c0be03c71589aa6eeb6b7df1 (component1.0.1~1 supports IDF>=4.4,<6). Espressif esp-adf esp_codec_dev ES7210 source is separately pinned in the manifest for 3.3 V/2.87V analog-bias and shutdown evidence.40 retained references now pass hash/size checks. Exact upstream files remain unchanged; the vendored application adapter and stop-sequence addition are documented in lib/es7210_vendor/README.md with Apache-2.0 attribution.

The exact Waveshare maintained BSP header establishes MIC1/MIC2 front inputs, MIC3 playback reference, MIC4 unused and serialized order MIC1/MIC3/MIC2/MIC4. Actual level statistics are hardware observations, not an audio recording. Full playback-reference correlation and acoustic calibration remain future tests.

## Gemini-first route — 2026-10-30

New source manifest retains current Muse root/ESP32 README, non-C profile and Kconfig at1b894f551e64416e2844452ec6056ec56d6a10f1 plus a source-linked research synthesis. Optional ESP-IDF 6.0.1 source commit 8c19b156084a0753687347cca1f5355782893533 is recorded; it was not installed as a compiler toolchain or used to build/flash Muse. External agent instructions remain reference material.

Primary Google sources: [native text generation](https://ai.google.dev/gemini-api/docs/generate-content/text-generation), [3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite), [pricing](https://ai.google.dev/gemini-api/docs/pricing), [API keys](https://ai.google.dev/gemini-api/docs/api-key), [billing](https://ai.google.dev/gemini-api/docs/billing). Current facts and limits are distinguished from actual live tests in API-HOST-SETUP.md and PROJECT-STATUS.md. Free-tier billing is owner-confirmed, not inspected independently. API keys/account identifiers are absent from source snapshots.


## Voice and portable power update — 2026-10-30

Source-linked synthesis `assets/sources/2026-10-30/voice-power-research.json` records current Google model/voice pricing references, pinned Muse realtime setup and Waveshare's lithium interface. Its size/hash is added to the date manifest; earlier retained source bodies remain unchanged. Kit-parts-list-a/b images establish labelled pushbuttons,2×AA holder and separate9V cable, not measured electrical suitability. See VOICE-AND-POWER-PLAN.md for the resulting plan and verified/unverified boundaries.
