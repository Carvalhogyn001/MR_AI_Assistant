# MR. Robot battery, talk button, and Wi-Fi wiring

Editable Excalidraw drawing

## Wire and test the green button first

The round **Waveshare ESP32-S3-Touch-AMOLED-1.75** is Mr. Robot. The **Freenove ESP32 WROVER** pictured on the populated breadboard is a separate camera board. The photos show the AA holder leads going toward the breadboard rails and two lit LEDs. A lit LED cannot establish that a rail is safe for either ESP32. Use a small separate breadboard for the button if available. To reuse the pictured board, disconnect the AA holder and USB and verify that each chosen terminal strip is isolated from existing wiring and both power rails. Bench photo · AA holder photo

1. **Unplug USB and remove the AA holder from the breadboard.** Use continuity mode on the loose green button. Find its two contact groups. Within a group the terminals typically stay connected. Across the groups, your meter should read open when released and show continuity only while pressed. If that behavior does not check out, stop and identify the part.
2. Use the **IO16** and **GND** (or **G**) labels on the round board's H2 header. Match the actual labels instead of counting contacts. For the drawing's example, put one verified button group at **E10/E12** and the other at **F10/F12** if the footprint fits across the center gap. Use any two verified isolated strips and insulated leads if the legs do not fit. With the switch fitted, connect **H2 IO16 → B10** and **H2 GND → I10**. B10 and E10 share one strip. F10 and I10 share another. Power rails stay empty. The 3.3 V input has an internal pull-up. Green button close-up · [Board pin definition](../firmware/assistant/include/board_pins.h)
3. With the jumper ends temporarily detached from H2, measure between the two loose ends. Expect **open released, continuity pressed, open again on release**, then reconnect to H2. If the actual Waveshare labels are hard to read, send a straight-on photo of the rear header with USB-C and the silkscreen in frame before plugging either jumper in. [Waveshare board reference](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/main/HARDWARE_REFERENCE.md)
4. Connect Waveshare USB-C to the Mac with the data cable. The supplied keyed speaker stays at **SPK** and the microphones are onboard. In [Control Room](http://127.0.0.1:18765/), connect the device and enable **Tap-to-talk** once. Press and release the physical button, speak at **LISTENING**, then confirm a reply. On a second turn, press again to check cancel. The Device diagnostics counter `talk_button_presses` should advance. Use Control Room as the sole USB client during the test. [Voice setup](GEMINI-VOICE.md)

| From | To | Carries |
| --- | --- | --- |
| Round Waveshare H2 IO16 | Isolated strip at B10 → switch group A at E10 | 3.3 V logic input |
| Round Waveshare H2 GND | Isolated strip at I10 → switch group B at F10 | Switch return |
| Round Waveshare SPK | Supplied keyed speaker plug, if already fitted leave it there | Speaker output |
| Round Waveshare USB-C | Mac USB data cable during the button test | Power and voice data |

## Supply power from the two AA cells

The proposed path is **AA holder +/− → matching converter IN+/IN− → regulated 5 V USB source output → USB lead → Waveshare USB-C**. Use the converter's USB source output when it has a verified one. If it only has pads, it needs a suitable USB source interface. Keep the battery power path separate from all breadboard signal strips. Leave the AA leads off **BAT**, **H2 VBUS**, **3V3**, and GPIO. The board's BAT connector is intended for a single 3.7 V lithium cell. [Waveshare power reference](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/main/HARDWARE_REFERENCE.md#power-usb-display-and-buttons)

A compatible converter is not identified in the photos. Before connecting one, read the AA labels, measure holder polarity and output, and use its cell specifications to establish the pack's operating voltage range. Measure the Waveshare's USB demand with the display on, while capturing audio, and during speaker playback. Check that the converter supports the pack's operating voltage range and measured peak demand. Verify 5 V USB output under load before plugging in the board. For the battery-only trial, use a single power source at USB-C, with the Mac cable removed. Check for resets through display and audio activity once the LAN voice path is ready. The LEDs, LCD, and Freenove have separate circuits and need no changes for this setup.

If you have a converter, send clear photos of **both sides and its markings**, plus the **AA labels** and, if you have a meter, the **holder voltage and polarity**. A regulated USB power bank can provide portable USB power for a separate bench test once its output and idle behavior are checked. [Existing battery options](POWER-AND-STATUS-LEDS.md)

## Carry voice over your Wi-Fi

Face Lab currently sends button state and audio through native USB. The Mac's Control Room at `127.0.0.1:18765` listens only on the Mac, so connecting both devices to Wi-Fi does not establish a voice session. The ESP32-S3 joins the router on **2.4 GHz**. The Mac can use another band as long as both devices can reach each other on the local LAN. Check client isolation if they cannot. [Waveshare radio specifications](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75) · [Current Mac listener](../backend/mr_robot_backend/server.py)

Proposed first slice: keep Mac USB power for development, add a separate authenticated LAN connection from the board to a Mac listener, and verify a physical button event and status reply. Keep the existing Control Room local to the Mac. Next, stream one bounded question and one spoken reply over that connection and verify start, cancel, timeout and redelivery behavior. Feed the existing Gemini Live service from the Mac, where the provider key stays. Validate one complete press-to-reply turn with USB data physically absent and the verified portable source powering the board. Wi-Fi voice and physical battery/button acceptance are pending.
