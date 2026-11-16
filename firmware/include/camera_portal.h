#pragma once

#include <cstddef>
#include <cstdio>

namespace mr_robot {
inline constexpr const char* cameraPortalSsid() {
  return "MR-Robot";
}

inline void formatCameraPortalPassword(unsigned long long deviceId, char* output, size_t outputLength) {
  std::snprintf(output, outputLength, "MRRobot%06llX", deviceId & 0xFFFFFFULL);
}

inline constexpr const char* cameraPortalUrl() {
  return "http://192.168.4.1";
}
}
