# Voice and text providers

Updated 2026-11-14. Connect the Waveshare to the Mac with the USB data cable. In Control Room, open **Providers**, choose a provider and model, then click **Save & apply**. The manager stops its current voice session if needed. Switching between Muse and Face Lab restarts the ESP32 automatically. Switching between Ollama and Gemini uses the same Face Lab firmware and needs no ESP32 restart. The header shows the saved provider and the firmware the board actually reports. When USB is unplugged, settings can still be saved on the Mac. Reconnect USB and click **Save & apply** to switch the board.

| Provider | Available in Control Room | Acceptance |
| --- | --- | --- |
| Gemini | Text and spoken conversations. With the manager running and one compatible Waveshare connected over USB, press and release the green button or say “Hey Mr. Robot.” The Mac detects the wake phrase locally and sends a question after activation. | Owner verified both automatic triggers. Prior two-turn test verified that Gemini remembered the first question. |
| Ollama | Local typed chat with question and reply captions. With Gemma 4 12B, the green button captures a spoken question and shows the text reply. [Ollama device guide](OLLAMA-DEVICE.md). | `gemma4:12b` returned “Local model ready.” through Control Room and the display acknowledged the caption. `gemma4:e4b` and `qwen3.6:latest` were listed by the running Ollama instance. |
| Meta Muse | Typed requests from Control Room go over USB through the paired board. Hold the green switch and release for a voice note or tap briefly for a live conversation. | Verified typed reply, preserved pairing across switches, and an owner-confirmed audible reply after a green-button tap. |

## Muse evaluation

The two firmware images share the boot selection data. Muse and Face Lab each use their own NVS area. The app slot change uses the onboard bootloader and preserves the existing Muse account and network settings. Ollama and Gemini run through the Mac. Muse button input goes directly from the gadget to Muse over Wi-Fi. [Muse pairing guide](MUSE-PAIRING.md) · [Firmware layout](../firmware/muse-evaluation/README.md)

Reproduce the SDK check without flashing or contacting Muse:

```sh
CC='cc -Wno-deprecated-declarations' python3 external/muse-gadget-sdk/esp32/tests/test_muse_voice_call.py
```

## Local voice evaluation

Face Lab 0.9.7 sends bounded audio directly to Gemma 4 12B for a text answer. For spoken output, test a standalone local text-to-speech engine before integrating playback. Measure microphone-to-reply latency and verify contextual follow-ups before linking it to automatic voice. Use `ollama list` to find installed chat models. [Ollama chat API](https://docs.ollama.com/api/chat)
