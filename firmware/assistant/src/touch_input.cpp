#include "touch_input.h"
#include "board_pins.h"
#include <Arduino.h>
#include <Wire.h>
#include <touch/TouchDrvCST92xx.h>
#include <cstring>

namespace mr_robot {
namespace {
TouchDrvCST92xx controller;
volatile bool pending = false;
bool ready = false;

void IRAM_ATTR onInterrupt() { pending = true; }
}  // namespace

bool beginTouch() {
  controller.setPins(board::kTouchReset, board::kTouchInterrupt);
  if (!controller.begin(Wire, CST92XX_SLAVE_ADDRESS, board::kI2cSda, board::kI2cScl)) return false;
  Wire.setClock(100000);
  int16_t width = 0, height = 0;
  if (!controller.getResolution(&width, &height) || width != board::kWidth || height != board::kHeight ||
      std::strcmp(controller.getModelName(), "CST9217") != 0) return false;
  pinMode(board::kTouchInterrupt, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(board::kTouchInterrupt), onInterrupt, FALLING);
  ready = true;
  return true;
}

TouchSample pollTouch() {
  TouchSample sample;
  if (!ready) return sample;
  noInterrupts();
  const bool event = pending;
  pending = false;
  interrupts();
  if (!event) return sample;
  // The pinned driver reads up to two points; keep both destination arrays sized accordingly.
  int16_t x[2] = {}, y[2] = {};
  sample.available = true;
  sample.points = controller.getPoint(x, y, 2);
  if (sample.points > 0 && x[0] >= 0 && x[0] < board::kWidth && y[0] >= 0 && y[0] < board::kHeight) {
    sample.x = x[0]; sample.y = y[0];
  } else sample.points = 0;
  return sample;
}
}  // namespace mr_robot
