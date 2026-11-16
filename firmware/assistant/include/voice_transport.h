#pragma once
#include "app_state.h"
namespace mr_robot {
bool handleVoiceCommand(const char* line, AppState& state, void (*refresh)(const AppState&));
bool voiceTap(AppState& state, void (*refresh)(const AppState&));
void expireVoice(AppState& state);
bool pollTalkButton(AppState& state);
}  // namespace mr_robot
