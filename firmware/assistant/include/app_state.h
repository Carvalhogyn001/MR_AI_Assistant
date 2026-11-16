#pragma once
#include <cstdint>
#include <cstddef>

namespace mr_robot {
enum class Face { Classic, Pixel, Orbit };
enum class Expression { Neutral, Happy, Curious, Sleepy, Surprised, Wink, Excited, Concerned, Squint, Blush, Dizzy };
enum class Screen { Face, Settings, Status, Gallery };
enum class HostActivity { Idle, Thinking, Drawing, Done, Error };
constexpr uint16_t kImageSide = 300;
constexpr size_t kImageBytes = kImageSide * kImageSide * 2;
enum class HostProvider { None, Mock, Gemini, OpenRouter, Compatible, Ollama, OllamaPrompt };
enum class VoicePhase { Idle, Ready, Wake, Recording, Thinking, Receiving, Speaking, Error };
enum class VoiceReaction { Neutral, Happy, Curious, Soft };
constexpr size_t kMaxCaptionBytes = 480;

struct AppState {
  Face face = Face::Pixel;
  Expression expression = Expression::Neutral;
  Screen screen = Screen::Face;
  HostActivity hostActivity = HostActivity::Idle;
  uint16_t* image = nullptr;
  uint8_t brightness = 96;
  bool displayReady = false;
  uint32_t frames = 0;
  bool cardInspected = false;
  uint64_t cardRawBytes = 0;
  const char* cardFilesystem = "uninspected";
  int cardError = 0;
  bool touchReady = false;
  uint32_t touchEvents = 0;
  int16_t lastTouchX = -1;
  int16_t lastTouchY = -1;
  uint32_t toneTests = 0;  // Successful software transfers, not acoustic verification.
  int audioError = 0;
  const char* audioStage = "untested";
  bool microphoneActive = false;
  bool microphoneArmed = false;
  uint32_t micTests = 0;
  uint32_t micFrames = 0;
  int micError = 0;
  const char* micStage = "untested";
  uint16_t micRms[4] = {};
  uint16_t micPeak[4] = {};
  uint32_t micClips[4] = {};
  HostProvider captionProvider = HostProvider::None;
  char caption[kMaxCaptionBytes + 1] = {};
  uint8_t captionPage = 0;
  bool voiceLocal = false;
  VoicePhase voicePhase = VoicePhase::Idle;
  bool voiceStreaming = false;
  bool voiceFollowup = false;
  VoiceReaction voiceReaction = VoiceReaction::Neutral;
  uint32_t voiceTurns = 0;
  uint32_t talkButtonPresses = 0;
};

const char* name(Face face);
const char* name(Screen screen);
const char* name(HostActivity activity);
const char* name(Expression expression);
const char* name(HostProvider provider);
const char* name(VoicePhase phase);
}  // namespace mr_robot
