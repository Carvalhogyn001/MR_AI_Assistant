# AA Power and Voice Status LEDs

Updated 2026-11-06. The owner chose the existing **two-AA holder and two AA cells**. The requested indicators are **green while the question is captured** and **red while the reply plays**. The diagrams below make the proposed connections explicit, but the new LED and battery circuits must remain disconnected until their actual parts and measurements are recorded.

Current known gaps: cell chemistry/model and polarity, regulated power converter and USB source interface, actual Waveshare GPS fitment, each physical LED's polarity/current rating, and measured resistor values. The kit illustration and owner report establish the intended component class, not individual electrical measurements. A normal firmware build leaves the candidate LED pins untouched. [Inventory and conditional reservations](HARDWARE-INVENTORY.md)

## Inspect the new photo



Original JPEG · Provenance and SHA-256 · Zoomable drawing

The preserved photo shows the Freenove board and fitted camera, its GPIO extension, a rectangular LCD with four leads, three DIP packages, and a yellow-looking LED with a resistor near the end of the breadboard. It does not establish resistor value, LED forward voltage/current, electrical polarity, continuity of the rails, or powered behavior. Wire color is not a net assignment. No photo transformation was applied to the saved original; its JPEG bytes and EXIF are unchanged.

Keep the Freenove/LCD wiring separate from the new Waveshare indicators. The same GPIO number on the two boards is not the same physical connection. Use an isolated area or a separate breadboard after checking every occupied strip.

## Green capture and red playback



Zoomable SVG · Editable Canvas · Editable Excalidraw

| Actual state | Green LED | Red LED | Meaning |
| --- | --- | --- | --- |
| Ready / voice off | Off | Off | No question capture or reply playback. |
| Ambient wake monitoring | Off | Off | Green is not a microphone privacy indicator; the on-screen **WAKE LISTENING** label still shows ambient capture. |
| Question capture started successfully | On | Off | Speak; green follows capture, not the physical button being down. |
| Thinking / receiving reply | Off | Off | The reply is being prepared or transferred. |
| Reply playback after output setup | Off | On | Red follows speaker playback, then turns off on cleanup. |
| Cancel / error / timeout | Off | Off | Output and capture are stopped. |

The existing talk input remains **IO16 → normally open switch → Waveshare GND**, using the internal pull-up. Press and release once to start; speak at LISTENING. Press again during the turn to cancel. A long hold is not required. [Verified assignment and illustrative breadboard holes](BREADBOARD-CAMERA-DISPLAYS.md#2-connect-the-momentary-talk-button)

The conditional LED map is **IO17 for green** and **IO18 for red**, active high. Each branch needs its own series resistor, then LED anode; its cathode returns to Waveshare GND. **These are dormant software candidates, not final assembly authorization.** Waveshare documents LC76G UART sharing on GPIO17/18 in the GPS variant. The GPS module is onboard; its antenna is external. The owner reports nothing attached, but an absent antenna does not prove an absent module. The retained standard-product listing suggests a non-GPS model; actual PCB/model identification must establish those signals are free before use. Read signal labels on the actual header instead of counting H2 positions. [Manufacturer hardware reference](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/main/HARDWARE_REFERENCE.md)

### Parts to set aside now

Use the **separate two-leg green LED and two-leg red LED** from the kit, plus **two resistors from the kit's 1 kΩ group**, one per LED. Do not use the four-leg RGB part for this diagram. The owner's parts-list image labels these LEDs and 220 Ω / 1 kΩ / 10 kΩ resistors. The owner reports that these are the parts available. Leave the pictured yellow LED/resistor in place until its existing circuit is understood.

Freenove's official external-LED lesson uses **220 Ω** in series. The **1 kΩ choice here is a project preparation choice** for lower indicator current, not a value read from the new photo or claimed by the vendor for this circuit. At exactly 3.3 V and 1 kΩ, even treating the LED drop as zero gives 3.3 mA; actual current is lower with a forward-biased LED, and tolerances/supply range still matter. Brightness and the actual LED rating remain unverified. [Freenove LED reference circuit](https://docs.freenove.com/projects/fnk0047/en/latest/fnk0047/codes/C/1_LED.html)

With everything unpowered, measure each selected resistor separately rather than through an existing circuit, and record its value/tolerance. Confirm each LED's anode/cathode; the tutorial's long-anode/short-cathode cue applies to untrimmed leads and is not conclusive after trimming. Record the actual part information and forward voltage at the intended low current before accepting the circuit. No resistor value is selected from photo colors. The estimate `I ≈ (Voutput − Vforward) / R` helps choose a branch resistance; check supply/output range and component tolerances as well. A resistor is required in **each** branch. The chip datasheet's high-drive test currents are characterization conditions, not an LED current target. [Espressif DC characteristics, §5.4](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)

### Illustrative breadboard placement



Zoomable editable SVG

This drawing is an **empty-board electrical-node example**, not a tracing of the occupied Freenove breadboard or a required LED leg span. A–E within one numbered row form one node; F–J form another, separated by the center gap. Confirm the actual board with continuity. Insulated jumper lines crossing other holes do not make connections there.

The green branch uses input row 6, resistor output/anode row 10 and cathode row 12. The red branch uses input row 18, resistor output/anode row 22 and cathode row 24. Two separate return jumpers reach row 26, then Waveshare GND. The printed contact labels show one illustrative placement with distinct occupied holes. Adapt with insulated jumpers for actual lead spacing after verifying the parts. Neither power rail is used.

The optional source implementation is described in [Status LEDs Firmware](STATUS-LEDS-FIRMWARE.md). It remains disabled by default; the currently installed 0.9.3 has no external LED output.

Before a future powered test: record the actual parts and free GPIOs, review the chosen current/resistance, inspect the unpowered net/polarity/continuity, and only then use the opt-in firmware. Exact breadboard holes depend on actual LED leg spacing and occupied rows. A source test can verify state mapping and disabled-default behavior; it cannot verify the assembled circuit or brightness.

## The requested two-AA route



Zoomable SVG

The requested route is **two-AA holder → suitable regulated 5 V converter → proper USB source interface → USB power lead → Waveshare USB-C**. No compatible converter or source interface has been identified in the assets. The holder is not connected directly to BAT, 3V3, VBUS or a GPIO.

Before a converter can be selected, record the cells' chemistry/model, holder wiring/polarity, voltage over the intended discharge range, and measured board demand during display, microphone capture and speaker peaks. The converter must support that input range and output demand with appropriate regulation/current protection and a suitable USB source connector. A converter module with only exposed pads is not automatically a complete USB-C power source. Runtime requires measured energy/current; the photo cannot supply it.

This AA arrangement still uses a USB power lead. Replacing the Mac connection at the board's single USB-C port also removes the current USB audio/control data link. **Battery power alone does not provide wireless voice.** Keep the working Mac USB route for present voice use; a reviewed power/data topology or a future network transport is separate work. Do not improvise a Y-cable that combines two power sources. The manufacturer specifically requires review of external-supply/backfeed behavior before driving board rails. [Waveshare power and integration notes](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/main/HARDWARE_REFERENCE.md)

## If the goal is no USB power lead

A different route uses a **protected nominal 3.7 V single-cell lithium battery** at BAT. This replaces the AA choice; it does not make the AA holder compatible with BAT. Waveshare identifies an MX1.25 two-pin lithium charging/discharging connector. Connector shape alone does not establish polarity. [Waveshare battery interface](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75)

Before BAT connection, establish the exact battery model/chemistry/capacity/protection, connector polarity, allowed charge voltage/current and the board's actual AXP2101 configuration. Charger settings are programmable. Published defaults do not prove the configuration left by earlier firmware or suitability for the chosen cell. No final BAT contact polarity or charging setting is assigned in these drawings. [AXP2101 charger behavior, §6.7](https://files.waveshare.com/wiki/common/X-power-AXP2101_SWcharge_V1.0.pdf)

A verified USB power bank is another possible USB-power source, but it still needs a lead and testing for peak demand and idle shutoff. This guide does not select a product or claim battery runtime.

## Verification and editable sources

The owner photo is copied byte-for-byte and SHA-256 recorded. The four SVG/PNG drawings are code-native; their text and layouts were visually inspected, and their SVG/Canvas/Excalidraw data parse. Mirrors live in the Obsidian project alongside a linked power/status-LED note.

```sh
python3 tools/build_power_guides.py --render
# Or regenerate all current connection drawings:
python3 tools/build_visual_guides.py --wiring-only --render
```

Physical acceptance remains pending: confirmed parts and unpowered circuit checks, measured LED current, green only during question capture, red only during playback, both off after cancel/error, followed by a separately reviewed battery test. No LED/battery wiring, charger changes or battery-powered operation was performed to create this guide.
