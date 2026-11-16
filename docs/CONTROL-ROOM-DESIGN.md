# Control Room interface

Updated 2026-11-14, America/Los_Angeles.

The desktop layout uses a two-column workspace with a wide transcript and a dedicated robot viewer. Conversation, Device and Providers live in the header. Device, provider and request status sit along the bottom of the work area. On narrow screens the viewer follows the chat. The transcript measures 556 px at 1440 × 900 and about 463 px at 390 × 844. The composer supports multiline input and Command+Enter or Ctrl+Enter.

The visual style uses paper and olive surfaces with a pixel face on the round hardware preview. Light is the default on fresh profiles. Dark, Light and System remain available, with existing preferences preserved in localStorage. The horizontal tabs use Left and Right, Home and End.

## Three.js viewer

Drag to orbit the robot, use Rotate for a keyboard-accessible camera step, or Reset to return to the original angle. The round front panel and blue PCB are based on the Waveshare reference and the [hardware inventory](HARDWARE-INVENTORY.md). The exploded geometry is an illustration with simplified placement and proportions.

Exploded view separates the AMOLED, capacitive touch layer, PCB, ESP32 and flash, audio path, USB-C, power management, microSD and expansion header. Click or tap a part, or use its labeled button. The viewer outlines the selection and the inspector explains its role. Firmware and microphone status still appear as live text beside the viewer.

Three.js r187, [OrbitControls](https://github.com/mrdoob/three.js/blob/r187/examples/jsm/controls/OrbitControls.js) and [RoundedBoxGeometry](https://github.com/mrdoob/three.js/blob/r187/examples/jsm/geometries/RoundedBoxGeometry.js) are served locally under the [MIT license](https://github.com/mrdoob/three.js/blob/r187/LICENSE). The circuit board uses the batching pattern from the [official instancing demo](https://threejs.org/examples/webgl_instancing_raycast.html). The [Minecraft demo](https://threejs.org/examples/webgl_geometry_minecraft.html) served as a visual reference for the block geometry. Geist and Geist Mono 1.9.2 are served locally under SIL OFL 1.1. The license texts are in `manager/vendor/`.

The scene pauses offscreen and when the tab is hidden. Reduced motion renders a still view that responds immediately to controls and state changes. When WebGL is unavailable, the CSS pixel face and status remain visible.

## Local history

Typed prompts, replies, errors and generated PNGs are stored in IndexedDB for this browser profile and origin. They render again after navigating away, refreshing or reopening the site. Clear history removes the saved messages and images. The browser keeps the last-seen image ID so the manager's cached image does not reappear after clearing history. If local storage fails, the current conversation still works in memory and the history label changes.

The history is a local transcript. The text API still sends one prompt at a time to the selected model. The manager token stays in memory and gets removed from the address bar after launch. The launcher unlocks a fresh or reloaded page, while local history is already visible to that browser profile. Provider keys remain in host-side private settings.

```sh
~/.platformio/penv/bin/python tools/manager.py -o
```

## Device and model states

The Device tab controls the USB board, face, expression, brightness and Face Lab screen. The shared status area exposes Pause voice. Sending a typed request while waiting for the wake phrase pauses wake detection for the request and resumes it afterward. The scene distinguishes wake, question capture, model thinking, image generation, reply transfer and playback. The browser receives the Gemini Live transcript reaction at turn completion and applies it only in the speaking state. The board picks up the same reaction at playback start and holds the pose while audio is playing. The animation is an illustration of these states. Status polling can lag a short turn by up to its poll interval.

Face Lab Gallery receives a smaller preview of a Z-Image PNG while the original stays in browser history. Muse text becomes available once the board is paired and its link reports Online. Device and manager status time out after ten seconds in the browser, clearing live microphone claims while retaining Pause for an active session.

## Ollama model picker

Choose **Providers → Ollama · local → Model**, then use **Save & apply**. The menu lists Gemma 4 12B, Gemma 4 E4B, Qwen 3.6 and Z-Image Turbo, with capability descriptions. Other installed model accepts a model tag from `ollama list`. Switching between Ollama models on connected Face Lab saves the host setting without reopening USB and restores an enabled wake mode. Z-Image changes the composer to Generate image.

## Verification

Run `node manager/tests/app.test.cjs`. Chrome verified the revised build at 1440, 1024, 768, 390 and 320 px. Checks covered the reduced-motion scene, mouse drag, touch rotation, keyboard rotation, reset, exploded view, tab navigation, theme changes, and restoring and clearing local text and images. A separate Chrome run with WebGL disabled verified the CSS face. The Taste finish gate still reports marketing-page requirements, including a full-screen hero and separate full-screen sections. The workspace keeps chat and the viewer together. The gate also flagged shader terms from the vendored Three.js source and did not credit the fallback. Chrome verified the rendered scene, the CSS face with WebGL disabled, and recovery after deliberate context loss. The browser used fixture responses for chat and device interactions. The live browser rendered the connected Face Lab 0.10.0 board, kept Pause voice accessible, and restored the scene after simulated WebGL context loss.

The security review of UI UX Pro Max and Taste Skill is in [the November 14 audit](SYSTEM-AUDIT-2026-11-14.md).

The round-model update was checked in live Control Room by saving all four Ollama choices, confirming the manager setting and sustained USB connection, switching the composer to image mode, and selecting the 3D PCB by pointer. Keyboard and mobile controls also selected parts and displayed their descriptions.
