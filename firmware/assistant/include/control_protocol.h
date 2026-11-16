#pragma once
#include <cstddef>
#include <cstdint>
#include "app_state.h"

namespace mr_robot {
constexpr size_t kMaxCommandBytes = 1024;
enum class Operation { Status, Card, Tone, Mic, MicArm, MicCancel, Caption, CaptionClear, Face, Expression, Brightness, Screen, Activity, ImageBegin, ImageChunk, ImageEnd };
enum class ParseError { None, InvalidFrame, InvalidId, InvalidCommand, InvalidValue };
struct Command {
  uint16_t id = 0;
  Operation operation = Operation::Status;
  Face face = Face::Classic;
  Expression expression = Expression::Neutral;
  uint8_t brightness = 96;
  Screen screen = Screen::Face;
  HostActivity activity = HostActivity::Idle;
  uint32_t imageValue = 0;
  HostProvider captionProvider = HostProvider::None;
  char caption[kMaxCaptionBytes + 1] = {};
  ParseError error = ParseError::InvalidFrame;
};
Command parseCommand(const char* line);
bool applyCommand(const Command& command, AppState& state);
const char* name(ParseError error);
}  // namespace mr_robot
