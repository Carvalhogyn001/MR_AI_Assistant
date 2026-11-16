#pragma once
#include <cstddef>
#include <cstdint>

namespace mr_robot {
constexpr size_t kVoiceChunkBytes = 512;
constexpr size_t kMaxVoiceCommandBytes = 1152;
constexpr size_t kVoiceInputBytes = 256000;  // Eight seconds, 16 kHz mono PCM16.
constexpr size_t kVoiceOutputBytes = 960000; // At most twenty seconds, 24 kHz PCM16.
constexpr size_t kVoiceBulkBytes = 4096;
enum class VoiceOperation { Invalid, Arm, ArmFast, Local, Watch, Follow, Trigger, Sample, Finish, Status, Clear,
                            Thinking, React, Read, Begin, Write, Bulk, Play };
struct VoiceCommand {
  uint16_t id = 0;
  VoiceOperation operation = VoiceOperation::Invalid;
  uint32_t offset = 0, total = 0, crc = 0;
  size_t size = 0;
  uint8_t data[kVoiceChunkBytes] = {};
};
VoiceCommand parseVoiceCommand(const char* line);
uint32_t voiceCrc32(const uint8_t* data, size_t bytes);
}  // namespace mr_robot
