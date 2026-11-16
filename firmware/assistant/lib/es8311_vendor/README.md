# ES8311 driver provenance

Espressif Systems, Apache-2.0 (copyright/SPDX headers preserved). Copied from Waveshare commit `e4344e70c2fa78a13e8a06566507f1ba8af6672a`, `examples/arduino/08_ES8311/`: es8311.c, es8311.h, es8311_reg.h. Exact upstream bytes and URLs are in the project source manifest under `assets/sources/2026-10-29/`.

Local changes: qualify FreeRTOS headers and include the task declaration for Arduino2; reject short successful I2C register reads; guard failed calloc before dereference. The existing Wire bus is reused through Arduino HAL port0. Delete releases only the driver handle, never the shared bus. No manufacturer music sample is included.

This small driver is needed for the actual ES8311 clock/format/DAC initialization. The Arduino3 I2S example is adapted to the already installed IDF4 TX-only I2S API in our separate audio_output module. No ES7210 microphone capture is enabled; ES8311's general initialization also sets its internal ADC registers, but no RX data is routed/read.
