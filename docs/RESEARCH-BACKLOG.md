# Research Backlog

Research is accepted into the project only when its source, applicability, and verification plan are recorded in `DECISIONS.md`.

## Priority research

1. Finish actual Waveshare USB/memory acceptance, then verify non-C display/touch and audio with the maintained BSP.
2. Read supplied speaker markings/rating and confirm SPK connector fit before powered playback. Battery presence, protection, polarity and charging settings remain unknown.
3. Inspect the new reported 128 GB card's actual capacity/filesystem; never format automatically. Replace older unsupported 256 GB assumptions.
4. Evaluate pinned Muse `s3n` build with ESP-IDF6.0.1, owner Muse app/account and private token provisioning.
5. Benchmark a small offline ESP-SR command set alongside UI/audio memory. Investigate richer local inference on a host after host inventory.
6. Select authenticated backend deployment, device credential handling, request/response bounds and speech providers before API integration.
7. Revisit Freenove camera LAN/security only when the primary assistant works. Existing camera/SD pins are already documented; older amplifier diagnosis is deferred.

## Research standard

Every recommendation must distinguish manufacturer specification, verified hardware observation, and assumption. Do not copy a random pin map or wiring diagram without matching it to the exact board revision.
