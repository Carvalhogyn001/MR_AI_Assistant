#include <cassert>
#include <cstring>
#include <string>
#include "control_protocol.h"

using namespace mr_robot;

int main() {
  AppState state;
  auto command = parseCommand("MRR1 1 status");
  assert(command.id == 1 && command.error == ParseError::None);
  assert(applyCommand(command, state) && state.face == Face::Pixel);
  command = parseCommand("MRR1 2 card");
  assert(command.operation == Operation::Card && applyCommand(command, state));
  command = parseCommand("MRR1 3 tone");
  assert(command.operation == Operation::Tone && applyCommand(command, state));
  command = parseCommand("MRR1 4 mic");
  assert(command.operation == Operation::Mic && applyCommand(command, state));
  command = parseCommand("MRR1 5 mic-arm");
  assert(command.operation == Operation::MicArm && applyCommand(command, state));
  state.microphoneArmed = true;
  assert(applyCommand(parseCommand("MRR1 6 mic-cancel"), state) && !state.microphoneArmed);
  command = parseCommand("MRR1 65535 face orbit");
  assert(command.id == 65535 && applyCommand(command, state) && state.face == Face::Orbit);
  assert(applyCommand(parseCommand("MRR1 4 expression happy"), state));
  assert(state.expression == Expression::Happy);
  assert(applyCommand(parseCommand("MRR1 5 brightness 16"), state) && state.brightness == 16);
  assert(applyCommand(parseCommand("MRR1 6 brightness 160"), state) && state.brightness == 160);
  assert(applyCommand(parseCommand("MRR1 7 caption gemini 48656c6c6f"), state));
  assert(state.captionProvider == HostProvider::Gemini && std::strcmp(state.caption, "Hello") == 0);
  for (const char* input : {"MRR1 8 caption gemini 4", "MRR1 8 caption gemini zz", "MRR1 8 caption gemini 00",
       "MRR1 8 caption gemini 0a", "MRR1 8 caption gemini 1f", "MRR1 8 caption gemini 7f",
       "MRR1 8 caption gemini 80", "MRR1 8 caption unknown 4869", "MRR1 8 caption gemini 4869 extra"}) {
    assert(!applyCommand(parseCommand(input), state));
    assert(std::strcmp(state.caption, "Hello") == 0 && state.captionProvider == HostProvider::Gemini);
  }
  std::string captionFrame = "MRR1 9 caption compatible ";
  for (size_t i = 0; i < kMaxCaptionBytes; ++i) captionFrame += "41";
  assert(applyCommand(parseCommand(captionFrame.c_str()), state) && std::strlen(state.caption) == kMaxCaptionBytes);
  captionFrame += "41";
  assert(!applyCommand(parseCommand(captionFrame.c_str()), state));
  assert(applyCommand(parseCommand("MRR1 10 caption-clear"), state));
  assert(state.caption[0] == '\0' && state.captionProvider == HostProvider::None);

  // Invalid input must not mutate state, including valid-looking trailing data.
  for (const char* input : {"MRR1 0 face pixel", "MRR1 65536 face pixel", "MRR1 -1 face pixel",
       "MRR1 999999999999999999999999 face pixel", "MRR1 1 status unexpected",
       "MRR1 1 mic-arm now", "MRR1 1 mic-cancel now", "MRR1 1 mic 100", "MRR1 1 tone 100",
       "MRR1 1 face pixel extra", "MRR1 1 face unknown", "MRR1 1 expression recording",
       "MRR1 1 brightness 0", "MRR1 1 brightness 15", "MRR1 1 brightness 161",
       "MRR1 1 brightness 999999999999999999", "MRR1 1 brightness +80", "MRR1 1 brightness 80x",
       "MRR2 1 face pixel", "MRR1 1 reboot now", "MRR1\t1 status", "MRR1 1 face\npixel", ""}) {
    command = parseCommand(input);
    assert(command.error != ParseError::None && !applyCommand(command, state));
    assert(state.face == Face::Orbit && state.expression == Expression::Happy && state.brightness == 160);
  }
  assert(applyCommand(parseCommand("MRR1 11 screen gallery"), state) && state.screen == Screen::Gallery);
  assert(applyCommand(parseCommand("MRR1 12 activity drawing"), state) && state.hostActivity == HostActivity::Drawing);
  assert(parseCommand("MRR1 13 image-begin 4294967295").imageValue == UINT32_MAX);
  assert(parseCommand("MRR1 14 image-chunk 0 1122").error == ParseError::None);
  assert(parseCommand("MRR1 14 image-chunk 0 11").error == ParseError::InvalidValue);
  assert(parseCommand("MRR1 14 image-chunk 180001 1122").error == ParseError::InvalidValue);
  assert(parseCommand("MRR1 14 image-chunk 0 1aZ2").error == ParseError::InvalidValue);
  std::string oversized(500, 'A');
  assert(parseCommand(oversized.c_str()).error == ParseError::InvalidFrame);
  assert(parseCommand(nullptr).error == ParseError::InvalidFrame);
  assert(std::strcmp(name(state.face), "orbit") == 0);
}
