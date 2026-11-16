#pragma once
#include "app_state.h"

namespace mr_robot {
using CaptureRefresh = void (*)(const AppState&);
// Measures levels only. No raw samples leave the local temporary buffer.
void testMicrophone(AppState& state, CaptureRefresh refresh);
// Explicit voice transfer: caller owns/clears buffer; MIC1, 16 kHz, signed PCM.
bool recordMicrophone(AppState& state, int16_t* output, size_t frames,
                      CaptureRefresh refresh, bool (*cancel)());
constexpr size_t kStreamFrames = 1024;  // 64 ms of mono PCM at 16 kHz.
bool startMicrophoneStream(AppState& state);
bool readMicrophoneStream(AppState& state, int16_t (&output)[kStreamFrames]);
void stopMicrophoneStream(AppState& state);
}
