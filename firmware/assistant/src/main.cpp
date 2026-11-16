#include <Arduino.h>
#include <esp_ota_ops.h>
#include "app_state.h"
#include "control_protocol.h"
#include "face_renderer.h"
#include "card_inspector.h"
#include "touch_input.h"
#include "audio_output.h"
#include "microphone_input.h"
#include "voice_transport.h"
#include "voice_protocol.h"
#include "board_pins.h"
#include "status_leds.h"
#include "image_transfer.h"

namespace {
mr_robot::AppState state;
char line[mr_robot::kMaxVoiceCommandBytes + 1];
size_t length = 0;
bool discardLine = false;
uint32_t microphoneArmedAt = 0;
uint32_t captionAt = 0;
uint32_t activityAt = 0;

void reply(uint16_t id, mr_robot::ParseError error) {
  if (error != mr_robot::ParseError::None) {
    Serial.printf("MRR1 {\"id\":%u,\"ok\":false,\"error\":\"%s\"}\n", id, mr_robot::name(error));
    return;
  }
  const auto leds = mr_robot::statusLedLevels();
  Serial.printf("MRR1 {\"id\":%u,\"ok\":true,\"protocol\":1,\"firmware\":\"face-lab-0.10.0\","
                "\"face\":\"%s\",\"expression\":\"%s\",\"brightness\":%u,"
                "\"display_ready\":%s,\"frames\":%lu,\"uptime_ms\":%lu,"
                "\"card_inspected\":%s,\"card_raw_bytes\":%llu,\"card_filesystem\":\"%s\",\"card_error\":%d,"
                "\"touch_ready\":%s,\"touch_events\":%lu,\"touch_x\":%d,\"touch_y\":%d,"
                "\"tone_tests\":%lu,\"audio_error\":%d,\"audio_stage\":\"%s\","
                "\"mic_tests\":%lu,\"mic_error\":%d,\"mic_stage\":\"%s\",\"mic_frames\":%lu,"
                "\"mic_rms\":[%u,%u,%u,%u],\"mic_peak\":[%u,%u,%u,%u],\"mic_clips\":[%lu,%lu,%lu,%lu],"
                "\"microphone_active\":%s,\"microphone_armed\":%s,"
                "\"caption_supported\":true,\"caption_available\":%s,\"caption_provider\":\"%s\",\"max_command_bytes\":1024,"
                "\"voice_supported\":true,\"voice_phase\":\"%s\",\"voice_turns\":%lu,"
                "\"local_voice_supported\":true,\"paged_caption_supported\":true,\"voice_stream_supported\":true,\"voice_conversation_supported\":true,\"talk_button_presses\":%lu,"
                "\"status_leds_supported\":true,\"status_leds_enabled\":%s,\"status_led_green\":%s,\"status_led_red\":%s,"
                "\"screens_supported\":true,\"screen\":\"%s\",\"activity_supported\":true,\"host_activity\":\"%s\","
                "\"image_supported\":true,\"image_available\":%s,"
                "\"network_enabled\":false,\"ai_connected\":false,\"sd_mounted\":false,\"speaker_enabled\":false}\n",
                id, mr_robot::name(state.face), mr_robot::name(state.expression), state.brightness,
                state.displayReady ? "true" : "false", static_cast<unsigned long>(state.frames),
                static_cast<unsigned long>(millis()), state.cardInspected ? "true" : "false",
                static_cast<unsigned long long>(state.cardRawBytes), state.cardFilesystem, state.cardError,
                state.touchReady ? "true" : "false", static_cast<unsigned long>(state.touchEvents),
                state.lastTouchX, state.lastTouchY, static_cast<unsigned long>(state.toneTests),
                state.audioError, state.audioStage, static_cast<unsigned long>(state.micTests), state.micError,
                state.micStage, static_cast<unsigned long>(state.micFrames),
                state.micRms[0], state.micRms[1], state.micRms[2], state.micRms[3],
                state.micPeak[0], state.micPeak[1], state.micPeak[2], state.micPeak[3],
                static_cast<unsigned long>(state.micClips[0]), static_cast<unsigned long>(state.micClips[1]),
                static_cast<unsigned long>(state.micClips[2]), static_cast<unsigned long>(state.micClips[3]),
                state.microphoneActive ? "true" : "false", state.microphoneArmed ? "true" : "false",
                state.caption[0] ? "true" : "false", mr_robot::name(state.captionProvider),
                mr_robot::name(state.voicePhase), static_cast<unsigned long>(state.voiceTurns),
                static_cast<unsigned long>(state.talkButtonPresses),
                mr_robot::kStatusLedsEnabled ? "true" : "false",
                leds.green ? "true" : "false", leds.red ? "true" : "false",
                mr_robot::name(state.screen), mr_robot::name(state.hostActivity),
                state.image ? "true" : "false");
}

void refreshCapture(const mr_robot::AppState& current) {
  if (state.displayReady) {
    mr_robot::renderFace(current, millis());
    ++state.frames;
  }
}

void bootMuse() {
  const auto *running = esp_ota_get_running_partition();
  const auto *target = esp_partition_find_first(ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_APP_OTA_0, nullptr);
  esp_app_desc_t description{};
  if (state.voicePhase != mr_robot::VoicePhase::Idle ||
      !running || running->address != 0x420000 || !target || target->address != 0x20000 ||
      esp_ota_get_partition_description(target, &description) != ESP_OK ||
      strcmp(description.project_name, "muse-gadget") != 0 ||
      esp_ota_set_boot_partition(target) != ESP_OK) {
    Serial.println("@boot error");
    return;
  }
  Serial.println("@boot ok");
  Serial.flush();
  ESP.restart();
}

void pollControl() {
  // Bounded work per iteration so input cannot starve rendering/watchdog.
  const int inputBudget = state.voicePhase == mr_robot::VoicePhase::Receiving ?
                          mr_robot::kMaxVoiceCommandBytes + 1 : 768;
  for (int budget = 0; budget < inputBudget && Serial.available() > 0; ++budget) {
    const char value = static_cast<char>(Serial.read());
    if (value == '\n') {
      if (discardLine) reply(0, mr_robot::ParseError::InvalidFrame);
      else if (length > 0) {
        line[length] = '\0';
        if (strcmp(line, ">host-face-status") == 0) {
          reply(65535, mr_robot::ParseError::None);
          length = 0;
          continue;
        }
        if (strcmp(line, ">boot=muse") == 0) {
          bootMuse();
          length = 0;
          continue;
        }
        if (mr_robot::handleVoiceCommand(line, state, refreshCapture)) {
          length = 0; discardLine = false; continue;
        }
        const auto command = mr_robot::parseCommand(line);
        if (state.microphoneActive && command.operation != mr_robot::Operation::Status) {
          reply(command.id, mr_robot::ParseError::InvalidCommand);
          length = 0; discardLine = false; continue;
        }
        if (mr_robot::imageOperation(command.operation)) {
          const auto result = mr_robot::receiveImage(command, state, millis());
          if (result == mr_robot::ParseError::None && command.operation != mr_robot::Operation::ImageEnd)
            Serial.printf("MRR1 {\"id\":%u,\"ok\":true}\n", command.id);
          else reply(command.id, result);
          length = 0; discardLine = false; continue;
        }
        if (mr_robot::applyCommand(command, state)) {
          if (command.operation == mr_robot::Operation::Activity) {
            activityAt = millis();
            if (state.hostActivity != mr_robot::HostActivity::Idle) state.screen = mr_robot::Screen::Face;
          }
          if (command.operation == mr_robot::Operation::Caption) state.screen = mr_robot::Screen::Face;
          if (state.displayReady && command.operation == mr_robot::Operation::Brightness)
            mr_robot::setDisplayBrightness(state.brightness);
          if (command.operation == mr_robot::Operation::Card) mr_robot::inspectCard(state);
          if (command.operation == mr_robot::Operation::Tone) mr_robot::testSpeaker(state);
          if (command.operation == mr_robot::Operation::Mic) mr_robot::testMicrophone(state, refreshCapture);
          if (command.operation == mr_robot::Operation::MicArm) {
            state.microphoneArmed = state.touchReady;
            microphoneArmedAt = millis();
          }
          if (command.operation == mr_robot::Operation::Caption) captionAt = millis();
        }
        reply(command.id, command.error);
      }
      length = 0;
      discardLine = false;
    } else if (value != '\r' && !discardLine) {
      if (length == mr_robot::kMaxVoiceCommandBytes || value < 32 || value > 126) discardLine = true;
      else line[length++] = value;
    }
  }
}
void tapScreen(int x) {
  using namespace mr_robot;
  if (state.screen == Screen::Settings) {
    const int next = static_cast<int>(state.brightness) + (x < board::kWidth / 2 ? -16 : 16);
    state.brightness = next < 16 ? 16 : next > 160 ? 160 : next;
    if (state.displayReady) setDisplayBrightness(state.brightness);
  } else if (state.screen == Screen::Face) {
    if (voiceTap(state, refreshCapture)) return;
    if (state.caption[0] && (state.captionProvider == HostProvider::Ollama ||
                             state.captionProvider == HostProvider::OllamaPrompt)) {
      ++state.captionPage;
      captionAt = millis();
    } else {
      state.face = state.face == Face::Classic ? Face::Pixel : state.face == Face::Pixel ? Face::Orbit : Face::Classic;
    }
  }
}

void handleTouch() {
  using namespace mr_robot;
  static bool fingerDown = false;
  static bool handled = false;
  static int firstX = 0, firstY = 0;
  static uint32_t pressedAt = 0;
  const auto touch = pollTouch();
  if (!touch.available) return;
  const bool navigationAllowed = state.voicePhase == VoicePhase::Idle || state.voicePhase == VoicePhase::Error ||
                                 state.voicePhase == VoicePhase::Wake || state.voicePhase == VoicePhase::Ready;
  if (touch.points) {
    state.lastTouchX = touch.x;
    state.lastTouchY = touch.y;
    if (!fingerDown) {
      fingerDown = true;
      handled = false;
      firstX = touch.x;
      firstY = touch.y;
      pressedAt = millis();
      ++state.touchEvents;
      if (!navigationAllowed) handled = voiceTap(state, refreshCapture);
      else if (state.microphoneArmed) {
        handled = true;
        testMicrophone(state, refreshCapture);
      }
    }
    return;
  }
  if (!fingerDown) return;
  fingerDown = false;
  if (handled || !navigationAllowed || millis() - pressedAt > 1200u) return;
  const int dx = state.lastTouchX - firstX;
  const int dy = state.lastTouchY - firstY;
  if (abs(dx) >= 58 && abs(dx) > abs(dy) * 2) {
    constexpr Screen screens[] = {Screen::Face, Screen::Settings, Screen::Status, Screen::Gallery};
    const unsigned current = static_cast<unsigned>(state.screen);
    state.screen = screens[(current + (dx < 0 ? 1 : 3)) % 4];
  } else if (abs(dx) < 32 && abs(dy) < 32) {
    tapScreen(firstX);
  }
}
}  // namespace

void setup() {
  mr_robot::beginStatusLeds();
  mr_robot::disableSpeaker();
  pinMode(mr_robot::board::kTalkButton, INPUT_PULLUP);
  Serial.setRxBufferSize(8192);
  Serial.setTxBufferSize(4096);
  Serial.begin(115200);
  delay(300);
  Serial.println("MR_ROBOT_FACE_LAB version=0.10.0");
  state.displayReady = mr_robot::beginDisplay(state.brightness);
  Serial.printf("DISPLAY_INIT=%s width=466 height=466\n", state.displayReady ? "PASS" : "FAIL");
  state.touchReady = mr_robot::beginTouch();
  Serial.printf("TOUCH_INIT=%s model=CST9217\n", state.touchReady ? "PASS" : "FAIL");
  if (state.displayReady) mr_robot::renderFace(state, millis());
}

void loop() {
  pollControl();
  mr_robot::expireVoice(state);
  if (mr_robot::pollTalkButton(state)) mr_robot::voiceTap(state, refreshCapture);
  if (state.caption[0] && millis() - captionAt >= 60000u) {
    mr_robot::Command clear;
    clear.error = mr_robot::ParseError::None;
    clear.operation = mr_robot::Operation::CaptionClear;
    mr_robot::applyCommand(clear, state);
  }
  if (state.microphoneArmed && millis() - microphoneArmedAt >= 60000u)
    state.microphoneArmed = false;
  if (state.hostActivity != mr_robot::HostActivity::Idle) {
    const bool working = state.hostActivity == mr_robot::HostActivity::Thinking ||
                         state.hostActivity == mr_robot::HostActivity::Drawing;
    if (millis() - activityAt >= (working ? 200000u : 3500u))
      state.hostActivity = mr_robot::HostActivity::Idle;
  }
  mr_robot::expireImageTransfer(millis());
  const auto previousScreen = state.screen;
  handleTouch();
  // A swipe updates wake pages once. Normal animation and all active question
  // capture/playback still avoid panel transfers while the microphone is on.
  const bool wakePageChanged = state.voicePhase == mr_robot::VoicePhase::Wake &&
                               previousScreen != state.screen;
  static uint32_t lastFrame = 0;
  static uint32_t lastHeartbeat = 0;
  const uint32_t frameInterval = state.voicePhase == mr_robot::VoicePhase::Receiving ? 1000u :
                                 state.voicePhase == mr_robot::VoicePhase::Thinking ? 250u : 100u;
  if (state.displayReady && (wakePageChanged ||
                            (!state.microphoneActive && millis() - lastFrame >= frameInterval))) {
    lastFrame = millis();
    mr_robot::renderFace(state, lastFrame);
    ++state.frames;
  }
  if (!state.microphoneActive && millis() - lastHeartbeat >= 5000u) {
    lastHeartbeat = millis();
    Serial.printf("FACE_HEARTBEAT display=%s frames=%lu free_heap=%lu free_psram=%lu\n",
                  state.displayReady ? "ready" : "failed", static_cast<unsigned long>(state.frames),
                  static_cast<unsigned long>(ESP.getFreeHeap()), static_cast<unsigned long>(ESP.getFreePsram()));
  }
  delay(2);
}
