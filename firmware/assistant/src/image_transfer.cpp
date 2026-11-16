#include "image_transfer.h"
#include "voice_protocol.h"
#include <esp_heap_caps.h>
#include <cstring>

namespace mr_robot {
namespace {
uint8_t* pending = nullptr;
size_t received = 0;
uint32_t checksum = 0;
uint32_t lastChunk = 0;
uint16_t completedRequest = 0;
size_t lastSize = 0;

void discard() {
  if (pending) heap_caps_free(pending);
  pending = nullptr;
  received = 0;
  lastSize = 0;
}

uint8_t digit(char c) {
  if (c <= '9') return c - '0';
  return (c | 0x20) - 'a' + 10;
}
}

bool imageOperation(Operation operation) {
  return operation == Operation::ImageBegin || operation == Operation::ImageChunk ||
         operation == Operation::ImageEnd;
}

void expireImageTransfer(uint32_t now) {
  if (pending && now - lastChunk > 5000u) discard();
}

ParseError receiveImage(const Command& command, AppState& state, uint32_t now) {
  if (command.error != ParseError::None) return command.error;
  if (!state.displayReady || state.microphoneArmed || state.voicePhase != VoicePhase::Idle)
    return ParseError::InvalidCommand;
  if (command.operation == Operation::ImageBegin) {
    discard();
    completedRequest = 0;
    pending = static_cast<uint8_t*>(heap_caps_malloc(kImageBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    if (!pending) return ParseError::InvalidCommand;
    checksum = command.imageValue;
    lastChunk = now;
    return ParseError::None;
  }
  if (command.operation == Operation::ImageEnd) {
    if (!pending) return command.id == completedRequest ? ParseError::None : ParseError::InvalidValue;
    if (received != kImageBytes || voiceCrc32(pending, received) != checksum) {
      discard();
      return ParseError::InvalidValue;
    }
    if (state.image) heap_caps_free(state.image);
    state.image = reinterpret_cast<uint16_t*>(pending);
    state.screen = Screen::Gallery;
    state.hostActivity = HostActivity::Idle;
    pending = nullptr;
    received = 0;
    completedRequest = command.id;
    return ParseError::None;
  }
  if (!pending) return ParseError::InvalidValue;
  const size_t bytes = std::strlen(command.caption) / 2;
  const size_t offset = command.imageValue;
  const bool duplicate = bytes == lastSize && offset == received - lastSize;
  if (!duplicate && (offset != received || bytes > kImageBytes - received)) return ParseError::InvalidValue;
  for (size_t index = 0; index < bytes; ++index) {
    const uint8_t value = (digit(command.caption[index * 2]) << 4) | digit(command.caption[index * 2 + 1]);
    if (duplicate && pending[offset + index] != value) return ParseError::InvalidValue;
    pending[offset + index] = value;
  }
  if (!duplicate) received += bytes;
  lastSize = bytes;
  lastChunk = now;
  return ParseError::None;
}
}  // namespace mr_robot
