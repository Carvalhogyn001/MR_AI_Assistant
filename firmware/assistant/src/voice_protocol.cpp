#include "voice_protocol.h"
#include <cstring>

namespace mr_robot {
namespace {
bool number(const char* text, uint32_t maximum, uint32_t& out) {
  if (!*text) return false;
  out = 0;
  for (; *text; ++text) {
    if (*text < '0' || *text > '9') return false;
    const uint32_t digit = *text - '0';
    if (out > maximum / 10 || (out == maximum / 10 && digit > maximum % 10)) return false;
    out = out * 10 + digit;
  }
  return true;
}
int hex(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}
}
VoiceCommand parseVoiceCommand(const char* line) {
  VoiceCommand c;
  if (!line) return c;
  size_t size = 0;
  while (size <= kMaxVoiceCommandBytes && line[size]) ++size;
  if (!size || size > kMaxVoiceCommandBytes) return c;
  char copy[kMaxVoiceCommandBytes + 1];
  std::memcpy(copy, line, size + 1);
  char* parts[6] = {};
  size_t count = 0;
  char* p = copy;
  while (*p) {
    while (*p == ' ') ++p;
    if (!*p) break;
    if (count == 6) return c;
    parts[count++] = p;
    while (*p && *p != ' ') {
      if (*p < 33 || *p > 126) return c;
      ++p;
    }
    if (*p) *p++ = 0;
  }
  uint32_t id;
  if (count < 3 || std::strcmp(parts[0], "MRV1") || !number(parts[1], 65535, id) || !id) return c;
  c.id = id;
  if (count == 3) {
    if (!std::strcmp(parts[2], "arm")) c.operation = VoiceOperation::Arm;
    else if (!std::strcmp(parts[2], "arm-fast")) c.operation = VoiceOperation::ArmFast;
    else if (!std::strcmp(parts[2], "local")) c.operation = VoiceOperation::Local;
    else if (!std::strcmp(parts[2], "watch")) c.operation = VoiceOperation::Watch;
    else if (!std::strcmp(parts[2], "follow")) c.operation = VoiceOperation::Follow;
    else if (!std::strcmp(parts[2], "trigger")) c.operation = VoiceOperation::Trigger;
    else if (!std::strcmp(parts[2], "sample")) c.operation = VoiceOperation::Sample;
    else if (!std::strcmp(parts[2], "finish")) c.operation = VoiceOperation::Finish;
    else if (!std::strcmp(parts[2], "status")) c.operation = VoiceOperation::Status;
    else if (!std::strcmp(parts[2], "clear")) c.operation = VoiceOperation::Clear;
    else if (!std::strcmp(parts[2], "thinking")) c.operation = VoiceOperation::Thinking;
    else if (!std::strcmp(parts[2], "play")) c.operation = VoiceOperation::Play;
  } else if (count == 4 && !std::strcmp(parts[2], "react")) {
    if (number(parts[3], 3, c.offset)) c.operation = VoiceOperation::React;
  } else if (count == 4 && !std::strcmp(parts[2], "read")) {
    if (number(parts[3], kVoiceInputBytes, c.offset)) c.operation = VoiceOperation::Read;
  } else if (count == 5 && !std::strcmp(parts[2], "begin")) {
    if (number(parts[3], kVoiceOutputBytes, c.total) && c.total && c.total % 2 == 0 &&
        number(parts[4], UINT32_MAX, c.crc)) c.operation = VoiceOperation::Begin;
  } else if (count == 5 && !std::strcmp(parts[2], "bulk")) {
    if (number(parts[3], kVoiceOutputBytes, c.offset) &&
        number(parts[4], kVoiceBulkBytes, c.total) && c.total && c.total % 2 == 0)
      c.operation = VoiceOperation::Bulk;
  } else if (count == 5 && !std::strcmp(parts[2], "write")) {
    if (!number(parts[3], kVoiceOutputBytes, c.offset)) return c;
    const size_t length = std::strlen(parts[4]);
    if (!length || length > 2 * kVoiceChunkBytes || length % 4) return c;
    for (size_t i = 0; i < length; i += 2) {
      const int high = hex(parts[4][i]), low = hex(parts[4][i + 1]);
      if (high < 0 || low < 0) return c;
      c.data[i / 2] = static_cast<uint8_t>(high * 16 + low);
    }
    c.size = length / 2;
    c.operation = VoiceOperation::Write;
  }
  return c;
}
uint32_t voiceCrc32(const uint8_t* data, size_t bytes) {
  uint32_t crc = UINT32_MAX;
  for (size_t i = 0; i < bytes; ++i) {
    crc ^= data[i];
    for (int bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
  }
  return crc ^ UINT32_MAX;
}
}  // namespace mr_robot
