#include "voice_transport.h"
#include "voice_protocol.h"
#include "microphone_input.h"
#include "audio_output.h"
#include "touch_input.h"
#include "board_pins.h"
#include "status_leds.h"
#include <Arduino.h>
#include <esp_heap_caps.h>
#include <cstring>

namespace mr_robot {
namespace {
uint8_t* buffer = nullptr;
size_t allocated = 0, available = 0, expected = 0;
uint32_t checksum = 0, touchedAt = 0, startedAt = 0;
uint16_t sessionId = 0;
bool released = false;
void clearBuffer() {
  if (buffer) {
    volatile uint8_t* p = buffer;
    for (size_t i = 0; i < allocated; ++i) p[i] = 0;
    heap_caps_free(buffer);
  }
  buffer = nullptr;
  allocated = available = expected = 0;
  checksum = 0;
}
bool allocate(size_t bytes) {
  clearBuffer();
  buffer = static_cast<uint8_t*>(heap_caps_malloc(bytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (!buffer) return false;
  allocated = bytes;
  std::memset(buffer, 0, bytes);
  return true;
}
AppState* playingState = nullptr;

bool cancelOnTap() {
  if (playingState && pollTalkButton(*playingState)) return true;
  const auto touch = pollTouch();
  if (touch.available) {
    if (!touch.points) released = true;
    else if (released) return true;
  }
  return false;
}
bool captureStream(AppState& state, VoicePhase phase, void (*refresh)(const AppState&)) {
  state.voicePhase = phase;
  if (refresh) refresh(state);
  if (state.microphoneActive || startMicrophoneStream(state)) {
    // Wake -> Recording keeps the same stream; its phase still changes the LED.
    updateStatusLeds(state.voicePhase, true, false);
    return true;
  }
  state.voicePhase = VoicePhase::Error;
  return false;
}

bool receiveBulk(uint8_t* destination, size_t size) {
  const uint32_t start = millis();
  size_t offset = 0;
  while (offset < size && millis() - start < 1000u) {
    const size_t count = Serial.read(destination + offset, size - offset);
    if (count) offset += count;
    else delay(1);
  }
  return offset == size;
}
void status(uint16_t id, const AppState& state, bool ok = true) {
  Serial.printf("MRV1 {\"id\":%u,\"ok\":%s,\"phase\":\"%s\",\"bytes\":%u,\"expected\":%u,\"crc32\":%lu,\"turns\":%lu}\n",
                id, ok ? "true" : "false", name(state.voicePhase), static_cast<unsigned>(available),
                static_cast<unsigned>(expected), static_cast<unsigned long>(checksum),
                static_cast<unsigned long>(state.voiceTurns));
}
}

bool pollTalkButton(AppState& state) {
  static bool raw = false, stable = false;
  static uint32_t changedAt = 0;
  const bool pressed = digitalRead(board::kTalkButton) == LOW;
  if (pressed != raw) {
    raw = pressed;
    changedAt = millis();
  }
  if (raw == stable || millis() - changedAt < 35u) return false;
  stable = raw;
  if (!stable) return false;
  ++state.talkButtonPresses;
  return true;
}

const char* name(VoicePhase phase) {
  switch (phase) {
    case VoicePhase::Idle: return "idle";
    case VoicePhase::Ready: return "ready";
    case VoicePhase::Wake: return "wake";
    case VoicePhase::Recording: return "recording";
    case VoicePhase::Thinking: return "thinking";
    case VoicePhase::Receiving: return "receiving";
    case VoicePhase::Speaking: return "speaking";
    case VoicePhase::Error: return "error";
  }
  return "error";
}

bool handleVoiceCommand(const char* line, AppState& state, void (*refresh)(const AppState&)) {
  if (std::strncmp(line, "MRV1 ", 5)) return false;
  const auto c = parseVoiceCommand(line);
  if (c.operation == VoiceOperation::Invalid) { status(c.id, state, false); return true; }
  if (c.operation == VoiceOperation::Arm || c.operation == VoiceOperation::ArmFast ||
      c.operation == VoiceOperation::Watch || c.operation == VoiceOperation::Local) {
    if (state.voicePhase != VoicePhase::Idle && state.voicePhase != VoicePhase::Error) {
      status(c.id, state, false); return true;
    }
    clearBuffer();
    sessionId = c.id;
    startedAt = touchedAt = millis();
    state.voiceStreaming = c.operation != VoiceOperation::Arm;
    state.voiceLocal = c.operation == VoiceOperation::Local;
    state.voiceFollowup = false;
    state.voiceReaction = VoiceReaction::Neutral;
    state.microphoneArmed = false;
    state.caption[0] = 0;
    state.voicePhase = VoicePhase::Ready;
    if ((c.operation == VoiceOperation::Watch || state.voiceLocal) &&
        !captureStream(state, state.voiceLocal ? VoicePhase::Recording : VoicePhase::Wake, refresh)) {
      status(c.id, state, false); return true;
    }
  } else if (c.id != sessionId) { status(c.id, state, false); return true; }
  else if (c.operation == VoiceOperation::Clear) {
    stopMicrophoneStream(state);
    clearBuffer();
    disableSpeaker();
    state.voiceFollowup = false;
    state.voiceLocal = false;
    state.voiceReaction = VoiceReaction::Neutral;
    state.voicePhase = VoicePhase::Idle;
  } else if (c.operation == VoiceOperation::Follow && state.voiceStreaming && state.voicePhase == VoicePhase::Idle) {
    startedAt = touchedAt = millis();
    state.voiceFollowup = true;
    state.voiceReaction = VoiceReaction::Neutral;
    if (!captureStream(state, VoicePhase::Recording, refresh)) {
      status(c.id, state, false);
      return true;
    }
  } else if (c.operation == VoiceOperation::Trigger && state.voicePhase == VoicePhase::Wake) {
    startedAt = millis();
    if (!captureStream(state, VoicePhase::Recording, refresh)) {
      status(c.id, state, false); return true;
    }
  } else if (c.operation == VoiceOperation::Finish && state.voiceStreaming && state.voicePhase == VoicePhase::Recording) {
    stopMicrophoneStream(state);
    state.voicePhase = state.micError == ESP_OK ? VoicePhase::Thinking : VoicePhase::Error;
    startedAt = millis();
    if (refresh) refresh(state);
  } else if (c.operation == VoiceOperation::Sample && state.microphoneActive &&
             (state.voicePhase == VoicePhase::Wake || state.voicePhase == VoicePhase::Recording)) {
    int16_t samples[kStreamFrames] = {};
    const bool ok = readMicrophoneStream(state, samples);
    if (ok) {
      const auto* bytes = reinterpret_cast<const uint8_t*>(samples);
      Serial.printf("MRV1 {\"id\":%u,\"ok\":true,\"phase\":\"%s\",\"sequence\":%lu,\"pcm\":%u,\"crc32\":%lu}\n",
                    c.id, name(state.voicePhase), static_cast<unsigned long>(state.micFrames / kStreamFrames),
                    static_cast<unsigned>(sizeof(samples)),
                    static_cast<unsigned long>(voiceCrc32(bytes, sizeof(samples))));
      if (Serial.write(bytes, sizeof(samples)) == sizeof(samples)) {
        touchedAt = millis();
      } else {
        stopMicrophoneStream(state);
        state.voicePhase = VoicePhase::Error;
      }
    } else {
      stopMicrophoneStream(state);
      state.voicePhase = VoicePhase::Error;
      status(c.id, state, false);
    }
    volatile int16_t* erase = samples;
    for (size_t i = 0; i < kStreamFrames; ++i) erase[i] = 0;
    return true;
  } else if (c.operation == VoiceOperation::Read && state.voicePhase == VoicePhase::Thinking && buffer && c.offset < available) {
    const size_t bytes = available - c.offset < kVoiceChunkBytes ? available - c.offset : kVoiceChunkBytes;
    char hex[kVoiceChunkBytes * 2 + 1];
    constexpr char digits[] = "0123456789abcdef";
    for (size_t i = 0; i < bytes; ++i) {
      const auto b = buffer[c.offset + i];
      hex[2 * i] = digits[b >> 4]; hex[2 * i + 1] = digits[b & 15];
    }
    hex[bytes * 2] = 0;
    Serial.printf("MRV1 {\"id\":%u,\"ok\":true,\"offset\":%lu,\"data\":\"%s\"}\n", c.id,
                  static_cast<unsigned long>(c.offset), hex);
    touchedAt = millis();
    return true;
  } else if (c.operation == VoiceOperation::Thinking && state.voicePhase == VoicePhase::Thinking) {
    clearBuffer(); // Host has verified input; do not retain speech while waiting.
  } else if (c.operation == VoiceOperation::React && state.voicePhase == VoicePhase::Thinking) {
    state.voiceReaction = static_cast<VoiceReaction>(c.offset);
  } else if (c.operation == VoiceOperation::Begin && (state.voicePhase == VoicePhase::Thinking || state.voicePhase == VoicePhase::Ready)) {
    if (!allocate(c.total)) { state.voicePhase = VoicePhase::Error; status(c.id, state, false); return true; }
    expected = c.total;
    checksum = c.crc;
    state.voicePhase = VoicePhase::Receiving;
  } else if (c.operation == VoiceOperation::Write && state.voicePhase == VoicePhase::Receiving &&
             buffer && c.offset == available && c.size <= expected - available) {
    std::memcpy(buffer + available, c.data, c.size);
    available += c.size;
  } else if (c.operation == VoiceOperation::Bulk && state.voicePhase == VoicePhase::Receiving &&
             buffer && c.offset == available && c.total <= expected - available) {
    if (!receiveBulk(buffer + available, c.total)) {
      clearBuffer();
      state.voicePhase = VoicePhase::Error;
      status(c.id, state, false);
      return true;
    }
    available += c.total;
  } else if (c.operation == VoiceOperation::Play && state.voicePhase == VoicePhase::Receiving &&
             available == expected && voiceCrc32(buffer, available) == checksum) {
    state.voicePhase = VoicePhase::Speaking;
    released = true;
    if (refresh) refresh(state);
    // Full-frame SPI flush blocks longer than the short TX DMA queue. Render
    // before playback, then keep I2S fed; physical cancel polling remains live.
    playingState = &state;
    const bool ok = playPcm(state, reinterpret_cast<const int16_t*>(buffer), available / 2, nullptr, cancelOnTap);
    playingState = nullptr;
    clearBuffer();
    if (ok) ++state.voiceTurns;
    state.voicePhase = ok ? VoicePhase::Idle : VoicePhase::Error;
    status(c.id, state, ok);
    return true;
  } else if (c.operation != VoiceOperation::Status) { status(c.id, state, false); return true; }
  // Status polling never extends arm/processing deadlines.
  if (c.operation != VoiceOperation::Status) touchedAt = millis();
  status(c.id, state);
  return true;
}

bool voiceTap(AppState& state, void (*refresh)(const AppState&)) {
  if (state.voicePhase == VoicePhase::Idle || state.voicePhase == VoicePhase::Error) return false;
  if (state.voiceStreaming && (state.voicePhase == VoicePhase::Ready || state.voicePhase == VoicePhase::Wake)) {
    startedAt = touchedAt = millis();
    captureStream(state, VoicePhase::Recording, refresh);
    return true;
  }
  if (state.voicePhase != VoicePhase::Ready) {
    const bool endFollowup = (state.voiceFollowup || state.voiceLocal) && state.voicePhase == VoicePhase::Recording;
    stopMicrophoneStream(state);
    clearBuffer();
    state.voiceFollowup = false;
    state.voicePhase = endFollowup ? VoicePhase::Idle : VoicePhase::Error;
    return true;
  }
  if (!allocate(kVoiceInputBytes)) { state.voicePhase = VoicePhase::Error; return true; }
  state.voicePhase = VoicePhase::Recording;
  released = false;
  const bool ok = recordMicrophone(state, reinterpret_cast<int16_t*>(buffer), kVoiceInputBytes / 2, refresh, cancelOnTap);
  if (ok) {
    available = kVoiceInputBytes;
    checksum = voiceCrc32(buffer, available);
    state.voicePhase = VoicePhase::Thinking;
    touchedAt = millis();
  } else { clearBuffer(); state.voicePhase = VoicePhase::Error; }
  return true;
}

void expireVoice(AppState& state) {
  if (state.voicePhase == VoicePhase::Idle || state.voicePhase == VoicePhase::Error) return;
  const uint32_t limit = state.microphoneActive ? 2500u : state.voicePhase == VoicePhase::Ready ? 60000u :
                         state.voicePhase == VoicePhase::Thinking ? 60000u : 15000u;
  const uint32_t totalLimit = state.voicePhase == VoicePhase::Wake ? 600000u : 180000u;
  if (millis() - touchedAt >= limit || millis() - startedAt >= totalLimit) {
    stopMicrophoneStream(state);
    clearBuffer(); disableSpeaker(); state.voicePhase = VoicePhase::Error;
  }
}
}  // namespace mr_robot
