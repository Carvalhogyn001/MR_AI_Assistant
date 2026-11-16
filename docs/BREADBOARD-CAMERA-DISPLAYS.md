# Talk Button, Camera and Displays

Updated 2026-11-06. **Start with the two-wire talk button.** The round Waveshare already includes its ESP32, screen and microphones. It needs a USB-C data cable to the Mac, not display jumpers to the Freenove. Keep the existing camera on its Freenove ribbon connector and give that board a separate USB-C cable.

The drawings show a proposed physical assembly using already recorded assignments. **The external switch and new combined camera route are not hardware-verified.** Read the actual board labels before inserting a jumper. [Hardware inventory](HARDWARE-INVENTORY.md)

New follow-up: the [latest owner photo and AA/status-LED plan](POWER-AND-STATUS-LEDS.md) preserve the new LCD/LED breadboard arrangement. Green capture/red playback circuits and two-AA power remain conditional until parts and measurements are known.

## 1. Pick the right parts and photos



| Job | Image to use | What it establishes |
| --- | --- | --- |
| Round Waveshare screen, USB and talk header | Waveshare rear / speaker | Clear product-reference view of USB-C, SPK, BAT and the H2 signal labels. Verify those labels on your actual board. |
| Other ESP32 and its USB port | Freenove board close-up | WROVER-E marking, USB-C receptacle and extension board. |
| Camera and fitted ribbon | Camera / pin-label close-up | Existing white latch and orange camera ribbon. Leave it seated. |
| Button and jumper types | Kit parts list A | Choose the momentary **Push Button** and two male-to-male jumpers for the pictured female H2 socket. The separately illustrated slide **Switch** is not the talk button. |
| Latest LCD/LED breadboard arrangement | New owner photo | Current photographed layout, with yellow-looking LED and resistor. Their electrical ratings and net connectivity are unknown. |
| Earlier breadboard space and loose LED displays | Full breadboard photo | The extension, MPU6050, chips, matrix and other displays occupy rows. This is a parts layout, not proof of a working circuit. |
| Separate 1602A screen | LCD rear and front | 1602A V1.4 / PCF8574T identity and the previously blank lit character area. |

## 2. Connect the momentary talk button



Zoomable SVG · Editable Excalidraw

Use the small momentary switch, two jumpers, an isolated breadboard area and a continuity meter. The reference image shows a female Waveshare socket, so male-to-male jumpers fit. If your actual unit has exposed male pins, use the female end of a female-to-male jumper there.

1. **Unplug both boards.** Use a clear section isolated from the Freenove extension and every existing component, or use a separate breadboard. The power rails remain empty.
2. **Identify the switch electrically.** A four-leg tactile switch often has two internally connected pairs. Find those pairs with continuity while unpowered. Across the two different pairs, the circuit must be open when released and connected only while pressed. Do not infer pairing from its shape.
3. **Seat it across the center gap.** In the example, one pair occupies E10/E12 and the other F10/F12. Actual leg spacing may differ; change row numbers to fit without bending/forcing the switch. Keep the two contact groups on separate breadboard strips. Check continuity again after insertion.
4. **Match the Waveshare labels.** With the rear toward you and USB-C on the right, locate the actual contacts marked **IO16** and **GND** (or **G**). The vendor product image and retained schematic disagree about H2 order. **Do not count pins from either end.** If the physical labels cannot be read or do not match, leave it unplugged until identified.
5. **Connect two wires:** IO16 → **B10**, GND → **I10** in the illustrated example. B10 and E10 share the left group of five; I10 and F10 share the right group. The center gap separates them. No wire goes to 3V3, VBUS or either power rail. The board's internal pull-up provides the input bias.
6. **Check before power:** IO16-to-GND must be open when released and connected only when pressed. Verify neither jumper touches another header contact. If it is always connected, correct the switch orientation/strip selection while unpowered.
7. **Reconnect Waveshare USB-C to the Mac.** Connect in Control Room, then enable tap-to-talk. Press and release once, and speak when the screen says **LISTENING**. A second press during an active turn cancels. This is press/release to start, not hold-to-record.

Physical acceptance requires observing a deliberate switch press, an increasing `talk_button_presses` status value, the listening transition and cancellation. A source-code pin assignment is not acceptance of the assembled circuit. Use Control Room's existing serialized USB owner for status; disconnect it before a diagnostic client so two clients cannot consume each other's replies. Do not reset the board merely to inspect status.

## 3. Keep the screen and camera on their own boards



Zoomable SVG · Editable wiring Canvas

| Part | Connection now | Verification boundary |
| --- | --- | --- |
| Round Waveshare | USB-C data/power → Mac; supplied keyed speaker → **SPK** while unpowered. Panel and microphones are built in. | Current face/voice route is recorded in [project status](PROJECT-STATUS.md). BAT is not a speaker socket. Leave unverified batteries disconnected. |
| Freenove Wrover with camera | Separate USB-C data/power → Mac for bring-up. Keep fitted camera ribbon in its own latch. | Earlier camera preview and `/capture.jpg` worked on its access point. No new connection or live camera test is claimed here. |
| Between the boards | No jumper bundle is needed for this plan. Keep header power rails separate. | The proposed authenticated Wi-Fi still-image route goes from Freenove to the Mac; it is not implemented by this drawing. |

For a future combined Gemini camera turn, the Mac should request one authenticated still on the local Wi-Fi while retaining its Internet connection. Do not move the parallel camera ribbon onto the Waveshare header. The existing camera pin reservation belongs only to Freenove. [Camera / SD pin map](SD-CAMERA-PIN-MAP.md)

## 4. Treat the extra screens as separate bench checks

If “new screen” means the round Waveshare, section 3 is the connection plan. If it means the rectangular LCD or matrix in the kit, those parts need the checks below before a complete wiring diagram can be verified.

| Part | Known evidence | Required next measurement |
| --- | --- | --- |
| QAPASS 1602A V1.4 / PCF8574T | I²C answered at `0x27` with Freenove **GPIO33 SDA / GPIO13 SCL**, tested at 3.3 V. Characters stayed blank. | Confirm panel supply, contrast arrangement, expander mapping and idle SDA/SCL voltage. The pictured module has no user contrast potentiometer. |
| Bare 8 × 8 LED matrix | Photo shows the bare matrix and two SN74HC595s nearby. This does not establish a completed driver circuit. | Read actual part marking; measure row/column map and polarity; specify resistors, per-LED current and a suitable driver before pin assignment. |
| Single-digit, four-digit and bar-graph displays | Separate loose LED packages are visible on the breadboard. | Identify each package and current limits before adding wiring. |

If the LCD requires 5 V, its I²C pull-ups must not drive 5 V into ESP32 GPIO. A verified bidirectional I²C level shifter would place GPIO33/GPIO13 on the 3.3 V side and LCD SDA/SCL on the 5 V side, with a common **Freenove** ground. The supply, module labels and pull-ups still need verification; the kit photos do not identify such a shifter. Keep the LCD disconnected during the first talk-button test.

## AA battery and external status LEDs

The owner selected the existing two-AA holder. The [power/status-LED guide](POWER-AND-STATUS-LEDS.md) shows the missing regulated 5 V converter and USB source interface, the current USB-data dependency, and a separate conditional lithium BAT alternative. It also maps green to question capture and red to speaker playback using disabled-by-default candidate GPIO17/18; actual GPS/LED/resistor checks precede wiring.

## Editable files and verification

The Obsidian project hub links the mirrored PNG/SVG drawings, **MR. Robot Wiring.canvas** and **MR. Robot Talk Button.excalidraw**. The engineering folder remains the source of truth. Original asset photos are unchanged; the generated diagrams embed copies for portability.

Regenerate only these guides, leaving earlier screen concepts untouched:

```sh
python3 tools/build_visual_guides.py --wiring-only
# macOS: also render PNGs using Quick Look and sips
python3 tools/build_visual_guides.py --wiring-only --render
```

Document verification: inspect all three full-frame PNG exports, parse SVG XML and Canvas/Excalidraw JSON, and check referenced image paths. Hardware verification remains the continuity/press/cancel sequence above; no wiring, new voltage measurement or camera test was performed to create these drawings.

Illustrative two-LED breadboard placement shows separate row groups and return jumpers on an empty board. It is conditional on the LED/GPS checks in the power guide and does not reuse the occupied Freenove layout.
