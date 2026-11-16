#pragma once
#include <cstdint>

// Waveshare 1.75 NON-C only. Evidence: docs/HARDWARE-INVENTORY.md.
namespace mr_robot { namespace board {
constexpr int kDisplayCs = 12;
constexpr int kDisplayClock = 38;
constexpr int kDisplayData0 = 4;
constexpr int kDisplayData1 = 5;
constexpr int kDisplayData2 = 6;
constexpr int kDisplayData3 = 7;
constexpr int kDisplayReset = 39;
constexpr int kWidth = 466;
constexpr int kHeight = 466;
constexpr int kColumnOffset = 6;
constexpr int kRowOffset = 0;
constexpr int kSdClock = 2;
constexpr int kSdCommand = 1;
constexpr int kSdData0 = 3;
constexpr int kI2cSda = 15;
constexpr int kI2cScl = 14;
constexpr int kTouchReset = 40;
constexpr int kTouchInterrupt = 11;
constexpr int kAudioMclk = 42;
constexpr int kAudioBclk = 9;
constexpr int kAudioWordSelect = 45;
constexpr int kAudioDataOut = 8;
constexpr int kAudioDataIn = 10;
constexpr int kAmplifierEnable = 46;  // Active HIGH, NS4150B at 3.3 V.
constexpr uint8_t kSpeakerCodecAddress = 0x18;
constexpr uint8_t kMicrophoneCodecAddress = 0x40;
constexpr int kTalkButton = 16;  // H2 IO16, normally open switch to H2 GND.
// Conditional reservations only, recorded in docs/HARDWARE-INVENTORY.md.
// Standard/non-GPS variant and LED/resistor circuits must be verified before
// MR_ROBOT_ENABLE_VERIFIED_STATUS_LEDS=1. Default firmware never accesses them.
constexpr int kStatusGreenCandidate = 17;
constexpr int kStatusRedCandidate = 18;
}}  // namespace mr_robot::board
