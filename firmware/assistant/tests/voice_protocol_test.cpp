#include "voice_protocol.h"
#include <cassert>
#include <cstring>
#include <string>
using namespace mr_robot;
int main() {
  assert(voiceCrc32(reinterpret_cast<const uint8_t*>("123456789"), 9) == 0xcbf43926u);
  assert(parseVoiceCommand("MRV1 1 arm").operation == VoiceOperation::Arm);
  const auto good = parseVoiceCommand("MRV1 65535 begin 960000 4294967295");
  assert(good.operation == VoiceOperation::Begin && good.total == 960000 && good.crc == UINT32_MAX);
  const auto chunk = parseVoiceCommand("MRV1 1 write 0 0080ff7f");
  assert(chunk.operation == VoiceOperation::Write && chunk.size == 4 && chunk.data[1] == 128 && chunk.data[2] == 255);
  const auto bulk = parseVoiceCommand("MRV1 1 bulk 8192 4096");
  assert(bulk.operation == VoiceOperation::Bulk && bulk.offset == 8192 && bulk.total == 4096);
  assert(parseVoiceCommand("MRV1 1 bulk 0 4098").operation == VoiceOperation::Invalid);
  assert(parseVoiceCommand("MRV1 1 bulk 0 3").operation == VoiceOperation::Invalid);
  for (const char* bad : {"", "MRV1 0 arm", "MRV1 65536 arm", "MRV1 1 arm extra", "MRV1 1 begin 960002 0",
       "MRV1 1 begin 3 0", "MRV1 1 begin 2 4294967296", "MRV1 1 write 0 00", "MRV1 1 write 0 zzzz",
       "MRV1 1 read -1", "MRV1 1 read 256001", "MRV1 1 play\n", "MRV1 1 write 42949672950 0000"})
    assert(parseVoiceCommand(bad).operation == VoiceOperation::Invalid);
  std::string boundary = "MRV1 1 write 0 " + std::string(1024, 'f');
  assert(parseVoiceCommand(boundary.c_str()).size == 512);
  boundary += "ffff";
  assert(parseVoiceCommand(boundary.c_str()).operation == VoiceOperation::Invalid);
  assert(parseVoiceCommand(std::string(1153, 'x').c_str()).operation == VoiceOperation::Invalid);
  for (unsigned i = 0; i < 2000; ++i) {
    const std::string fuzz(i % 1154, static_cast<char>(i % 128));
    (void)parseVoiceCommand(fuzz.c_str());
  }
}
