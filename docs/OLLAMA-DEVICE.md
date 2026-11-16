# Ollama on the round display

Face Lab **0.10.0** receives a 300 × 300 RGB565 preview of Z-Image Turbo output on the Gallery screen. The manager keeps feeding the full 512 × 512 PNG to Conversation, where the browser saves it locally. The host's pinned Pillow dependency handles the resize and conversion. The existing serial owner performs the transfer for both typed and voice prompts. See the [November 14 audit](SYSTEM-AUDIT-2026-11-14.md) for the separately verified paths.


Choose **Providers → Ollama · local**, pick a model from the menu, and click **Save & apply**. Use **Other installed model** to enter another tag from `ollama list`. Keep the Waveshare connected by USB. Ollama runs on the Mac. Face Lab shows typed chat replies as captions and shows the Thinking indicator while the model runs.

| Model | Input and result |
| --- | --- |
| `gemma4:12b` | Type a question or tap the green button, wait for **LISTENING**, then speak. The answer appears on the ESP32. The OpenAI-compatible audio request uses `reasoning_effort: none`, and local capture allows about one second of silence between sentences. |
| `gemma4:e4b` | Typed chat and text replies on the round display. |
| `qwen3.6:latest` | Typed chat or a green-button question. Gemma 4 12B transcribes the spoken question locally before Qwen answers in text. A direct typed test answered the Proxima Centauri question after a 14-second cold load. |
| `x/z-image-turbo:latest` | Type an image description or say “Hey Mr. Robot” or tap the green button, then speak when **LISTENING** appears. Gemma 4 12B transcribes the speech locally. Z-Image takes that text and makes a PNG in **Conversation**. Face Lab 0.10.0 shows progress and can display the generated preview in Gallery. |

The active Ollama 0.40.16 server explicitly rejects image generation. Control Room starts the official Ollama **0.32.5** runtime on loopback port 11435 for Z-Image only. Its model directory contains the Z-Image manifest and reuses existing weight blobs. The original Ollama service continues serving chat on port 11434. The runtime archive from the [official release](https://github.com/ollama/ollama/releases/tag/v0.32.5) was checked against SHA-256 `5789dd037a86adb328c72c11fc45e6c558452d07e5b50814a8bdb7b0fbdbcd81` and extracted to ignored `private/ollama-image/`.

On the 32 GB M1 Pro, a 512 × 512, eight-step image took 49 seconds in a direct test and 107 seconds in the voice flow. Images are retained in manager memory for browser display. The owner verified a spoken prompt reached Conversation. Qwen answered a typed question through Control Room and the ESP32 acknowledged the caption. Its physical voice route remains to be checked.
