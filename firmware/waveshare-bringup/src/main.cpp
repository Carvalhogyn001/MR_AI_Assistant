#include <Arduino.h>
#include <esp_heap_caps.h>
#include <esp32s3/spiram.h>

namespace {
constexpr uint32_t kExpectedFlashBytes = 16u * 1024u * 1024u;
constexpr uint32_t kExpectedPsramBytes = 8u * 1024u * 1024u;
constexpr size_t kProbeBytes = 64u * 1024u;
bool baselinePassed = false;

// Checks only this allocated buffer; this is not a full RAM stress test.
bool probePsram() {
  auto* allocation = static_cast<uint8_t*>(
      heap_caps_malloc(kProbeBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (allocation == nullptr) {
    Serial.println("PSRAM_BUFFER_CHECK=FAIL reason=allocation");
    return false;
  }
  // Force physical reads/writes instead of allowing constant propagation.
  volatile uint8_t* buffer = allocation;
  for (size_t i = 0; i < kProbeBytes; ++i) {
    buffer[i] = static_cast<uint8_t>(i * 37u + 11u);
  }
  bool passed = true;
  for (size_t i = 0; i < kProbeBytes; ++i) {
    if (buffer[i] != static_cast<uint8_t>(i * 37u + 11u)) {
      passed = false;
      break;
    }
  }
  heap_caps_free(allocation);
  Serial.printf("PSRAM_BUFFER_CHECK=%s bytes=%u\n", passed ? "PASS" : "FAIL",
                static_cast<unsigned>(kProbeBytes));
  return passed;
}

void reportBaseline() {
  const uint32_t flashBytes = ESP.getFlashChipSize();
  // Arduino 2.0.17 getPsramSize() returns usable heap, not chip capacity.
  const uint32_t psramBytes = psramFound() ? esp_spiram_get_size() : 0u;
  Serial.println("MR_ROBOT_WAVESHARE_BASELINE version=2");
  Serial.printf("CHIP=%s sdk_revision=%u cores=%u cpu_mhz=%u\n", ESP.getChipModel(),
                ESP.getChipRevision(), ESP.getChipCores(), ESP.getCpuFreqMHz());
  Serial.printf("FLASH_BYTES=%lu expected=%lu\n", static_cast<unsigned long>(flashBytes),
                static_cast<unsigned long>(kExpectedFlashBytes));
  Serial.printf("PSRAM_PHYSICAL_BYTES=%lu expected=%lu\n", static_cast<unsigned long>(psramBytes),
                static_cast<unsigned long>(kExpectedPsramBytes));
  Serial.printf("PSRAM_HEAP_BYTES=%lu\n", static_cast<unsigned long>(ESP.getPsramSize()));
  const bool memoryPassed = probePsram();
  baselinePassed = flashBytes == kExpectedFlashBytes &&
                   psramBytes == kExpectedPsramBytes && memoryPassed;
  Serial.printf("BASELINE=%s\n", baselinePassed ? "PASS" : "FAIL");
}
}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t started = millis();
  while (!Serial && millis() - started < 2000u) {
    delay(10);
  }
  reportBaseline();
}

void loop() {
  // Reprint when the monitor opens late, without allocating again.
  if (Serial.available() > 0) {
    const char command = static_cast<char>(Serial.read());
    if (command == 'i') {
      reportBaseline();
    }
  }
  static uint32_t lastHeartbeat = 0;
  if (millis() - lastHeartbeat >= 5000u) {
    lastHeartbeat = millis();
    Serial.printf("HEARTBEAT baseline=%s uptime_ms=%lu free_heap=%lu free_psram=%lu\n",
                  baselinePassed ? "PASS" : "FAIL", static_cast<unsigned long>(millis()),
                  static_cast<unsigned long>(ESP.getFreeHeap()),
                  static_cast<unsigned long>(ESP.getFreePsram()));
  }
  delay(10);
}
