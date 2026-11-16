#include <cassert>
#include <string>
#include <vector>
#include "image_transfer.h"
#include "voice_protocol.h"

using namespace mr_robot;

int main() {
  AppState state;
  state.displayReady = true;
  std::vector<uint8_t> pixels(kImageBytes, 0x77);
  const auto checksum = voiceCrc32(pixels.data(), pixels.size());
  const auto begin = parseCommand(("MRR1 1 image-begin " + std::to_string(checksum)).c_str());
  const auto end = parseCommand("MRR1 42 image-end");
  assert(receiveImage(begin, state, 0) == ParseError::None);
  for (size_t offset = 0; offset < pixels.size(); offset += 240) {
    const std::string line = "MRR1 2 image-chunk " + std::to_string(offset) + " " + std::string(480, '7');
    const auto chunk = parseCommand(line.c_str());
    assert(receiveImage(chunk, state, offset / 240) == ParseError::None);
    assert(receiveImage(chunk, state, offset / 240) == ParseError::None);
  }
  assert(receiveImage(end, state, 751) == ParseError::None);
  assert(state.image && state.image[0] == 0x7777 && state.screen == Screen::Gallery);
  assert(receiveImage(end, state, 752) == ParseError::None);
  assert(receiveImage(begin, state, 753) == ParseError::None);
  assert(receiveImage(end, state, 754) == ParseError::InvalidValue);
  assert(state.image && state.image[0] == 0x7777);
  assert(receiveImage(begin, state, 755) == ParseError::None);
  expireImageTransfer(6000);
  assert(receiveImage(end, state, 6000) == ParseError::InvalidValue);
  state.voicePhase = VoicePhase::Recording;
  assert(receiveImage(begin, state, 6001) == ParseError::InvalidCommand);
  free(state.image);
}
