#include <cassert>
#include <cstring>
#include "lcd_status.h"

int main() {
  assert(std::strcmp(mr_robot::lcdTitle(), "MR. Robot Ready") == 0);
  char line[17] = {};
  mr_robot::formatSdLine(958, line, sizeof(line));
  assert(std::strcmp(line, "SD 958 MB Free") == 0);
  assert(std::strcmp(mr_robot::lcdDiagnosticLine(), "################") == 0);
  return 0;
}
