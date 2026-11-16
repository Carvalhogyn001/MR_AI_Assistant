#pragma once
#include <cstdint>
#include "app_state.h"

namespace mr_robot {
bool beginDisplay(uint8_t brightness);
void setDisplayBrightness(uint8_t brightness);
void renderFace(const AppState& state, uint32_t nowMs);
}  // namespace mr_robot
