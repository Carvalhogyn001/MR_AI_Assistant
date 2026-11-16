#pragma once
#include <cstdint>

namespace mr_robot {
struct TouchSample {
  bool available = false;
  uint8_t points = 0;
  int16_t x = -1;
  int16_t y = -1;
};
bool beginTouch();
TouchSample pollTouch();
}  // namespace mr_robot
