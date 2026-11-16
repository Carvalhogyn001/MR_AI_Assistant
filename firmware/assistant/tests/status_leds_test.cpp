#include "status_leds.h"
#include "board_pins.h"
#include <Arduino.h>
#include <cassert>
#include <cstdio>
#include <vector>
using namespace mr_robot;
namespace {
struct Event { bool mode; int pin; int value; };
std::vector<Event> events;
bool greenHigh = false, redHigh = false;
}
void digitalWrite(int pin, int value) {
  assert(pin == board::kStatusGreenCandidate || pin == board::kStatusRedCandidate);
  assert(value == LOW || value == HIGH);
  if (pin == board::kStatusGreenCandidate) greenHigh = value == HIGH;
  else redHigh = value == HIGH;
  assert(!(greenHigh && redHigh));
  events.push_back({false,pin,value});
}
void pinMode(int pin, int mode) {
  assert(pin == board::kStatusGreenCandidate || pin == board::kStatusRedCandidate);
  assert(mode == OUTPUT);
  // Both inactive latches must be set before either becomes an output.
  assert(events.size() >= 2 && !events[0].mode && events[0].value == LOW &&
         !events[1].mode && events[1].value == LOW);
  events.push_back({true,pin,mode});
}
void assertLevels(bool green, bool red) {
  const auto actual = statusLedLevels();
  assert(actual.green == (kStatusLedsEnabled && green));
  assert(actual.red == (kStatusLedsEnabled && red));
}
bool earlyReturnDuringPlayback(bool firstBufferAccepted) {
  StatusLedScope activity(VoicePhase::Idle,false,false);
  if (firstBufferAccepted) updateStatusLeds(VoicePhase::Speaking,false,true);
  assertLevels(false,firstBufferAccepted);
  return false;  // Models cancellation/error before or after PCM begins.
}
int main() {
  const VoicePhase phases[] = {VoicePhase::Idle,VoicePhase::Ready,VoicePhase::Wake,VoicePhase::Recording,
    VoicePhase::Thinking,VoicePhase::Receiving,VoicePhase::Speaking,VoicePhase::Error};
  for (const auto phase : phases) for (const bool capture : {false,true}) for (const bool playback : {false,true}) {
    const auto result=statusLedPolicy(phase,capture,playback);
    assert(!(result.green && result.red));
    if (phase != VoicePhase::Recording) assert(!result.green);
    if (phase != VoicePhase::Speaking) assert(!result.red);
    if (capture == playback) assert(!result.green && !result.red);
  }
  assert(statusLedPolicy(VoicePhase::Recording,true,false).green);
  assert(statusLedPolicy(VoicePhase::Speaking,false,true).red);
  // No premature GPIO operation, even if enabled, before explicit startup.
  updateStatusLeds(VoicePhase::Recording,true,false);
  clearStatusLeds();
  assert(events.empty());
  beginStatusLeds();
  assertLevels(false,false);
  if (kStatusLedsEnabled) assert(events.size()==4);
  else assert(events.empty());
  updateStatusLeds(VoicePhase::Wake,true,false); assertLevels(false,false);
  updateStatusLeds(VoicePhase::Recording,true,false); assertLevels(true,false);
  const auto sameStateEvents=events.size();
  updateStatusLeds(VoicePhase::Recording,true,false);
  assert(events.size()==sameStateEvents);  // No repeated writes in the same state.
  updateStatusLeds(VoicePhase::Speaking,false,true); assertLevels(false,true);
  updateStatusLeds(VoicePhase::Speaking,true,true); assertLevels(false,false);
  for (const auto phase : {VoicePhase::Thinking,VoicePhase::Receiving,VoicePhase::Idle,VoicePhase::Error}) {
    updateStatusLeds(VoicePhase::Recording,true,false);
    updateStatusLeds(phase,false,false); assertLevels(false,false);
  }
  assert(!earlyReturnDuringPlayback(false)); assertLevels(false,false);
  assert(!earlyReturnDuringPlayback(true)); assertLevels(false,false);
  { StatusLedScope activity(VoicePhase::Recording,true,false); assertLevels(true,false); }
  assertLevels(false,false);
  updateStatusLeds(VoicePhase::Recording,true,false);
  clearStatusLeds(); assertLevels(false,false);
  clearStatusLeds(); assertLevels(false,false);
  if (!kStatusLedsEnabled) assert(events.empty());
  std::puts(kStatusLedsEnabled ? "PASS: opted-in GPIO policy, break-before-make and scoped cleanup" :
                               "PASS: default disabled build performs zero GPIO operations");
}
