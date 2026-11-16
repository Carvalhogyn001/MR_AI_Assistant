#include "status_leds.h"
#if MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS
#include "board_pins.h"
#include <Arduino.h>
#endif

namespace mr_robot {
namespace {
StatusLedLevels levels = {false, false};
#if MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS
bool initialized = false;
#endif
void apply(StatusLedLevels next) {
#if MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS
  if (!initialized || (next.green == levels.green && next.red == levels.red)) return;
  // Break before make: no moment with both outputs high during a transition.
  digitalWrite(board::kStatusGreenCandidate, LOW);
  digitalWrite(board::kStatusRedCandidate, LOW);
  if (next.green) digitalWrite(board::kStatusGreenCandidate, HIGH);
  if (next.red) digitalWrite(board::kStatusRedCandidate, HIGH);
  levels = next;
#else
  (void)next;
  // No Arduino include, pinMode, digitalWrite or GPIO read in the normal build.
  levels = {false, false};
#endif
}
}  // namespace

StatusLedLevels statusLedPolicy(VoicePhase phase, bool captureActive, bool playbackActive) {
  return {phase == VoicePhase::Recording && captureActive && !playbackActive,
          phase == VoicePhase::Speaking && playbackActive && !captureActive};
}
void beginStatusLeds() {
#if MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS
  // Set inactive latches before making either verified, active-high pin output.
  digitalWrite(board::kStatusGreenCandidate, LOW);
  digitalWrite(board::kStatusRedCandidate, LOW);
  pinMode(board::kStatusGreenCandidate, OUTPUT);
  pinMode(board::kStatusRedCandidate, OUTPUT);
  initialized = true;
#endif
  levels = {false, false};
}
void updateStatusLeds(VoicePhase phase, bool captureActive, bool playbackActive) {
  apply(statusLedPolicy(phase, captureActive, playbackActive));
}
void clearStatusLeds() { apply({false, false}); }
StatusLedLevels statusLedLevels() { return levels; }
}  // namespace mr_robot
