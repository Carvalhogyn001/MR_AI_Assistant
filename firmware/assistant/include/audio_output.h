#pragma once
#include "app_state.h"

namespace mr_robot {
void disableSpeaker();
// Explicit diagnostic only: fixed level/duration, no input or persistent files.
void testSpeaker(AppState& state);
bool playPcm(AppState& state, const int16_t* samples, size_t frames,
             void (*refresh)(const AppState&), bool (*cancel)());
}
