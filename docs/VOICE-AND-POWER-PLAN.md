# Voice and Portable Power

Updated 2026-11-06. Installed Face Lab 0.9.3 gives the owner “Hey Mr. Robot”, screen tap and an optional IO16 talk switch. The Mac spots the wake phrase locally and Gemini Live returns spoken replies. See the current [voice guide](GEMINI-VOICE.md) and [connection drawings](BREADBOARD-CAMERA-DISPLAYS.md). The new [AA and status-LED plan](POWER-AND-STATUS-LEDS.md) records the owner’s two-AA choice; optional LED firmware is built in 0.9.4 source but is disabled and not installed.

## Two voice routes

| Route | Board responsibilities | Other requirements | Acceptance |
| --- | --- | --- | --- |
| Muse evaluation (deferred) | SDK UI, microphone/speaker, BLE setup and Wi-Fi | Muse account/token, phone enrollment, Internet | Build/boot/token/Wi-Fi verified; final discovery retry failed. Not currently installed. |
| Our Gemini application (active) | Face, visible wake/capture states, pause-based turn and bounded PCM playback | USB-connected Mac for wake detection and Gemini | Owner confirms clear speech in 0.8.0. USB counters verify one hands-free reply in 0.9.2. Physical switch and repeated wake turns remain to be checked. |

These are separate firmware images. Muse replaces Face Lab on the board; its source, host service and compiled recovery files remain available. It does not become another provider inside the Arduino application automatically. Keep a shared face/state/interaction design as the longer-term goal.

Muse's ordinary voice-note path returns captions. This evaluation enables **experimental live voice** for spoken replies, bounded to 30 seconds idle and 180 seconds total. On the non-C board, a short **BOOT/GPIO0** press starts a call, the next press hangs up; holding sends a voice note. Pairing confirmation uses the button when requested. Account/service acceptance is unverified until paired. No breadboard button is needed for this first test.

The local overlay disables OTA, LAN tunnelling and remote BLE commands. No security fuses or flash encryption are enabled. SDK/Wi-Fi credentials are empty in the build; USB provisioning stores the SDK token in device NVS, which is not encrypted in this evaluation. Phone enrollment supplies account/network state. Do not retain raw serial output while entering credentials. [Pinned SDK instructions](https://github.com/facebookincubator/muse-gadget-sdk/blob/1b894f551e64416e2844452ec6056ec56d6a10f1/esp32/AGENTS.md).

## Voice milestones

- [X] Microphone speech response and speaker sound verified.
- [X] Reproduce Face Lab 0.7.0 display/touch/advancing frames and preserve compiled recovery files.
- [X] Review live voice and add the bounded non-C overlay.
- [X] Build/validate/flash Muse, observe startup/status and provision the replacement token with ACK.
- [X] Owner confirms Muse display/Settings and configures Wi-Fi during evaluation.
- [ ] Complete Muse phone enrollment (deferred after final discovery failure).
- [ ] Verify one button-started spoken conversation, audible reply, hang-up, idle timeout and reconnect.
- [X] Implement/build/upload Gemini Live USB audio transport; verify physical speech and a clear audible reply in our independent firmware.
- [ ] Extend cancellation/expiry/reconnect and repeated voice-turn reliability acceptance.
- [X] Add and exercise the Mac's local “Hey Mr. Robot” keyword detector, with a visible listening state and explicit Stop.
- [ ] Check wake-word false activations and feedback under room noise. Measure an on-device engine with Wi-Fi/audio active before considering a portable design.

## Existing parts and power choices

The retained kit illustrations explicitly show a **2× AA holder**, small/large pushbuttons, slide switches, jumper wires, breadboard and 10 kΩ resistors. The owner now chooses the existing holder and two AA cells for portable-power planning. Mac USB remains the working voice route while the missing power stage is identified. Chemistry, actual wiring/polarity and loaded voltage remain unknown. The pictured black USB item is labelled **card reader**. No suitable voltage converter is identified in these images. Evidence: `assets/reference-images/kit-parts-list-a.jpg`, `kit-parts-list-b.jpg`, `kit-overview.jpg`; illustrations are not measurements of actual parts.

| Choice | Required checks |
| --- | --- |
| **Requested: 2× AA → regulated converter → proper USB source interface → USB-C lead** | Cell chemistry/model, holder polarity and voltage range remain unknown. Identify and review a regulated 5 V converter/source interface against measured display/audio peak demand before use. No compatible converter is established yet. |
| Alternative: USB power bank → USB-C lead | Verify regulated USB output, display/audio demand and idle auto-shutoff. Not the selected hardware. |
| Alternative without a USB power lead: protected 1S lithium cell → BAT | A different battery from the AA holder. Verify exact cell/protection, connector pitch and polarity, charge voltage/current, capacity and actual AXP2101 configuration before connecting. Matching plugs do not establish matching polarity. |

**Do not connect the AA holder or the kit's 9 V cable to BAT, 3V3 or GPIO.** BAT is a lithium charging interface. Keep header VBUS unused until external-supply/backfeed behavior is reviewed. Do not combine unverified supplies. Runtime requires current measurements.



The requested AA route still needs a USB power lead. The board has one USB-C port; substituting a battery source there removes the present Mac data link. A reviewed power/data arrangement or new network transport is separate work. No improvised Y-cable or unverified rail injection. [Detailed drawing and checks](POWER-AND-STATUS-LEDS.md)

After pairing, Muse's Wi-Fi route is intended to operate without the Mac. Battery power does not remove the Mac dependency from our current USB/Gemini route. [Waveshare hardware and battery interface](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75); retained schematic and [inventory](HARDWARE-INVENTORY.md).

## Optional external button

The implemented talk input uses the actual Waveshare header labels **IO16** and **GND**. It is a 3.3 V input with internal pull-up and 35 ms active-low debounce; a normally open switch closes IO16 to GND. Press and release once to start a question when voice mode is armed; press again during a turn to cancel. A long hold is not required. Physical switch assembly and acceptance remain pending. Verify the actual four-leg switch contact pairs with continuity while unpowered; the product illustration and schematic disagree about H2 ordering, so do not assemble by counted contact number. [Button drawing](BREADBOARD-CAMERA-DISPLAYS.md#2-connect-the-momentary-talk-button)

The new status-LED concept reserves IO17 for green question capture and IO18 for red reply playback **conditionally**. The kit provides a suitable component class; two 1 kΩ resistors are proposed for preparation. Actual resistor/LED measurements and GPS variant remain unresolved, so normal firmware leaves both candidates untouched. The GPS-G option has an onboard LC76G: no external antenna is not evidence that the pins are free. [Current inventory](HARDWARE-INVENTORY.md) · [LED guide](POWER-AND-STATUS-LEDS.md)

## Start Control Room in the Mac's default browser

```sh
cd /path/to/MR_AI_Assistant
~/.platformio/penv/bin/python tools/manager.py --open
```

`--open` opens and unlocks http://127.0.0.1:18765/ in the Mac's default browser. Keep the new server's Terminal process open; Ctrl+C stops it. An existing verified service is reused. The bare URL alone does not unlock it. Face Lab's USB manager/Gemini path does not control Muse firmware.

The active voice route uses **Gemini 3.8 Live** with Charon over the Mac's authenticated host service. Text-model selection and the Live audio route are separate settings. Current behavior and acceptance are recorded in the [Gemini voice guide](GEMINI-VOICE.md); battery planning does not change that USB transport.
