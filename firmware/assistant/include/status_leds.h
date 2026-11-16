#pragma once
#include "app_state.h"

// Physical parts/variant remain unverified. The default build does not even
// configure the conditional pins; see docs/HARDWARE-INVENTORY.md before opt-in.
#ifndef MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS
#define MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS 0
#endif
#if MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS != 0 && MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS != 1
#error "MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS must be 0 or 1"
#endif

namespace mr_robot {
struct StatusLedLevels { bool green; bool red; };
constexpr bool kStatusLedsEnabled = MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS == 1;

// Actual capture/playback activity gates the phase. These are turn indicators,
// not audio-level or speech-detection LEDs. Conflicting activity fails closed.
StatusLedLevels statusLedPolicy(VoicePhase phase, bool captureActive, bool playbackActive);
void beginStatusLeds();
void updateStatusLeds(VoicePhase phase, bool captureActive, bool playbackActive);
void clearStatusLeds();
StatusLedLevels statusLedLevels();

// Blocking audio paths must extinguish LEDs on every return, including errors
// and physical cancellation. Streamed capture has explicit stop/timeout hooks.
class StatusLedScope {
 public:
  StatusLedScope(VoicePhase phase, bool captureActive, bool playbackActive) {
    updateStatusLeds(phase, captureActive, playbackActive);
  }
  ~StatusLedScope() { clearStatusLeds(); }
  StatusLedScope(const StatusLedScope&) = delete;
  StatusLedScope& operator=(const StatusLedScope&) = delete;
};
}  // namespace mr_robot
