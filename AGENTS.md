# MR. Robot Project Rules

## Purpose

Build a secure, testable ESP32 based AI assistant in small, verified increments.

## Nonnegotiable rules

1. Treat hardware facts as unknown until recorded in `docs/HARDWARE-INVENTORY.md` with model, interface, voltage, and evidence.
2. Never connect a 5 V signal directly to an ESP32 GPIO. ESP32 GPIO is 3.3 V logic.
3. Do not hardcode API keys, WiFi credentials, tokens, or personal data. Keep local secrets in ignored files and document variable names only.
4. The ESP32 must not contain a long lived OpenRouter API key in a production design. Use an authenticated backend proxy for OpenRouter requests.
5. Implement one vertical slice at a time: hardware check, minimal firmware, measurable output, then documentation.
6. Make every hardware pin assignment explicit in the inventory before wiring or coding it.
7. Prefer small modules with one responsibility. Avoid adding a dependency until its need is demonstrated.
8. Keep build artifacts, logs, captured audio, and SD card data out of version control unless intentionally curated.
9. Before changing firmware, reproduce the current behavior and define a verification command or observable hardware result.
10. Update project documentation in the same change that establishes a new verified fact or decision.
11. Distinguish physical memory or storage capacity from heap or filesystem usable bytes. Record the API, units, and actual values before comparing a measurement with a hardware specification.
12. Status/diagnostic USB clients must preserve the native USB modem lines and clear POSIX HUPCL rather than resetting the board on open/close. Reserve resets for explicit operations. Use exclusive USB ownership so Control Room and diagnostics cannot consume each other's replies. Check advancing uptime across separate connections before attributing reconnects to firmware or hardware.

## Learning loop

When new evidence changes a project rule:

1. Record the evidence and decision in `docs/DECISIONS.md`.
2. Update the relevant hardware or architecture document.
3. Modify this file only when the finding is durable and applies to future work.
4. Remove or replace superseded guidance rather than stacking conflicting rules.
5. State the command, test, or physical observation that verifies the change.

## Definition of done

A feature is complete only when its firmware builds, its behavior is verified on hardware or clearly labeled unverified, its secrets are handled safely, and its documentation is current.
