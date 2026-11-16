#include "control_protocol.h"
#include <cstring>

namespace mr_robot {
namespace {
int hexDigit(char value) {
  if (value >= '0' && value <= '9') return value - '0';
  if (value >= 'a' && value <= 'f') return value - 'a' + 10;
  if (value >= 'A' && value <= 'F') return value - 'A' + 10;
  return -1;
}

bool decodeCaption(const char* hex, char* output) {
  const size_t bytes = std::strlen(hex);
  if (bytes == 0 || bytes > kMaxCaptionBytes * 2 || bytes % 2 != 0) return false;
  for (size_t i = 0; i < bytes; i += 2) {
    const int high = hexDigit(hex[i]), low = hexDigit(hex[i + 1]);
    if (high < 0 || low < 0) return false;
    const int value = high * 16 + low;
    if (value < 32 || value > 126) return false;
    output[i / 2] = static_cast<char>(value);
  }
  output[bytes / 2] = '\0';
  return true;
}

bool number(const char* value, unsigned maximum, unsigned& result) {
  if (*value == '\0') return false;
  result = 0;
  for (; *value; ++value) {
    if (*value < '0' || *value > '9') return false;
    const unsigned digit = static_cast<unsigned>(*value - '0');
    if (result > maximum / 10 || (result == maximum / 10 && digit > maximum % 10)) return false;
    result = result * 10 + digit;
  }
  return true;
}
}  // namespace

const char* name(Face face) {
  switch (face) {
    case Face::Classic: return "classic";
    case Face::Pixel: return "pixel";
    case Face::Orbit: return "orbit";
  }
  return "classic";
}
const char* name(Expression expression) {
  switch (expression) {
    case Expression::Neutral: return "neutral";
    case Expression::Happy: return "happy";
    case Expression::Curious: return "curious";
    case Expression::Sleepy: return "sleepy";
    case Expression::Concerned: return "concerned";
    case Expression::Excited: return "excited";
    case Expression::Wink: return "wink";
    case Expression::Surprised: return "surprised";
    case Expression::Squint: return "squint";
    case Expression::Blush: return "blush";
    case Expression::Dizzy: return "dizzy";
  }
  return "neutral";
}
const char* name(Screen screen) {
  switch (screen) {
    case Screen::Face: return "face";
    case Screen::Settings: return "settings";
    case Screen::Status: return "status";
    case Screen::Gallery: return "gallery";
  }
  return "face";
}
const char* name(HostActivity activity) {
  switch (activity) {
    case HostActivity::Idle: return "idle";
    case HostActivity::Thinking: return "thinking";
    case HostActivity::Drawing: return "drawing";
    case HostActivity::Done: return "done";
    case HostActivity::Error: return "error";
  }
  return "idle";
}
const char* name(HostProvider provider) {
  switch (provider) {
    case HostProvider::Mock: return "mock";
    case HostProvider::Gemini: return "gemini";
    case HostProvider::OpenRouter: return "openrouter";
    case HostProvider::Ollama: return "ollama";
    case HostProvider::OllamaPrompt: return "ollama-prompt";
    case HostProvider::Compatible: return "compatible";
    case HostProvider::None: return "none";
  }
  return "none";
}
const char* name(ParseError error) {
  switch (error) {
    case ParseError::None: return "none";
    case ParseError::InvalidFrame: return "invalid_frame";
    case ParseError::InvalidId: return "invalid_id";
    case ParseError::InvalidCommand: return "invalid_command";
    case ParseError::InvalidValue: return "invalid_value";
  }
  return "invalid_frame";
}

Command parseCommand(const char* line) {
  Command command;
  if (line == nullptr) return command;
  size_t length = 0;
  while (length <= kMaxCommandBytes && line[length] != '\0') ++length;
  if (length == 0 || length > kMaxCommandBytes) return command;
  char buffer[kMaxCommandBytes + 1];
  std::memcpy(buffer, line, length + 1);
  char* tokens[5] = {};
  size_t count = 0;
  char* cursor = buffer;
  while (*cursor != '\0') {
    while (*cursor == ' ') ++cursor;
    if (*cursor == '\0') break;
    if (count == 5) return command;
    tokens[count++] = cursor;
    while (*cursor != '\0' && *cursor != ' ') {
      // Protocol is printable ASCII; CR/LF are removed by the receiver.
      if (*cursor < 33 || *cursor > 126) return command;
      ++cursor;
    }
    if (*cursor != '\0') *cursor++ = '\0';
  }
  if (count < 3 || std::strcmp(tokens[0], "MRR1") != 0) return command;
  unsigned numeric = 0;
  if (!number(tokens[1], 65535, numeric) || numeric == 0) {
    command.error = ParseError::InvalidId;
    return command;
  }
  command.id = static_cast<uint16_t>(numeric);
  command.error = ParseError::InvalidCommand;
  if (std::strcmp(tokens[2], "status") == 0 && count == 3) {
    command.operation = Operation::Status;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "card") == 0 && count == 3) {
    command.operation = Operation::Card;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "tone") == 0 && count == 3) {
    command.operation = Operation::Tone;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "mic") == 0 && count == 3) {
    command.operation = Operation::Mic;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "mic-arm") == 0 && count == 3) {
    command.operation = Operation::MicArm;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "mic-cancel") == 0 && count == 3) {
    command.operation = Operation::MicCancel;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "caption-clear") == 0 && count == 3) {
    command.operation = Operation::CaptionClear;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "caption") == 0 && count == 5) {
    command.operation = Operation::Caption;
    command.error = ParseError::InvalidValue;
    if (std::strcmp(tokens[3], "mock") == 0) command.captionProvider = HostProvider::Mock;
    else if (std::strcmp(tokens[3], "gemini") == 0) command.captionProvider = HostProvider::Gemini;
    else if (std::strcmp(tokens[3], "openrouter") == 0) command.captionProvider = HostProvider::OpenRouter;
    else if (std::strcmp(tokens[3], "ollama") == 0) command.captionProvider = HostProvider::Ollama;
    else if (std::strcmp(tokens[3], "ollama-prompt") == 0) command.captionProvider = HostProvider::OllamaPrompt;
    else if (std::strcmp(tokens[3], "compatible") == 0) command.captionProvider = HostProvider::Compatible;
    else return command;
    if (!decodeCaption(tokens[4], command.caption)) return command;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "image-end") == 0 && count == 3) {
    command.operation = Operation::ImageEnd;
    command.error = ParseError::None;
    return command;
  }
  if (std::strcmp(tokens[2], "image-chunk") == 0 && count == 5) {
    command.operation = Operation::ImageChunk;
    command.error = ParseError::InvalidValue;
    if (!number(tokens[3], kImageBytes, numeric)) return command;
    command.imageValue = numeric;
    const size_t length = std::strlen(tokens[4]);
    if (!length || length > kMaxCaptionBytes || length % 4) return command;
    for (size_t i = 0; i < length; ++i) {
      if (hexDigit(tokens[4][i]) < 0) return command;
    }
    std::memcpy(command.caption, tokens[4], length);
    command.error = ParseError::None;
    return command;
  }
  if (count != 4) return command;
  command.error = ParseError::InvalidValue;
  if (std::strcmp(tokens[2], "face") == 0) {
    command.operation = Operation::Face;
    if (std::strcmp(tokens[3], "classic") == 0) command.face = Face::Classic;
    else if (std::strcmp(tokens[3], "pixel") == 0) command.face = Face::Pixel;
    else if (std::strcmp(tokens[3], "orbit") == 0) command.face = Face::Orbit;
    else return command;
  } else if (std::strcmp(tokens[2], "expression") == 0) {
    command.operation = Operation::Expression;
    if (std::strcmp(tokens[3], "neutral") == 0) command.expression = Expression::Neutral;
    else if (std::strcmp(tokens[3], "happy") == 0) command.expression = Expression::Happy;
    else if (std::strcmp(tokens[3], "curious") == 0) command.expression = Expression::Curious;
    else if (std::strcmp(tokens[3], "sleepy") == 0) command.expression = Expression::Sleepy;
    else if (std::strcmp(tokens[3], "concerned") == 0) command.expression = Expression::Concerned;
    else if (std::strcmp(tokens[3], "excited") == 0) command.expression = Expression::Excited;
    else if (std::strcmp(tokens[3], "wink") == 0) command.expression = Expression::Wink;
    else if (std::strcmp(tokens[3], "surprised") == 0) command.expression = Expression::Surprised;
    else if (std::strcmp(tokens[3], "squint") == 0) command.expression = Expression::Squint;
    else if (std::strcmp(tokens[3], "blush") == 0) command.expression = Expression::Blush;
    else if (std::strcmp(tokens[3], "dizzy") == 0) command.expression = Expression::Dizzy;
    else return command;
  } else if (std::strcmp(tokens[2], "screen") == 0) {
    command.operation = Operation::Screen;
    if (std::strcmp(tokens[3], "face") == 0) command.screen = Screen::Face;
    else if (std::strcmp(tokens[3], "settings") == 0) command.screen = Screen::Settings;
    else if (std::strcmp(tokens[3], "status") == 0) command.screen = Screen::Status;
    else if (std::strcmp(tokens[3], "gallery") == 0) command.screen = Screen::Gallery;
    else return command;
  } else if (std::strcmp(tokens[2], "activity") == 0) {
    command.operation = Operation::Activity;
    if (std::strcmp(tokens[3], "idle") == 0) command.activity = HostActivity::Idle;
    else if (std::strcmp(tokens[3], "thinking") == 0) command.activity = HostActivity::Thinking;
    else if (std::strcmp(tokens[3], "drawing") == 0) command.activity = HostActivity::Drawing;
    else if (std::strcmp(tokens[3], "done") == 0) command.activity = HostActivity::Done;
    else if (std::strcmp(tokens[3], "error") == 0) command.activity = HostActivity::Error;
    else return command;
  } else if (std::strcmp(tokens[2], "image-begin") == 0) {
    command.operation = Operation::ImageBegin;
    if (!number(tokens[3], UINT32_MAX, numeric)) return command;
    command.imageValue = numeric;
  } else if (std::strcmp(tokens[2], "brightness") == 0) {
    command.operation = Operation::Brightness;
    if (!number(tokens[3], 160, numeric) || numeric < 16) return command;
    command.brightness = static_cast<uint8_t>(numeric);
  } else {
    command.error = ParseError::InvalidCommand;
    return command;
  }
  command.error = ParseError::None;
  return command;
}

bool applyCommand(const Command& command, AppState& state) {
  if (command.error != ParseError::None) return false;
  switch (command.operation) {
    case Operation::Status: break;
    case Operation::Card: break;
    case Operation::Tone: break;
    case Operation::Mic: break;
    case Operation::MicArm: break;
    case Operation::MicCancel: state.microphoneArmed = false; break;
    case Operation::Caption:
      state.captionPage = 0;
      state.captionProvider = command.captionProvider;
      std::memcpy(state.caption, command.caption, sizeof(state.caption));
      break;
    case Operation::CaptionClear:
      state.captionProvider = HostProvider::None;
      std::memset(state.caption, 0, sizeof(state.caption));
      break;
    case Operation::Face: state.face = command.face; break;
    case Operation::Expression: state.expression = command.expression; break;
    case Operation::Screen: state.screen = command.screen; break;
    case Operation::Activity: state.hostActivity = command.activity; break;
    case Operation::ImageBegin:
    case Operation::ImageChunk:
    case Operation::ImageEnd: break;
    case Operation::Brightness: state.brightness = command.brightness; break;
  }
  return true;
}
}  // namespace mr_robot
