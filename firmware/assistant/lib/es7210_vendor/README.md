# ES7210 driver provenance

Espressif Systems, Apache-2.0, headers preserved. Source: esp-bsp commit `5ef4592e48f1e7d9c0be03c71589aa6eeb6b7df1`, components/es7210 (component1.0.1~1, IDF>=4.4,<6). Exact driver/header/register/component sources and URLs are in the project source manifest.

Local changes: include stdlib/Arduino HAL explicitly; replace the register-write transport with Arduino i2cWrite on the already initialized shared Wire0 bus. No bus init/delete. Add es7210_stop_codec using the attributed Espressif esp_codec_dev es7210_stop sequence retained as espressif-codec-dev-es7210.c.txt (URL/commit/hash in manifest). Return the first error while attempting every shutdown write. Delete frees the handle only.

Application uses the documented16kHz/256× coefficient, four 16-bit TDM slots,24dB PGA,0dB digital volume,2.87V bias. Bias/analog settings follow Espressif codec-dev; slots/pins follow the exact Waveshare non-C maintained BSP. All settings/measurements are distinguished in HARDWARE-INVENTORY.md. No raw audio files or upstream audio examples are included in our application.

0.5.1 correction: align analog/global/pair power registers with the retained maintained codec-dev es7210_start/mic_select sequence:0x40=0x43,0x06=0x00,0x4B=0x00,0x4C=0x00. The original0xC3/0x04/0x0F/0x0F sequence returned noise-floor samples in missed speech windows.0.6.0 includes the maintained power sequence plus owner-triggered timing and verifies sound response; these combined changes do not isolate a causal defect in the original driver. Keep clock/gain/bias/TDM unchanged to bound the comparison; acoustic verification is recorded in PROJECT-STATUS.md. Exact upstream snapshots remain unchanged.
