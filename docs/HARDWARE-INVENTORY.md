# Hardware Inventory

### Owner photos and green talk button, 2026-11-13

| Part | Interface and electrical status | Evidence |
| - | - | - |
| Green push button, exact model unknown | Four metal terminals are visible. Use it with the Waveshare's 3.3 V active-low IO16 input after verifying two contact groups and momentary normally open operation with a meter. No external voltage or resistor is required for the input. | Owner selected this part. Side view · Terminal view |
| Freenove ESP32 WROVER and GPIO Extension Board | Camera ribbon, LCD leads, two lit LEDs and other components are visible. Rail voltage, rail continuity, power direction and individual nets were not measured. Keep its rails separate from the Waveshare. | Bench photo · Photo with AA holder |
| 2× AA holder with two installed cells | Two leads appear to feed the pictured breadboard rails through jumpers. Holder wiring, polarity, cell chemistry, voltage under load and suitable 5 V regulator/USB source remain unverified. | Photo with AA holder |
| Round Waveshare ESP32-S3-Touch-AMOLED-1.75 | H2 **IO16** (3.3 V input, internal pull-up) and H2 **GND** are the only breadboard connections in this plan. USB-C is the power input for the proposed regulated AA route. Wi-Fi is 2.4 GHz; current Face Lab voice still uses USB. | Existing verified board inventory below, [Waveshare hardware reference](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/main/HARDWARE_REFERENCE.md), and [button pin definition](../firmware/assistant/include/board_pins.h). The new photos show the Freenove, so inspect the Waveshare contact labels before connecting. |

See the [battery and Wi-Fi wiring guide](BATTERY-WIFI-WIRING.md) for the unpowered continuity test and phased acceptance.

The assembled button straddles the breadboard center gap in the new bench photos. One visible orange jumper enters the blue power rail and the other enters the A–E half near the LED circuit. The F–J button side has no visible jumper, and the Waveshare ends are outside the photos. The IO16-to-switch-to-GND circuit has not passed continuity or powered testing.

A later rear-header photo identifies the actual Waveshare PCB as **Rev1.1**. With the rear facing the camera and USB-C on the right, its printed labels read **IO18, IO17, IO16, RXD, TXD, 3V3, GND, VBUS** from left to right. At initial review the owner reported IO18, the photo showed a 3V3 jumper, and Face Lab 0.9.3 reported zero presses. The previous voice session separately reported `voice_usb_timeout`.

After the owner reported moving the signal to IO16, removing the 3V3 jumper, and checking continuity, Control Room's USB status reported `talk_button_presses=1`. Tap-to-talk then armed and stayed in `waiting_for_tap` with no USB error. The owner reported a second press with no response. After stopping voice, a fresh read still reported one press, four touch events, and 127043 ms uptime, up from 89429 ms before arming. Three further owner-reported press/release cycles with voice off left the counter at one at 171429 ms uptime. The owner then moved the ground jumper directly from Waveshare GND to the switch strip, bypassing the breadboard rail, and confirmed the button worked. Before the 0.9.5 update, the installed 0.9.3 reported 13 presses and one completed voice reply.

Muse board mapping for the non-C Waveshare: the same verified IO16 switch to GND uses an internal pull-up and the existing switch debounce. Onboard BOOT/GPIO0 remains the physical pairing-confirmation input. PWR remains on the existing PMIC path.

The second photo batch shows a Freenove audio converter/amplifier, a ULN2003AN stepper driver, a relay, and sensor and LED modules. The audio board is marked **VCC 3.3–5 V** for its supply input. The yellow relay has a **5 V coil**. Neither provides regulated USB power. No suitable 5 V boost converter was identified in this batch. Audio board markings · Stepper driver · Relay markings · [Freenove audio reference](https://docs.freenove.com/projects/fnk0047/en/latest/fnk0047/codes/C/29_Bluetooth_Media_by_Audio_Module.html)

### Conditional status LEDs and battery planning, 2026-11-06

**Planning record only: no external LED or battery connection is accepted.** The new owner photo is preserved unchanged as `assets/reference-images/freenove-lcd-breadboard-led-2026-11-06.jpg`, with its SHA-256 and origin in the adjacent provenance JSON. It shows a yellow-looking LED package and a resistor beside the Freenove breadboard. Their part numbers, electrical polarity, LED forward voltage/current rating, resistor value/tolerance and complete connectivity are **unknown**. The owner reports using the kit LEDs shown in the retained assets. The kit illustration labels separate two-leg green/red LEDs and 220 Ω, 1 kΩ and 10 kΩ resistors. This establishes the intended kit component class; the new photo does not identify or measure a green/red pair.

| Proposed part / function | Candidate interface and voltage | Evidence / conditions before use |
| - | - | - |
| Green question-capture indicator | Candidate **Waveshare GPIO17 / IO17**, active-high 3.3 V output → its own series resistor → LED anode; cathode → Waveshare GND | Reserved for a disabled-by-default software option only. Actual standard/non-GPS board and free IO17 must be verified; LED model/polarity/current and resistor must be recorded before enabling or connecting. Green means actual question capture, never ambient wake monitoring or a bare button press. |
| Red speaker-playback indicator | Candidate **Waveshare GPIO18 / IO18**, active-high 3.3 V output → its own series resistor → LED anode; cathode → Waveshare GND | Same conditions. Red means active reply playback after output setup, never thinking/receiving. Normal firmware must not configure/write either candidate pin. |
| Prepared resistor choice | **Two nominal 1 kΩ kit resistors**, one per 3.3 V LED branch | Project low-current preparation choice, not an accepted assembly or measured value. Official Freenove external-LED example uses 220 Ω; the larger 1 kΩ lowers current. Confirm each actual resistance/tolerance and LED polarity/rating before connection. At exactly 3.3 V / 1 kΩ, the zero-forward-drop upper bound is 3.3 mA; this is a calculation, not a current measurement. |
| Portable battery | Owner confirms the existing **2× AA holder + two AA cells** as the requested route; cell chemistry/model and regulated converter are unknown | Requires an identified suitable regulated 5 V converter and USB source interface before a USB-C power lead. The AA holder is not a direct BAT/3V3/VBUS/GPIO input. A protected nominal 3.7 V 1S lithium cell would be a separate alternative requiring polarity/protection/charger checks. Power does not replace current Mac USB voice data. |

Manufacturer hardware reference rechecked live on 2026-11-06: GPIO17/18 are expansion GPIO on standard/`-B` boards, but can share the LC76G UART on `-G`. The GPS version has an **onboard** LC76G and an external antenna. The owner reports nothing attached, but no external antenna does not prove no onboard GPS. The retained standard-product listing supports a non-GPS interpretation, not physical fitment acceptance. Actual GPS fitment remains unresolved, so this reservation is **not a final wiring assignment**. Match actual signal labels, never H2 contact count. [Waveshare pin/reference source](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/blob/main/HARDWARE_REFERENCE.md)

The owner parts list (`kit-parts-list-a.jpg`) and [official Freenove external-LED lesson](https://docs.freenove.com/projects/fnk0047/en/latest/fnk0047/codes/C/1_LED.html) support the common two-leg LED + series resistor circuit. Its Freenove GPIO2 assignment must not be copied to Waveshare. Each actual branch still needs recorded resistance and a chosen current within both LED and GPIO limits; no resistor value is inferred from the photo. The ESP32-S3 datasheet's drive-current test conditions are not a target LED operating current. [Espressif electrical characteristics, §5.4](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)

Waveshare identifies BAT as an MX1.25 2-pin nominal 3.7 V lithium charging/discharging interface. The AXP2101 charge voltage and current are programmable; datasheet defaults do not establish the present board configuration or battery suitability. Verify the exact cell and charger together before connection. [Waveshare connector specification](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75) · [AXP2101 charger, §6.7](https://files.waveshare.com/wiki/common/X-power-AXP2101_SWcharge_V1.0.pdf)

Acceptance is staged: document actual parts/variant → unpowered net/polarity/continuity check → reviewed current-limited circuit → opt-in firmware → observed capture/playback/cleanup and measured current. Until then, the normal build leaves GPIO17/18 untouched and the physical LED/battery assembly remains disconnected. See [power and status-LED guide](POWER-AND-STATUS-LEDS.md).

### Talk switch assignment, 2026-11-06

The non-C Waveshare uses the H2 contact marked **IO16** for a normally open momentary switch to the H2 contact marked **GND** or **G**. This is an active-low 3.3 V input with the ESP32 internal pull-up. Use the board labels to locate the contacts. The retained H2 schematic table and the vendor case illustration show different GPIO ordering, so a contact count is unsuitable for assembly. No power rail is required for this circuit. The actual button leg pairs must be confirmed with continuity while unpowered. Sources are the retained Waveshare hardware reference and the kit photos. External wiring remains pending physical verification.

The GPIO16 assignment is available in the voice mode that waits for a tap or a wake phrase. The switch can start a turn or cancel an active turn. Verification requires a deliberate press and release on the assembled circuit and a status or recording transition. The camera stays on its existing Freenove ribbon connector. The 1602A LCD stays separate while its supply, contrast and I²C pull-ups are verified.

Latest audio extension, 2026-10-31: Face Lab voice uses the existing inventoried pins, ES7210 MIC1/slot0 at 16 kHz PCM16 and ES8311 output at 24 kHz PCM16. The retained ES8311 driver coefficient table explicitly supports 6,144,000 Hz MCLK / 24,000 Hz sample rate (256×); stereo I2S duplicates mono output. Hardware PCM playback/capture acceptance is recorded in PROJECT-STATUS.md, separately from this source-based configuration. No external button, voltage or pin is changed.

Updated 2026-10-30. **Specification** = published evidence; **reported** = owner statement; **hardware verified** = recorded device observation. Product illustrations do not verify the owner's physical unit.

## Primary target: Waveshare ESP32-S3-Touch-AMOLED-1.75

| Item / model | Interface and voltage | Evidence and status |
| - | - | - |
| ESP32-S3-Touch-AMOLED-1.75 | USB-C, standard USB 5 V power; GPIO 3.3 V logic | Owner's Amazon ASIN B0F7XTJ1ZL and supplied illustrations; primary target selected. Owner confirms no case. USB probe and running factory boot identify non-C 1.75; exact PCB revision/GPS fitment remain unknown. **Not 1.75C.** |
| ESP32-S3R8 | Dual-core Xtensa LX7 up to 240 MHz; 512 KB SRAM, 384 KB ROM; 8 MB octal PSRAM; external 16 MB flash | [Manufacturer overview](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75) and pinned BSP. USB esptool confirms ESP32-S3 rev0.2 with embedded 8 MB PSRAM and 16 MB flash; factory startup reports 8 MB PSRAM at 80 MHz and a passing SRAM test. SRAM/ROM totals and maximum CPU clock remain manufacturer specifications. |
| CO5300 display | 1.75-inch round AMOLED, 466 × 466, QSPI, advertised 16.7M colors; internal supply | Manufacturer specification. Brightness uses panel commands; no LED backlight GPIO. |
| CST9217 touch | Two-point capacitive touch over I2C; internal 3.3 V logic bus | Manufacturer reference. Face Lab 0.3.0 now initializes actual CST9217 identity/resolution successfully; owner confirms physical taps change the face; coordinate/edge calibration remains pending. |
| ES7210 + two microphones | Audio ADC, I2C configuration and I2S/TDM capture; internal power | Maintained BSP.0.6.0 measures a clear speech response on both microphone slots with no clipping, then stops capture. ES7210 is an ADC; echo cancellation needs software and playback reference. Seller wording does not verify working AEC. |
| ES8311 + NS4150B output | I2S codec/DAC and amplifier; MX1.25 2-pin SPK connector | Manufacturer reference. Owner confirms supplied speaker attached to SPK. Waveshare package specification lists 8 Ω / 2 W; physical markings/impedance have not been measured. 0.4.0 codec/TX transfer and cleanup pass; owner confirms the replayed beep; physical tap/face change also succeeds afterward. Speaker outputs must not connect to GPIO or ground. |
| AXP2101 PMIC | I2C; USB power and single-cell nominal 3.7 V lithium battery connector | Manufacturer reference. Battery presence/capacity/polarity/protection and charge current unknown. USB only initially. |
| QMI8658 IMU | Six axes, shared I2C, internal supply | Manufacturer specification; untested. |
| PCF85063 RTC | Shared I2C; backup through board battery power circuit | Specification; backup behavior untested. |
| TCA9554 expander | Shared I2C, 3.3 V logic | Specification; untested. |
| TF/microSD slot | 1-bit SDMMC, onboard 3.3 V card interface | Maintained BSP. No external SD adapter needed. |
| New nominal 128 GB microSD | Expected SDXC; onboard card supply 3.3 V | Owner reports insertion. Read-only CSD/boot-sector inspection now reports 124,383,133,696 raw bytes and exFAT signature, card_error=0. Brand/model and full-block integrity unknown; no filesystem mount or writes. |
| Radio | 2.4 GHz Wi-Fi 802.11 b/g/n, Bluetooth 5 LE | Manufacturer specification. Seller illustration says ax/b/g/n; use manufacturer b/g/n, not Wi-Fi 6. |
| H2 expansion | 8 positions, 2.54 mm; VBUS, GND, 3V3, UART0, GPIO16/17/18 | Manufacturer schematic numbering; physical left/right orientation must be checked before wiring. |

Evidence: `assets/sources/2026-10-29/waveshare-hardware-reference.md`, `waveshare-maintained-bsp.h.txt`, `waveshare-schematic.pdf`, and source manifest. These are pinned to manufacturer commit `e4344e70c2fa78a13e8a06566507f1ba8af6672a`.

## Waveshare reserved pins — recorded before coding

These are **internal PCB connections**, not jumper instructions. All GPIO logic is 3.3 V. Only USB is used in the initial diagnostic. Applies to **1.75**, not **1.75C**.

| Function | GPIO(s) / connection | Constraint |
| - | - | - |
| Native USB | D−19, D+20 | Reserved for USB data/flashing. |
| BOOT | 0, active low | Boot strap; diagnostic does not configure it. |
| Shared I2C | SDA15, SCL14 | Initialize once; onboard devices share bus. |
| AMOLED QSPI | SIO0=4, SIO1=5, SIO2=6, SIO3=7, CLK38, CS12 | Display bus. |
| AMOLED control | RESET39, TE13 | Separate touch reset. |
| Touch | RESET40, INT11 | Shared I2C controller. |
| Audio clocks | MCLK42, BCLK9, LRCK/WS45 | Shared codec/ADC clocks. |
| Speaker data | MCU DOUT8 → ES8311, PA control46 | NS4150B VCC3V3 supply, GPIO46 active-high enable; leave LOW except during requested playback. |
| Microphone data | MCU DIN10 ← ES7210 | Obtain TDM slot order from BSP. |
| SDMMC | CMD1, CLK2, D0=3 | 1-bit; not the Freenove map. |
| SD D3/CS | 41 | Wired but unused in 1-bit mode; not card detect. |
| IMU INT2 | 21 | INT1 through expander P6. |
| UART0 | TX43, RX44 | May carry console output. |
| Expansion | 16,17,18 | GPIO16 is the talk input. GPIO17/18 are conditional LED candidates recorded above, disabled and untouched in normal firmware until actual variant/circuit verification; GPS may share them. |
| PWR | PMIC path; SYS_OUT at TCA9554 P4 | Not a free MCU GPIO. Muse driver polls PMIC key latch. |

**Resolved source conflict:** legacy Arduino `pin_config.h` declares audio MCLK16 as well as MCLK42 in another section. Maintained BSP, hardware reference and Muse's non-C driver use **42**. GPIO16 remains expansion GPIO; do not build an audio driver from the conflicting old macro.

| H2 schematic pin | Signal |
| - | - |
| 1 | VBUS, USB power rail; never GPIO |
| 2 | GND |
| 3 | 3V3 |
| 4 | GPIO44 / UART RX |
| 5 | GPIO43 / UART TX |
| 6 | GPIO17 |
| 7 | GPIO18 |
| 8 | GPIO16 |

7-bit onboard I2C addresses: ES8311 `0x18`, TCA9554 `0x20`, AXP2101 `0x34`, ES7210 `0x40`, PCF85063 `0x51`, CST9217 `0x5A`, QMI8658 `0x6B`. Do not pass codec 8-bit address constants into 7-bit APIs.

### Physical USB/memory acceptance — 2026-10-29

Uploaded diagnostic version2: physical flash **16,777,216 bytes**, PSRAM physical capacity **8,388,608 bytes** from IDF4 `esp_spiram_get_size()`, Arduino usable PSRAM heap **8,386,295 bytes**, volatile **65,536-byte write/read PASS**, continuing PASS heartbeats. Arduino `ESP.getPsramSize()` reports heap free+allocated bytes in this core; do not compare it directly to chip capacity. Full factory flash backup was saved privately before upload. The current diagnostic does not initialize display, touch, audio or SD; factory initialization logs do not establish their visual/audio acceptance. Details in PROJECT-STATUS.md and ADR010.

## Mechanical and variant reference

Supplied dimension illustration: display assembly width 48.96 mm, visible round display 43.76 mm, PCB diameter 46.00 mm, illustrated bare depth up to 10.40 mm. Protective case diameter 51.00 mm, maximum illustrated depth 12.10 mm. Drawing values only; verify with calipers before final enclosure work. Original retained at `assets/reference-images/waveshare-1.75/user-dimensions.png`.

Standard SKU31261; `-B` case SKU31262; `-G` LC76G GNSS SKU31264. A pictured GPS connector does not prove fitted GPS, and an absent external antenna does not prove the onboard LC76G is absent. [Manufacturer onboard resource 13](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75) identifies the GPS option as an onboard module. **1.75C is a different board**; Muse lists 32 MB flash and different reset/audio pins.

## Existing Freenove equipment — earlier evidence retained

| Item | Interface / voltage | Evidence and status |
| - | - | - |
| Freenove ESP32 Wrover / WROVER E | USB-C data via CH340; 3.3 V GPIO | The board close-up shows the USB-C receptacle. Earlier photos/probe: ESP32 D0WD V3, 4 MB flash. Existing camera firmware build reproduced 2026-10-29. Secondary camera role. |
| Fitted camera | Parallel camera + SCCB on board connector | Prior sensor PID `0x009B`; RGB565 with software JPEG conversion, browser live stream visually confirmed at `http://192.168.4.1`. Commercial sensor model still unconfirmed. |
| QAPASS 1602A V1.4 / PCF8574T | I2C `0x27`, SDA33/SCL13, tested at 3.3 V | Interface/backlight verified; character area blank. Panel voltage/mapping unresolved. No contrast potentiometer. Old GPIO21/22 bus superseded. |
| Bare 8 × 8 LED matrix and two SN74HC595s | Row/column LED interface; pinout, drive current and supply unverified | Breadboard photo. Record the actual part marking and measure the topology before assigning any pins. |
| Other populated breadboard parts | Package marked L293D, single/four-digit and bar-graph LED packages; actual interface, supply, polarity and pin assignments unverified | Reinspection of the same owner breadboard photo on 2026-11-06 identifies their visible form/markings only. Keep disconnected; placement beside chips does not establish a completed circuit. |
| Earlier microSD cards | Onboard 1-bit SDMMC at 3.3 V | Prior raw: 240 MB; replacement 58 MB usable (~64 MB nominal); latest 960 MB raw / 958 MB usable (~1 GB nominal). None verifies the new card. |
| MPU6050 module | I2C; INT, AD0, XCL, XDA, SDA, SCL, GND, VCC | Photo identified. Breakout supply/regulator/pull-ups unknown. Keep disconnected. |
| Freenove audio board, PAM8403 visible | I2S-style converter labels plus speaker amplifier | Not a microphone. Supply, converter model, header order and speaker impedance unverified. Keep disconnected. |

Freenove SD: CMD15, CLK14, D0=2. Camera D0..D7=4,5,18,19,36,39,34,35; XCLK21, PCLK22, VSYNC25, HREF23, SIOD26, SIOC27; firmware PWDN/RESET=`-1`. See [SD and camera map](SD-CAMERA-PIN-MAP.md). These assignments do not apply to Waveshare.

## Portable power and talk button — 2026-10-30, reconciled 2026-11-06

Owner reports two AA cells and a connector. The retained kit-parts-list-b.jpg explicitly labels a 2× AA holder and a separate 9 V battery cable; kit-parts-list-a.jpg shows momentary buttons, switches and 10 kΩ resistors. These are kit illustrations. Cell chemistry, actual holder polarity/wiring and loaded voltage remain unknown. No suitable regulated boost converter is identified. Do not connect these holders/cables to BAT, 3V3 or GPIO.

Waveshare specifies BAT as an MX1.25 2-pin nominal 3.7 V rechargeable lithium charge/discharge interface, not AA input. The owner now chooses the existing two-AA holder; its route requires an identified regulated 5 V converter and proper USB source interface. A USB power bank and protected 1S lithium cell are separate alternatives, not selected hardware. The lithium route requires verified polarity/protection/charge settings. No battery connection has been performed. See [power plan](VOICE-AND-POWER-PLAN.md).

Face Lab 0.9.2 implements the previously reserved **GPIO16** talk input: `board_pins.h` defines `kTalkButton=16`, `main.cpp` uses `INPUT_PULLUP`, and `voice_transport.cpp` detects an active-low press with 35 ms debounce. This supersedes the earlier statement that no firmware was enabled. Connect only by actual **IO16** and **GND** labels; the schematic contact numbers are not physical assembly instructions because the retained product image orders H2 differently. Actual four-leg switch continuity and external wiring remain unverified. Muse's earlier evaluation used onboard BOOT/GPIO0, active low, for talk/pairing. Existing display TE13, reset39, touch reset40, audio MCLK42 and other non-C pins remain unchanged. USB-only testing does not establish a safe battery charge configuration.

## Safety boundary

- USB-only first setup; no breadboard or battery installation required.
- Never put 5 V logic on GPIO. VBUS is power, not a signal reference.
- Do not connect the boards' power rails. Future camera link is planned over Wi-Fi.
- Back up factory flash privately before replacement. No erase or eFuse/security changes for bring-up.
- New external peripherals require model, interface, voltage, pin map and evidence here before wiring or coding.

## Owner update and next slice — 2026-10-29

Owner reports the supplied speaker is now attached to SPK, the new 128 GB card is inserted, and USB is reconnected. These are owner observations, not audio or SD-function acceptance. Diagnostic version2 was read again after reconnect and still reports memory/buffer PASS.

Touch slice uses the recorded **CST9217**, I2C address `0x5A`, SDA15/SCL14, RESET40 and INT11 (3.3 V logic), following the pinned manufacturer `10_Touch_CST9217` example. SensorLib 0.3.1 supplies the existing driver; that dependency is needed for controller identification, reset and event reads. `TouchDrvCST92xx.begin(Wire,...)` owns the single bus initialization; future codecs must reuse it. The bus is set to100 kHz. Two-point arrays are allocated even though the UI uses only the first touch. A touch changes only the cosmetic face; no recording/network/audio action is attached.

The initial face-only slice used the already inventoried display GPIOs: CS12, CLK38, data4/5/6/7, RESET39; native USB19/20. Manufacturer `01_HelloWorld` specifies 466 × 466, rotation0, column offset6 and row offset0; these values are recorded here before the display code. First display speed is 40 MHz, matching the library default. Full-frame writes use even-aligned coordinates/sizes; brightness initially96/255 with a software range16–160. No speaker, touch, SD, I2C or PMIC driver is initialized in this slice.

After the face/USB slice passed, the next read-only card slice uses the previously recorded onboard 1-bit SDMMC pins CMD1/CLK2/D0=3 at a conservative400 kHz. No D1–D7 or card-detect/write-protect GPIOs are assigned. It reads CSD capacity and at most sector 0 plus one first-MBR-partition boot sector, without a filesystem mount or data writes. It deinitializes the SD host afterward. A filesystem signature is identification evidence, not a filesystem integrity or full-capacity test.

Card metadata acceptance: Face Lab 0.2.0 read 124,383,133,696 bytes reported by CSD (~115.84 GiB), identified an exFAT boot signature, then deinitialized SDMMC. Frame counters continued 1→22 after inspection. This does not prove every block or establish filesystem integrity. Current card remains unmounted.

Touch initialization acceptance: version 0.3.0 runtime reports display_ready=true, touch_ready=true after requiring CST9217 model and 466×466 resolution. The initial observation window recorded no tap events; owner interaction is pending, so no physical touch/face-change PASS is claimed.

### Speaker test evidence recorded before coding

The [manufacturer package specification](https://www.waveshare.com/product/esp32-s3-touch-amoled-1.75.htm) lists an 8 Ω / 2 W speaker. The pinned maintained BSP explicitly states NS4150B PA supply 3.3 V, codec DAC 3.3 V and GPIO46 active-high (`pa_reverted=false`). Sources retained as `waveshare-maintained-bsp.c.txt` and `waveshare-audio-example.ino.txt` in the source manifest. Use ES8311 address0x18 on the existing SDA15/SCL14 Wire bus; TX I2S MCLK42/BCLK9/WS45/DOUT8, 3.3V logic. Do not connect or enable MCU DIN10/ES7210 for this output-only test. The Arduino example uses codec clocks16kHz/256×MCLK. No battery/PMIC charging configuration is required by that example; do not guess new power settings if playback fails.

Acceptance defined before change: reproduce0.3.0 display/touch ready with advancing frames, build/upload the output-only module, explicitly request a bounded quiet440Hz/400ms tone, require successful I2C/DMA results and amplifier LOW afterward, continuing frames/touch, and owner listening confirmation. Software success alone is not acoustic acceptance.

### Microphone level-test design recorded before coding

The pinned Waveshare BSP header identifies physical ES7210 MIC1/MIC2 as front microphones, MIC3 as ES8311 analog playback reference, MIC4 unconnected. Serialized TDM order is **MIC1, MIC3/reference, MIC2, MIC4/unused**. These are published assignments; acoustic/reference separation still requires measurement. GPIO10 is 3.3 V MCU receive data; clocks remain MCLK42/BCLK9/WS45. PA46 stays LOW for microphone measurement. ES7210 configuration address is0x40 on existing Wire0 SDA15/SCL14.

Use an isolated RX-only four-slot 16-bit TDM diagnostic at 16 kHz with256×MCLK=4.096MHz. Installed IDF4 exposes `I2S_CHANNEL_FMT_MULTIPLE` and high-bit `I2S_TDM_ACTIVE_CH0..3` masks; these are not0..3 low-bit masks. Espressif's pinned standalone ES7210 component supports IDF>=4.4,<6 and the4.096MHz/16kHz coefficient. Its I2C adapter will reuse Arduino HAL bus0 without reinitialization. Use24dB PGA,0dB digital volume and2.87V microphone bias, matching Espressif codec-dev's3.3V analog/bias reference settings. Exact driver/bias/stop sources are retained in the manifest; these settings are not measured supply voltages.

Acceptance: reproduce0.4.0 display/touch baseline, compile/upload minimal RX module, explicit USB `mic` captures exactly32,000 frames per slot after 128 ms settling, reports only RMS/peak/clipped counts, visibly indicates measurement, then stops ADC/RX and clears volatile sample buffers. Require nonconstant, unclipped microphone samples and a repeatable quiet-versus-speech level increase; raw audio is never written or transmitted. Preserve separate speaker function; duplex/AEC and voice recognition remain future work.

### ES7210 analog-enable conflict — before0.5.1 correction

0.5.0 returns32,000 frames without transfer errors but RMS stays near `[5..11,2..3,4..9,1]`; cued tests show no established speech increase. The standalone esp-bsp initializer uses analog register0x40=`0xC3`, global power0x06=`0x04`, pair power0x4B/0x4C=`0x0F`. The maintained esp_codec_dev `es7210_start` uses analog0x40=`0x43`, global0x06=`0x00`; `es7210_mic_select` powers selected pairs with 0x4B/0x4C=`0x00`. Exact pinned source is retained. Apply those four maintained-driver values as one correction, preserving clock, gain, bias, TDM format and shutdown. Require measured sound response before accepting microphone function; ACK/DMA success alone is insufficient. This is codec analog power control, not a PMIC/battery configuration change. Individual responsible bits have not been isolated experimentally.

### Actual microphone acceptance —0.6.0

Owner-triggered four-second measurement follows an explicit USB arm, with MIC TEST READY/TAP THEN SPEAK followed by a red MIC LEVEL TEST indicator. Owner confirms tapping and speaking while red.64,000 frames per slot, error0/stage complete; room RMS `[10,2,8,1]` versus speech `[119,2,121,1]`, speech peaks `[746,26,724,13]`, no clipping. Slots0/2 respond11.9×/15.125× over preceding room levels; slots1/3 remain near noise. This supports usable microphone signal and published mapping, but does not verify playback-reference correlation, intelligibility or AEC. RX→TX tone succeeds afterward on the same session with continuing frames/touch and no restart. No PMIC/battery settings changed. Earlier low samples were in missed speech windows; the analog-power correction's individual causal effect was not isolated.

Unused arming expiry is physically observed at 60.19 seconds: no capture, capture/arm flags false, continuing display frames and no restart. Arm/cancel and owner tap-triggered disarming also pass. Current app remains0.6.0, idle Classic face, brightness96, microphone inactive and unarmed; amplifier commanded LOW.

### Host reply caption slice — 2026-10-30, before coding

Reproduce0.6.0 display/touch ready and advancing frames before changes. Existing466×466 CO5300 geometry, offsets and GPIOs stay unchanged. Add a bounded ASCII preview below the robot mouth: at most 96 stored characters, four lines of24 columns in the existing font, starting near y330; source label identifies the laptop/provider. Mic-ready/active indicators take priority. Captions live in RAM, clear on command/disconnect and expire60seconds after receipt. No new pin, voltage, filesystem or network operation is introduced. Acceptance: parser rejects malformed/control/oversized caption payloads without state changes, firmware builds, USB metadata acknowledges the caption without echoing its text, frames/touch continue, and owner sees the synthetic Gemini greeting on the round display. Full replies remain on the laptop; captions are a short preview, not a voice session.

### Display and touch recheck — 2026-11-14

Face Lab 0.10.0 reported `display_ready=true` and `touch_ready=true` on the inventoried CO5300 and CST9217. It accepted the four screen commands and committed a 180,000-byte RGB565 preview to Gallery. This is the application payload size. Physical swipe direction, edge tracking and image color appearance await observation on the panel. The microphone level diagnostic reported 64,000 frames and no driver error. No wiring changed. See [the system audit](SYSTEM-AUDIT-2026-11-14.md).
