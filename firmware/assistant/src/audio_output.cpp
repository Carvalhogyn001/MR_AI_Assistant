#include "audio_output.h"
#include "board_pins.h"
#include "status_leds.h"
#include <Arduino.h>
#include <Wire.h>
#include <driver/i2s.h>
#include <es8311.h>
#include <cmath>

namespace mr_robot {
namespace {
constexpr i2s_port_t kPort = I2S_NUM_0;
constexpr uint32_t kRate = 16000;
constexpr size_t kChunkFrames = 128;
constexpr size_t kToneFrames = kRate * 400 / 1000;
constexpr size_t kFadeFrames = kRate * 20 / 1000;
constexpr int kPeak = 2048;  // -24 dBFS peak, with further DAC attenuation.

class OutputSession {
 public:
  bool installed = false;
  es8311_handle_t codec = nullptr;

  esp_err_t close() {
    // Physical amplifier shutdown has priority even if codec I2C fails.
    disableSpeaker();
    esp_err_t result = ESP_OK;
    if (codec) {
      result = es8311_voice_mute(codec, true);
      es8311_delete(codec);
      codec = nullptr;
    }
    if (installed) {
      const auto stopped = i2s_driver_uninstall(kPort);
      if (result == ESP_OK) result = stopped;
      installed = false;
    }
    return result;
  }
  ~OutputSession() { close(); }
};

esp_err_t writeFrames(const int16_t* samples, size_t frames) {
  size_t written = 0;
  const size_t bytes = frames * 2 * sizeof(int16_t);
  const auto result = i2s_write(kPort, samples, bytes, &written, pdMS_TO_TICKS(100));
  return result == ESP_OK && written != bytes ? ESP_ERR_TIMEOUT : result;
}

esp_err_t play(OutputSession& session, const char*& stage, const int16_t* pcm = nullptr,
               size_t pcmFrames = 0, AppState* state = nullptr,
               void (*refresh)(const AppState&) = nullptr, bool (*cancel)() = nullptr) {
  const uint32_t rate = pcm ? 24000 : kRate;
  stage = "i2s_install";
  i2s_config_t config = {};
  config.mode = static_cast<i2s_mode_t>(I2S_MODE_MASTER | I2S_MODE_TX);
  config.sample_rate = rate;
  config.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  config.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  config.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  config.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  config.dma_buf_count = 4;
  config.dma_buf_len = kChunkFrames;
  config.tx_desc_auto_clear = true;
  config.mclk_multiple = I2S_MCLK_MULTIPLE_256;
  esp_err_t result = i2s_driver_install(kPort, &config, 0, nullptr);
  if (result != ESP_OK) return result;
  session.installed = true;
  const i2s_pin_config_t pins = {board::kAudioMclk, board::kAudioBclk, board::kAudioWordSelect,
                               board::kAudioDataOut, I2S_PIN_NO_CHANGE};
  stage = "i2s_pins";
  if ((result = i2s_set_pin(kPort, &pins)) != ESP_OK) return result;
  if ((result = i2s_zero_dma_buffer(kPort)) != ESP_OK) return result;

  stage = "codec_probe";
  // beginTouch owns Wire initialization. Never reinitialize or delete that bus here.
  Wire.beginTransmission(board::kSpeakerCodecAddress);
  if (Wire.endTransmission() != 0) return ESP_ERR_NOT_FOUND;
  session.codec = es8311_create(0, board::kSpeakerCodecAddress);
  if (!session.codec) return ESP_ERR_NO_MEM;
  const es8311_clock_config_t clocks = {false, false, true, static_cast<int>(rate * 256), static_cast<int>(rate)};
  stage = "codec_init";
  if ((result = es8311_init(session.codec, &clocks, ES8311_RESOLUTION_16,
                            ES8311_RESOLUTION_16)) != ESP_OK) return result;
  if ((result = es8311_voice_mute(session.codec, true)) != ESP_OK) return result;
  stage = "codec_volume";
  if ((result = es8311_voice_volume_set(session.codec, 85, nullptr)) != ESP_OK) return result;

  int16_t samples[kChunkFrames * 2] = {};
  stage = "silence";
  // Queue silence before enabling the amplifier and allow its output to settle.
  if ((result = writeFrames(samples, kChunkFrames)) != ESP_OK) return result;
  digitalWrite(board::kAmplifierEnable, HIGH);
  for (int block = 0; block < 8; ++block)
    if ((result = writeFrames(samples, kChunkFrames)) != ESP_OK) return result;
  if ((result = es8311_voice_mute(session.codec, false)) != ESP_OK) return result;

  // Scope cleanup covers every error/cancel return. The reply LED begins only
  // when the first PCM buffer is accepted, never during setup or a test tone.
  StatusLedScope ledActivity(VoicePhase::Idle, false, false);
  stage = "tone_write";
  const size_t totalFrames = pcm ? pcmFrames : kToneFrames;
  uint32_t lastRefresh = millis();
  for (size_t offset = 0; offset < totalFrames; offset += kChunkFrames) {
    if (cancel && cancel()) return ESP_ERR_INVALID_STATE;
    for (size_t frame = 0; frame < kChunkFrames; ++frame) {
      const size_t position = offset + frame;
      if (position >= totalFrames) {
        samples[frame * 2] = samples[frame * 2 + 1] = 0;
        continue;
      }
      const size_t remaining = totalFrames - 1 - position;
      const size_t edge = position < remaining ? position : remaining;
      const float envelope = edge < kFadeFrames ? static_cast<float>(edge) / kFadeFrames : 1.0f;
      // Keep initial speech playback quiet; codec volume is separately bounded.
      const auto sample = pcm ? static_cast<int16_t>(pcm[position] * 0.25f * envelope) :
          static_cast<int16_t>(kPeak * envelope * std::sin(6.28318530718f * 440.0f * position / kRate));
      samples[frame * 2] = sample;
      samples[frame * 2 + 1] = sample;
    }
    if ((result = writeFrames(samples, kChunkFrames)) != ESP_OK) return result;
    if (pcm && state && offset == 0) updateStatusLeds(state->voicePhase, false, true);
    if (refresh && state && millis() - lastRefresh >= 100u) {
      refresh(*state);
      lastRefresh = millis();
    }
  }
  // DMA can still contain the final blocks; drain with silence before shutdown.
  for (auto& sample : samples) sample = 0;
  stage = "drain";
  for (int block = 0; block < 8; ++block)
    if ((result = writeFrames(samples, kChunkFrames)) != ESP_OK) return result;
  delay(40);
  return ESP_OK;
}
}  // namespace

void disableSpeaker() {
  clearStatusLeds();
  digitalWrite(board::kAmplifierEnable, LOW);
  pinMode(board::kAmplifierEnable, OUTPUT);
}

void testSpeaker(AppState& state) {
  disableSpeaker();
  OutputSession session;
  state.audioError = play(session, state.audioStage);
  const auto cleanup = session.close();
  if (state.audioError == ESP_OK) {
    state.audioError = cleanup;
    state.audioStage = cleanup == ESP_OK ? "complete" : "cleanup";
  }
  if (state.audioError == ESP_OK) ++state.toneTests;
  Serial.printf("SPEAKER_TEST stage=%s error=%d transfers=%lu amp_command=low\n", state.audioStage,
                state.audioError, static_cast<unsigned long>(state.toneTests));
}

bool playPcm(AppState& state, const int16_t* samples, size_t frames,
             void (*refresh)(const AppState&), bool (*cancel)()) {
  if (!samples || frames == 0 || frames > 480000) return false;
  disableSpeaker();
  OutputSession session;
  state.audioError = play(session, state.audioStage, samples, frames, &state, refresh, cancel);
  const auto cleanup = session.close();
  if (state.audioError == ESP_OK) state.audioError = cleanup;
  state.audioStage = state.audioError == ESP_OK ? "complete" : "cancel_or_error";
  return state.audioError == ESP_OK;
}
}  // namespace mr_robot
