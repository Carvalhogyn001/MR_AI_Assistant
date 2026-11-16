#include <cassert>
#include "display_probe.h"

int main() {
  assert(mr_robot::isValidI2cAddress(0x27));
  assert(mr_robot::isValidI2cAddress(0x3f));
  assert(!mr_robot::isValidI2cAddress(0x00));
  assert(!mr_robot::isValidI2cAddress(0x80));
  return 0;
}
