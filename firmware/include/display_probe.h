#pragma once

namespace mr_robot {
inline constexpr bool isValidI2cAddress(unsigned address) {
  return address >= 0x03 && address <= 0x77;
}
}
