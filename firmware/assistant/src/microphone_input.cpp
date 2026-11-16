#include "microphone_input.h"
#include "audio_output.h"
#include "board_pins.h"
#include "status_leds.h"
#include <Arduino.h>
#include <Wire.h>
#include <driver/i2s.h>
#include <es7210.h>
#include <cmath>

namespace mr_robot {
namespace {
constexpr i2s_port_t kPort = I2S_NUM_0;
constexpr uint32_t kRate = 16000;
constexpr uint32_t kFrames = kRate * 4;
constexpr size_t kBlock = 256;
constexpr size_t kSlots = 4;
static_assert(kFrames % kBlock == 0, "Capture must end on a complete block");

class CaptureSession {
 public:
  bool installed = false;
  es7210_dev_handle_t codec = nullptr;
  esp_err_t close() {
    disableSpeaker();
    esp_err_t result = ESP_OK;
    if (codec) {
      result = es7210_stop_codec(codec);
      es7210_del_codec(codec);
      codec = nullptr;
    }
    if (installed) {
      const auto stopped = i2s_driver_uninstall(kPort);
      if (result == ESP_OK) result = stopped;
      installed = false;
    }
    return result;
  }
  ~CaptureSession() { close(); }
};

struct Samples {
  int16_t values[kBlock * kSlots] = {};
  ~Samples() {
    // Clear the application buffer explicitly; DMA storage is released by IDF.
    volatile int16_t* bytes = values;
    for (size_t i = 0; i < kBlock * kSlots; ++i) bytes[i] = 0;
  }
};

esp_err_t readBlock(Samples& samples) {
  size_t received = 0;
  const auto result = i2s_read(kPort, samples.values, sizeof(samples.values), &received, pdMS_TO_TICKS(250));
  return result == ESP_OK && received != sizeof(samples.values) ? ESP_ERR_TIMEOUT : result;
}

esp_err_t openCapture(CaptureSession& session, AppState& state) {
  state.micStage = "i2s_install";
  i2s_config_t config = {};
  config.mode = static_cast<i2s_mode_t>(I2S_MODE_MASTER | I2S_MODE_RX);
  config.sample_rate = kRate;
  config.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  config.channel_format = I2S_CHANNEL_FMT_MULTIPLE;
  config.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  config.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  config.dma_buf_count = 8;
  config.dma_buf_len = kBlock;
  config.mclk_multiple = I2S_MCLK_MULTIPLE_256;
  config.chan_mask = static_cast<i2s_channel_t>(I2S_TDM_ACTIVE_CH0 | I2S_TDM_ACTIVE_CH1 |
                                             I2S_TDM_ACTIVE_CH2 | I2S_TDM_ACTIVE_CH3);
  config.total_chan = kSlots;
  esp_err_t result = i2s_driver_install(kPort, &config, 0, nullptr);
  if (result != ESP_OK) return result;
  session.installed = true;
  const i2s_pin_config_t pins = {board::kAudioMclk, board::kAudioBclk, board::kAudioWordSelect,
                               I2S_PIN_NO_CHANGE, board::kAudioDataIn};
  state.micStage = "i2s_pins";
  if ((result = i2s_set_pin(kPort, &pins)) != ESP_OK) return result;
  state.micStage = "codec_probe";
  Wire.beginTransmission(board::kMicrophoneCodecAddress);
  if (Wire.endTransmission() != 0) return ESP_ERR_NOT_FOUND;
  const es7210_i2c_config_t bus = {I2C_NUM_0, board::kMicrophoneCodecAddress};
  if ((result = es7210_new_codec(&bus, &session.codec)) != ESP_OK) return result;
  es7210_codec_config_t codec = {};
  codec.sample_rate_hz = kRate;
  codec.mclk_ratio = 256;
  codec.i2s_format = ES7210_I2S_FMT_I2S;
  codec.bit_width = ES7210_I2S_BITS_16B;
  codec.mic_bias = ES7210_MIC_BIAS_2V87;
  codec.mic_gain = ES7210_MIC_GAIN_24DB;
  codec.flags.tdm_enable = true;
  state.micStage = "codec_init";
  if ((result = es7210_config_codec(session.codec, &codec)) != ESP_OK) return result;
  if ((result = es7210_config_volume(session.codec, 0)) != ESP_OK) return result;

  Samples samples;
  state.micStage = "settling";
  // Discard initialization noise and the DMA data queued during codec setup.
  for (int block = 0; block < 8; ++block)
    if ((result = readBlock(samples)) != ESP_OK) return result;
  state.micStage = "capturing";
  return ESP_OK;
}

CaptureSession stream;

esp_err_t capture(CaptureSession& session, AppState& state, CaptureRefresh refresh,
                  int16_t* output = nullptr, size_t frames = kFrames, bool (*cancel)() = nullptr) {
  esp_err_t result = openCapture(session, state);
  if (result != ESP_OK) return result;
  StatusLedScope ledActivity(state.voicePhase, true, false);
  Samples samples;
  uint64_t squares[kSlots] = {};
  uint32_t lastRefresh = millis();
  for (size_t offset = 0; offset < frames; offset += kBlock) {
    if (cancel && cancel()) return ESP_ERR_INVALID_STATE;
    if ((result = readBlock(samples)) != ESP_OK) return result;
    for (size_t frame = 0; frame < kBlock; ++frame) {
      if (output) output[offset + frame] = samples.values[frame * kSlots];
      for (size_t slot = 0; slot < kSlots; ++slot) {
        const int32_t value = samples.values[frame * kSlots + slot];
        const uint16_t magnitude = value < 0 ? -value : value;
        squares[slot] += static_cast<int64_t>(value) * value;
        if (magnitude > state.micPeak[slot]) state.micPeak[slot] = magnitude;
        if (value == -32768 || value == 32767) ++state.micClips[slot];
      }
    }
    state.micFrames += kBlock;
    for (size_t slot = 0; slot < kSlots; ++slot)
      state.micRms[slot] = static_cast<uint16_t>(std::sqrt(static_cast<double>(squares[slot]) / state.micFrames));
    if (refresh && millis() - lastRefresh >= 100u) {
      refresh(state);
      lastRefresh = millis();
    }
  }
  return ESP_OK;
}
}  // namespace

void testMicrophone(AppState& state, CaptureRefresh refresh) {
  disableSpeaker();
  state.microphoneArmed = false;
  state.microphoneActive = true;
  state.micFrames = 0;
  for (size_t slot = 0; slot < kSlots; ++slot) {
    state.micRms[slot] = state.micPeak[slot] = 0;
    state.micClips[slot] = 0;
  }
  if (refresh) refresh(state);
  CaptureSession session;
  state.micError = capture(session, state, refresh);
  const auto cleanup = session.close();
  if (state.micError == ESP_OK) {
    state.micError = cleanup;
    state.micStage = cleanup == ESP_OK ? "complete" : "cleanup";
  }
  if (state.micError == ESP_OK) ++state.micTests;
  state.microphoneActive = false;
  if (refresh) refresh(state);
  Serial.printf("MIC_TEST stage=%s error=%d frames=%lu tests=%lu capture=off\n", state.micStage,
                state.micError, static_cast<unsigned long>(state.micFrames),
                static_cast<unsigned long>(state.micTests));
}

bool recordMicrophone(AppState& state, int16_t* output, size_t frames,
                      CaptureRefresh refresh, bool (*cancel)()) {
  if (!output || frames == 0 || frames > 128000 || frames % kBlock) return false;
  disableSpeaker();
  state.microphoneArmed = false;
  state.microphoneActive = true;
  state.micFrames = 0;
  for (size_t slot = 0; slot < kSlots; ++slot) {
    state.micRms[slot] = state.micPeak[slot] = 0;
    state.micClips[slot] = 0;
  }
  if (refresh) refresh(state);
  CaptureSession session;
  state.micError = capture(session, state, refresh, output, frames, cancel);
  const auto cleanup = session.close();
  if (state.micError == ESP_OK) state.micError = cleanup;
  state.micStage = state.micError == ESP_OK ? "complete" : "cancel_or_error";
  state.microphoneActive = false;
  if (refresh) refresh(state);
  return state.micError == ESP_OK;
}

bool startMicrophoneStream(AppState& state) {
  if (stream.installed) return false;
  disableSpeaker();
  state.microphoneActive = true;
  state.micFrames = 0;
  state.micError = openCapture(stream, state);
  if (state.micError != ESP_OK) stopMicrophoneStream(state);
  else updateStatusLeds(state.voicePhase, true, false);
  return state.micError == ESP_OK;
}

bool readMicrophoneStream(AppState& state, int16_t (&output)[kStreamFrames]) {
  if (!stream.installed) return false;
  Samples samples;
  for (size_t offset = 0; offset < kStreamFrames; offset += kBlock) {
    state.micError = readBlock(samples);
    if (state.micError != ESP_OK) return false;
    for (size_t frame = 0; frame < kBlock; ++frame)
      output[offset + frame] = samples.values[frame * kSlots];
  }
  state.micFrames += kStreamFrames;
  return true;
}

void stopMicrophoneStream(AppState& state) {
  clearStatusLeds();
  if (!stream.installed && !state.microphoneActive) return;
  const auto cleanup = stream.close();
  if (state.micError == ESP_OK) state.micError = cleanup;
  state.microphoneActive = false;
  state.micStage = state.micError == ESP_OK ? "complete" : "stream_error";
}
}  // namespace mr_robot
