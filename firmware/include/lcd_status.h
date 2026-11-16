#pragma once

#include <cstdio>
#include <cstddef>

namespace mr_robot {
inline constexpr const char* lcdTitle() {
  return "MR. Robot Ready";
}

inline constexpr const char* lcdDiagnosticLine() {
  return "################";
}

inline void formatSdLine(unsigned long long freeMegabytes, char* output, size_t outputLength) {
  std::snprintf(output, outputLength, "SD %llu MB Free", freeMegabytes);
}
}
