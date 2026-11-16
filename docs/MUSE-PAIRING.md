# Muse Pairing and First Voice Test

**Paired and online (2026-11-13).** The owner turned on the Android phone's system **Location** setting, then Muse found and paired with the Waveshare. Developer mode and Bluetooth were already enabled. USB status confirmed `wifi_connected=true`, `paired=true`, link **Online**, and voice **Connected**. The standalone credential field remained false. This records the fix on the owner's Android 17 phone. Audible voice is a separate test. Face Lab 0.9.8 recovery images are saved.

**Before the fix.** Android's **Pair new device** and Muse's **Add Device** lists both missed the board. The Mac received its live BLE advertisement at −43 dBm and briefly connected to discover the pairing service and its RX/TX characteristics. It disconnected without writing or pairing. USB showed Wi-Fi connected and **Ready to pair**.

## Phone enrollment

1. Use the Muse phone account whose conversations Mr. Robot should use. Using the project account open on the laptop keeps project history together; matching the token-builder account is not a technical requirement established by our tests.
2. In Muse, open Settings → Devices and enable Developer mode so community gadgets appear. Start Add Device there, rather than the phone's general Bluetooth settings.
3. On Android, turn on the phone's system **Location** setting and allow Muse's **Nearby devices** permission. Keep the phone close and the board awake. Select the MuseGadget matching the name shown on the board.
4. Briefly press BOOT when the app asks for physical confirmation. Do not hold it for five seconds; a long setup hold can reset enrollment.
5. Supply Wi-Fi privately if requested. Tell the agent only whether pairing succeeded, never credentials.

## If discovery fails

Check system **Location** first on the owner's Android phone, then Muse's Nearby devices permission and Developer mode. Scan from **Add Device** inside Muse. The pinned SDK advertises continuously while unpaired. If discovery still fails, record the phone OS, Muse version if visible, and exact nonsecret error.

Public USB status, from the project root:

```sh
~/.platformio/penv/bin/python tools/muse.py -p PORT status
```

It prints the fixed board identity, booleans and allowlisted link/voice states. `paired=false` means Muse account enrollment is unfinished even if Wi-Fi works. `standalone_account_credential_configured` describes the separate Settings token; it can remain false after successful phone Link enrollment. Neither a stored token nor Wi-Fi proves service acceptance. The client preserves USB modem lines/HUPCL; separate hardware checks retained Wi-Fi and advanced uptime 82→85 seconds.

For a fresh phone attempt, start the bounded metadata monitor first:

```sh
~/.platformio/penv/bin/python tools/muse.py -p PORT -s 180 watch
```

It reports state changes and the firmware's physical-confirmation acknowledgement. It sends only status queries, discards other UART content, and never presses BOOT, resets the board or writes credentials. It stops after the requested 10–600 seconds or Ctrl-C. Use only one serial client at a time.

### Resumed Android discovery — 2026-10-31

Owner confirms the screen responds after reconnecting USB. Nearby Devices is already allowed; force-stopping/reopening Muse and scanning with Developer mode did not restore discovery. Owner reports Android 17; phone model and Muse version remain unknown. Owner declines installing a diagnostic phone app and authorizes one final Muse attempt, followed by the Google API route if unsuccessful.

A brief built-in USB JTAG inspection found BLE started/synced, advertising enabled/active, quiet mode off and connection handle 65535 (no client). The CPU was resumed and debug server closed. This verifies the firmware's advertising state at that instant, not reception over the air. No flash, credential, pin or eFuse change was made. A later USB monitor observed link `Connecting`, Wi-Fi connected and paired=false; this is still incomplete enrollment.

An independent [Nordic nRF Connect scan](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp) was proposed, but the owner declined installing it. Do not require this step or claim reception was verified. The SDK puts its local name in the scan response; this remains a source fact, not a scanner observation.

The final October attempt used one normal restart via the IDF esptool `run` command and a 300-second metadata watch. Wi-Fi reconnected. The board remained unpaired and the owner's Bluetooth toggle did not restore discovery. The November trial resolved discovery by enabling Android system Location.

## First audible conversation, after pairing

Start with a comfortable volume in the device's Sound settings. **Briefly tap the green IO16 button** to start a live call. Tap it again to hang up. Hold the green button, speak, then release it to send a voice note and receive text captions. The build allows 30 seconds of idle time and 180 seconds total.

**Audible reply verified, 2026-11-14.** After Control Room switched the board into Muse, a quick green-button tap opened the live call. USB showed the press and release, HTTP 200, the live session event, completed responses and 893 reply audio frames queued with zero dropped or invalid. The owner heard the reply from the ESP32 speaker. The client still uses the pinned SDK and the documented connection identity. The previous server-side failure stopped reproducing during this test and the cause of the recovery is unknown.

Post-pairing tests (2026-11-13): the owner heard the local Sound settings chirp with the speaker enabled. A quick BOOT tap displayed **Backend unavailable**. Holding BOOT while speaking and then releasing returned an on-screen answer and showed **Speaking**. The pinned SDK's `start_tts()` in `muse_chat_session.cpp` deliberately sets `s_turn.silent = true` to pace voice-note captions with silence. This explains the voice-note result. The experimental live call uses a separate realtime endpoint that must admit the call before reply audio can arrive.

A redacted USB trace of a side-by-side retry recorded HTTP 200 followed by an error event with no reported code and call-end counters of **0 reply audio frames queued, 0 dropped, 0 invalid**. HTTP 200 established the stream, and the error ended this attempt before the device queued any reply audio. The subsequent held-button turn logged the voice-note caption path. The specific backend cause remains unverified.

The board now runs the local non-C Muse patch. The existing green switch on **IO16 to GND** supplies the debounced talk edges. Onboard **BOOT/GPIO0** goes directly to physical pairing confirmation. The update wrote only the application at `0x20000` after verifying the partition table matched the previous build. The flash hash verified, and USB confirmed the board returned **Online** with its existing account pairing. See the [hardware inventory](HARDWARE-INVENTORY.md) and [firmware build](../firmware/muse-evaluation/README.md).

The owner confirmed that the Muse phone app speaks live replies on the same account when using its dedicated **Call** feature. After the IO16 update, a quick green-button tap showed **Connecting to Muse app**, then **Backend unavailable**. USB recorded two live-call attempts returning HTTP 200 followed by error type `backend_unavailable`, with zero reply audio frames queued on both. Holding the green button and releasing after speaking returned a visible answer, displayed **Speaking**, and stayed silent. USB confirmed the voice-note caption handler. The pinned client uses its documented `hatch-web` connection identity. The later upstream voice-call changes reviewed affect progress and turn handling, with no identified fix for this backend error.

## Desktop finding

The inspected signed-in Firefox web Devices panel shows “No devices found” and no Add Device/Developer mode control. The SDK's Web Bluetooth page can configure an existing device/account token but does not mint it. SDK token, account authorization and Wi-Fi are separate. Owner then chose phone once for enrollment. No web-session credential was extracted or placed on the board. The intended post-pairing Muse path uses board Wi-Fi without the phone acting as an ongoing gateway.

The signed-in Chrome Devices panel also shows “No devices found” and exposes no enrollment control. The pinned SDK Web Bluetooth helper supports a standalone device/account credential if already issued, and its VM ID field defaults to the account's default VM. The board's SDK token was provisioned separately. A fresh USB watch showed `paired=false` and no standalone credential even when the link label said `Connecting`. The Mac still received the unpaired advertisement.

[Pinned SDK instructions](https://github.com/facebookincubator/muse-gadget-sdk/blob/1b894f551e64416e2844452ec6056ec56d6a10f1/esp32/AGENTS.md), [voice/power plan](VOICE-AND-POWER-PLAN.md), [evaluation build](../firmware/muse-evaluation/README.md).


Owner observation update: Android discovery now reaches the physical-confirmation prompt. On the supplied reference image (`assets/reference-images/waveshare-1.75/user-board-features.png`), BOOT is item5 beside the lower-left mounting hole, with USB-C on the right. It is a tiny physical edge button, separate from the touch display and PWR. Briefly press/release; if confirmation expired, select the gadget in Muse again. This is not yet proof of completed pairing or audio.


The confirmation window is60seconds in this pinned SDK. If USB reports Ready to pair, select the gadget again before pressing BOOT; an old phone prompt may no longer have an active device session. A frozen-looking display is a separate observation: verify uptime/USB responsiveness and an explicit display test before concluding the whole board has hung or erasing setup.
