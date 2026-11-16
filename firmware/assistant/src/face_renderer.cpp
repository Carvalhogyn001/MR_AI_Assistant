#include "face_renderer.h"
#include "board_pins.h"
#include <Arduino_GFX_Library.h>
#include <esp_heap_caps.h>
#include <cmath>
#include <cstdio>
#include <cstring>

namespace mr_robot {
namespace {
constexpr uint16_t rgb(uint8_t r, uint8_t g, uint8_t b) {
  return ((r & 0xf8) << 8) | ((g & 0xfc) << 3) | (b >> 3);
}
constexpr uint16_t kBlack = 0;
constexpr uint16_t kText = rgb(226, 235, 240);
constexpr uint16_t kMuted = rgb(134, 157, 171);
constexpr uint16_t kTeal = rgb(102, 227, 209);
constexpr uint16_t kCoral = rgb(250, 166, 132);
constexpr uint16_t kLavender = rgb(179, 164, 251);
Arduino_ESP32QSPI bus(board::kDisplayCs, board::kDisplayClock, board::kDisplayData0,
                     board::kDisplayData1, board::kDisplayData2, board::kDisplayData3);
// GFX 1.5.9 has an IPS boolean before width/height (removed in 1.6.x).
Arduino_CO5300 panel(&bus, board::kDisplayReset, 0, false, board::kWidth, board::kHeight,
                    board::kColumnOffset, board::kRowOffset, 0, 0);

// Keep drawing in PSRAM and flush one even-aligned full panel window.
// CO5300 cannot reliably receive arbitrary odd primitive rectangles directly.
class PsramCanvas final : public Arduino_Canvas {
 public:
  PsramCanvas() : Arduino_Canvas(board::kWidth, board::kHeight, &panel) {}
  bool begin(int32_t speed) override {
    const size_t bytes = static_cast<size_t>(board::kWidth) * board::kHeight * 2;
    if (_framebuffer == nullptr) {
      _framebuffer = static_cast<uint16_t*>(
          heap_caps_aligned_alloc(16, (bytes + 15) & ~size_t(15), MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    }
    return _framebuffer != nullptr && Arduino_Canvas::begin(speed);
  }
};
PsramCanvas canvas;

void centered(const char* value, int y, uint8_t size, uint16_t color) {
  canvas.setTextSize(size);
  canvas.setTextColor(color);
  canvas.setCursor((board::kWidth - static_cast<int>(std::strlen(value)) * 6 * size) / 2, y);
  canvas.print(value);
}

void caption(const char* text) {
  size_t offset = 0;
  for (int row = 0; row < 4 && text[offset]; ++row) {
    while (text[offset] == ' ') ++offset;
    const size_t remaining = std::strlen(text + offset);
    size_t count = remaining < 24 ? remaining : 24;
    if (remaining > count && row < 3) {
      for (size_t split = count; split > 0; --split)
        if (text[offset + split] == ' ') { count = split; break; }
    }
    char line[25] = {};
    if (row == 3 && remaining > count) {
      count = 21;
      std::memcpy(line, text + offset, count);
      std::memcpy(line + count, "...", 3);
    } else std::memcpy(line, text + offset, count);
    centered(line, 326 + row * 19, 2, kText);
    offset += count;
  }
}

void ollamaCaption(const AppState& state) {
  constexpr unsigned rows = 7;
  constexpr unsigned widths[rows] = {13, 16, 17, 18, 17, 16, 13};
  constexpr int lineHeight = 45;
  char lines[kMaxCaptionBytes / 8 + 1][19] = {};
  const char* cursor = state.caption;
  unsigned count = 0;
  while (*cursor && count < sizeof(lines) / sizeof(lines[0])) {
    while (*cursor == ' ') ++cursor;
    if (!*cursor) break;
    const size_t remaining = std::strlen(cursor);
    const size_t limit = widths[count % rows];
    size_t length = remaining < limit ? remaining : limit;
    if (remaining > limit && cursor[length] != ' ') {
      // Prefer a word break while keeping at least half the line occupied.
      for (size_t split = length; split >= limit / 2; --split) {
        if (cursor[split] == ' ') {
          length = split;
          break;
        }
      }
    }
    std::memcpy(lines[count++], cursor, length);
    cursor += length;
  }
  if (!count) return;
  const unsigned pages = (count + rows - 1) / rows;
  const unsigned page = state.captionPage % pages;
  const unsigned remaining = count - page * rows;
  const unsigned visible = remaining < rows ? remaining : rows;
  const int top = (board::kHeight - 32 - (static_cast<int>(visible) - 1) * lineHeight) / 2;
  for (unsigned row = 0; row < visible; ++row) {
    centered(lines[page * rows + row], top + row * lineHeight, 4, kText);
  }
  if (pages > 1) {
    char hint[16];
    snprintf(hint, sizeof(hint), "%u/%u", page + 1, pages);
    centered(hint, 410, 1, kMuted);
  }
}

}  // namespace

bool beginDisplay(uint8_t brightness) {
  if (!canvas.begin(40000000)) return false;
  if (panel.width() != board::kWidth || panel.height() != board::kHeight) return false;
  canvas.setTextWrap(false);
  canvas.fillScreen(kBlack);
  panel.setBrightness(brightness);
  canvas.flush();
  return true;
}
void setDisplayBrightness(uint8_t brightness) { panel.setBrightness(brightness); }

namespace {
void pixelRobot(const AppState& state, uint32_t nowMs) {
  const auto phase = state.voicePhase;
  const bool speaking = phase == VoicePhase::Speaking;
  const bool listening = phase == VoicePhase::Recording || phase == VoicePhase::Wake;
  const bool thinking = phase == VoicePhase::Thinking || phase == VoicePhase::Receiving ||
                        state.hostActivity == HostActivity::Thinking || state.hostActivity == HostActivity::Drawing;
  auto expression = state.expression;
  if (speaking) {
    switch (state.voiceReaction) {
      case VoiceReaction::Happy: expression = Expression::Excited; break;
      case VoiceReaction::Curious: expression = Expression::Curious; break;
      case VoiceReaction::Soft: expression = Expression::Concerned; break;
      case VoiceReaction::Neutral: break;
    }
  }
  if (phase == VoicePhase::Idle) {
    if (state.hostActivity == HostActivity::Done) expression = Expression::Happy;
    if (state.hostActivity == HostActivity::Error) expression = Expression::Concerned;
  }
  const bool blink = !listening && !speaking && nowMs % 4100 < 140;
  const bool classic = state.face == Face::Classic;
  const bool orbit = state.face == Face::Orbit;
  const auto body = classic ? rgb(102, 227, 209) : orbit ? rgb(179, 164, 251) : rgb(112, 181, 255);
  const auto bright = classic ? rgb(192, 255, 236) : orbit ? rgb(226, 216, 255) : rgb(172, 219, 255);
  const auto shade = classic ? rgb(30, 125, 124) : orbit ? rgb(105, 80, 160) : rgb(56, 112, 178);
  const auto dark = rgb(14, 30, 52);
  const auto signal = listening ? kCoral : speaking ? kTeal : thinking ? kLavender : bright;
  const int bob = (!listening && !speaking && nowMs / 420 % 2) ? 4 : 0;
  const auto pixel = [bob](int x, int y, int w, int h, uint16_t color) {
    canvas.fillRect(78 + x * 10, 90 + y * 10 + bob, w * 10, h * 10, color);
  };
  pixel(14, 1, 3, 2, signal);
  pixel(15, 3, 1, 3, body);
  pixel(4, 6, 23, 2, bright);
  if (orbit) {
    pixel(1, 9, 29, 7, shade);
    pixel(4, 8, 23, 10, body);
    pixel(-2, 10, 2, 3, signal);
    pixel(31, 13, 2, 3, signal);
  } else {
    pixel(2, 8, 27, 10, body);
    pixel(0, 10, 2, 5, shade);
    pixel(29, 10, 2, 5, shade);
  }
  if (classic) pixel(5, 10, 21, 6, dark);
  pixel(4, 18, 23, 2, shade);
  pixel(6, 20, 5, 3, shade);
  pixel(20, 20, 5, 3, shade);
  pixel(6, 20, 5, 1, bright);
  pixel(20, 20, 5, 1, bright);
  const int look = thinking ? static_cast<int>(nowMs / 500 % 3) - 1 : 0;
  const auto eye = classic ? bright : dark;
  for (const int x : {7, 20}) {
    int height = 4;
    if (blink || expression == Expression::Sleepy || (expression == Expression::Wink && x == 20))
      height = 1;
    else if (expression == Expression::Squint && x == 7)
      height = 3;
    else if (expression == Expression::Surprised || (expression == Expression::Curious && x == 20))
      height = 6;
    else if (expression == Expression::Happy || expression == Expression::Excited || expression == Expression::Squint)
      height = 2;
    if (expression == Expression::Dizzy && !blink) {
      pixel(x, 10, 1, 1, eye);
      pixel(x + 3, 10, 1, 1, eye);
      pixel(x + 1, 11, 2, 2, eye);
      pixel(x, 13, 1, 1, eye);
      pixel(x + 3, 13, 1, 1, eye);
    } else pixel(x + look, 12 - height / 2, 4, height, eye);
    if (orbit && height >= 4) pixel(x + look + 1, 11, 2, 2, bright);
    if (expression == Expression::Concerned && !blink) {
      pixel(x + 1, 9, 3, 1, eye);
      pixel(x + (x == 7 ? 3 : 0), 8, 1, 1, eye);
    }
  }
  if (expression == Expression::Blush) {
    pixel(6, 15, 3, 1, kCoral);
    pixel(22, 15, 3, 1, kCoral);
    pixel(13, 16, 5, 1, dark);
  } else if (expression == Expression::Surprised) {
    pixel(14, 15, 3, 3, dark);
  } else if (expression == Expression::Happy || expression == Expression::Excited || expression == Expression::Wink) {
    pixel(12, 16, 7, expression == Expression::Excited ? 2 : 1, dark);
    pixel(12, 15, 1, 1, dark);
    pixel(18, 15, 1, 1, dark);
  } else if (expression == Expression::Concerned) {
    pixel(13, 16, 5, 1, dark);
    pixel(12, 17, 1, 1, dark);
    pixel(18, 17, 1, 1, dark);
  } else {
    pixel(13, 16, 5, speaking ? 2 : 1, dark);
  }
  if (listening || speaking || thinking) {
    const int bars = thinking ? 1 + nowMs / 300 % 3 : speaking ? 3 : 2;
    for (int i = 0; i < bars; ++i) {
      pixel(-3, 12 + i * 2, 1, 1, signal);
      pixel(33, 12 + i * 2, 1, 1, signal);
    }
  }
}

// Status symbols, not a measured waveform. Capture/playback deliberately avoid
// full-frame flushes so the display cannot starve the audio DMA queue.
void listening() {
  constexpr int heights[] = {24, 52, 86, 120, 86, 52, 24};
  for (int i = 0; i < 7; ++i)
    canvas.fillRoundRect(135 + i * 30, 220 - heights[i] / 2, 16, heights[i], 8, kCoral);
}
void header(const char* mode) {
  centered("MR. ROBOT", 55, 1, kText);
  centered(mode, 74, 1, kMuted);
}
void action(const char* value) { centered(value, 368, 1, kText); }
void footer(const char* value) { centered(value, 406, 1, kMuted); }

void renderPage(const AppState& state) {
  char value[32];
  if (state.screen == Screen::Gallery) {
    header("GALLERY");
    if (state.image) {
      constexpr int edge = (board::kWidth - kImageSide) / 2;
      canvas.draw16bitRGBBitmap(edge, edge, state.image, kImageSide, kImageSide);
    } else {
      centered("NO IMAGE YET", 205, 3, kText);
      centered("GENERATE IN CONTROL ROOM", 250, 1, kMuted);
    }
  } else if (state.screen == Screen::Settings) {
    header("SETTINGS");
    centered("BRIGHTNESS", 143, 3, kText);
    snprintf(value, sizeof(value), "%u", state.brightness);
    centered(value, 208, 6, kTeal);
    centered("-    +", 290, 4, kText);
    action("TAP LEFT OR RIGHT TO ADJUST");
  } else {
    header("DEVICE STATUS");
    centered(state.displayReady ? "DISPLAY READY" : "DISPLAY OFFLINE", 143, 2, kText);
    centered(state.touchReady ? "TOUCH READY" : "TOUCH OFFLINE", 205, 2, kTeal);
    snprintf(value, sizeof(value), "FRAMES %lu", static_cast<unsigned long>(state.frames));
    centered(value, 268, 2, kText);
    action("FACE LAB 0.10.0");
  }
  footer(state.voicePhase == VoicePhase::Wake || state.microphoneActive ?
         "MIC ON / SWIPE FOR SCREENS" : "MIC OFF / SWIPE FOR SCREENS");
}
}  // namespace

void renderFace(const AppState& state, uint32_t nowMs) {
  canvas.fillScreen(kBlack);
  // Microphone diagnostics have priority over stale captions or an earlier
  // voice error. Never show an idle/MIC OFF screen while capture is active.
  const bool voiceCapture = state.voicePhase == VoicePhase::Wake || state.voicePhase == VoicePhase::Recording;
  if ((state.microphoneActive && !voiceCapture) || state.microphoneArmed) {
    header("LOCAL DIAGNOSTIC");
    if (state.microphoneActive) {
      listening();
      centered("MIC LEVEL TEST", 316, 2, kCoral);
      char level[32];
      snprintf(level, sizeof(level), "LEVEL L:%u R:%u", state.micRms[0], state.micRms[2]);
      action(level);
      footer("MIC ON / LOCAL TEST");
    } else {
      pixelRobot(state, nowMs);
      centered("MIC TEST READY", 326, 2, kText);
      action("TAP THEN SPEAK");
      footer("MIC OFF / LOCAL TEST");
    }
  } else if (state.screen != Screen::Face && (state.voicePhase == VoicePhase::Idle ||
             state.voicePhase == VoicePhase::Wake || state.voicePhase == VoicePhase::Ready)) {
    renderPage(state);
  } else if (state.voicePhase != VoicePhase::Idle) {
    header(state.voiceLocal ? "OLLAMA / MAC" :
           state.voicePhase == VoicePhase::Wake ? "LOCAL WAKE DETECTOR" : "GEMINI LIVE / MAC");
    switch (state.voicePhase) {
      case VoicePhase::Ready:
        pixelRobot(state, nowMs);
        centered("READY TO TALK", 326, 2, kText);
        action("TAP TO BEGIN");
        footer("MIC OFF / VOICE ARMED");
        break;
      case VoicePhase::Wake:
        pixelRobot(state, nowMs);
        canvas.fillCircle(233, 153, 5, kCoral);
        centered("WAKE LISTENING", 326, 2, kCoral);
        action("SAY HEY MR. ROBOT OR PRESS BUTTON");
        footer("MIC ON / OR TAP TO TALK");
        break;
      case VoicePhase::Recording:
        pixelRobot(state, nowMs);
        centered("LISTENING", 328, 2, kCoral);
        if (state.voiceFollowup) centered("ASK A FOLLOW-UP", 349, 1, kMuted);
        else if (state.voiceStreaming) centered("PAUSE TO FINISH", 349, 1, kMuted);
        else {
          char time[32];
          const unsigned elapsed = state.micFrames / 16000;
          snprintf(time, sizeof(time), "%u SECONDS LEFT", elapsed < 8 ? 8 - elapsed : 0);
          centered(time, 349, 1, kMuted);
        }
        action("TAP TO CANCEL");
        footer(state.voiceLocal ? "MIC ON / LOCAL ON MAC" : "MIC ON / GEMINI VIA MAC");
        break;
      case VoicePhase::Thinking:
        pixelRobot(state, nowMs);
        centered("THINKING", 328, 2, kLavender);
        action("TAP TO CANCEL");
        footer(state.voiceLocal ? "MIC OFF / LOCAL ON MAC" : "MIC OFF / GEMINI VIA MAC");
        break;
      case VoicePhase::Receiving:
        pixelRobot(state, nowMs);
        centered("GETTING REPLY", 322, 2, kLavender);
        action("TAP TO CANCEL");
        footer(state.voiceLocal ? "MIC OFF / LOCAL ON MAC" : "MIC OFF / GEMINI VIA MAC");
        break;
      case VoicePhase::Speaking:
        pixelRobot(state, nowMs);
        centered("SPEAKING", 328, 2, kTeal);
        action("TAP TO CANCEL");
        footer(state.voiceLocal ? "MIC OFF / LOCAL ON MAC" : "MIC OFF / GEMINI VIA MAC");
        break;
      case VoicePhase::Error:
        pixelRobot(state, nowMs);
        centered("!", 185, 3, kCoral);
        // The transport uses Error for cancellation and faults alike.
        // Do not invent a cause, retry gesture, or working connection.
        centered("VOICE STOPPED", 322, 2, kCoral);
        action("CHECK CONTROL ROOM");
        footer("MIC OFF / RESTART ON MAC");
        break;
      case VoicePhase::Idle: break;
    }
  } else if (state.hostActivity != HostActivity::Idle &&
             (state.hostActivity != HostActivity::Done || !state.caption[0])) {
    header("CONTROL ROOM / MAC");
    pixelRobot(state, nowMs);
    const char* label = state.hostActivity == HostActivity::Drawing ? "DRAWING IMAGE" :
                        state.hostActivity == HostActivity::Done ? "REPLY READY" :
                        state.hostActivity == HostActivity::Error ? "REQUEST STOPPED" : "THINKING";
    centered(label, 327, 2, state.hostActivity == HostActivity::Error ? kCoral : kLavender);
    footer("MIC OFF");
  } else if (state.caption[0] && (state.captionProvider == HostProvider::Ollama ||
                                  state.captionProvider == HostProvider::OllamaPrompt)) {
    ollamaCaption(state);
  } else {
    header(state.caption[0] ? "HOST REPLY" : "FACE LAB");
    pixelRobot(state, nowMs);
    if (state.caption[0]) {
      caption(state.caption);
      char source[32];
      snprintf(source, sizeof(source), "%s / MAC / MIC OFF", name(state.captionProvider));
      footer(source);
    } else {
      centered(name(state.face), 332, 2, kText);
      action(state.touchReady ? "TAP FACE / SWIPE FOR SCREENS" : "USB CONTROL");
      footer("MIC OFF / VOICE NOT ARMED");
    }
  }
  canvas.flush();
}
}  // namespace mr_robot
