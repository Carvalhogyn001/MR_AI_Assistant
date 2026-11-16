#pragma once

#include <cstdio>
#include <cstddef>

namespace mr_robot {
inline constexpr const char* captureFilename() {
  return "/mr-robot-capture.jpg";
}

inline bool captureFilenameForIndex(unsigned index, char* output, size_t outputLength) {
  const int required = index == 0
      ? std::snprintf(output, outputLength, "%s", captureFilename())
      : std::snprintf(output, outputLength, "/mr-robot-capture-%03u.jpg", index);
  return required > 0 && static_cast<size_t>(required) < outputLength;
}

inline constexpr bool shouldConvertToJpeg(bool frameIsJpeg) {
  return !frameIsJpeg;
}
}
