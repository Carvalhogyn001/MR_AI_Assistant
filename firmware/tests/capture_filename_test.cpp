#include <cassert>
#include <cstring>
#include "capture_filename.h"

int main() {
  const char* path = mr_robot::captureFilename();
  assert(std::strcmp(path, "/mr-robot-capture.jpg") == 0);
  assert(mr_robot::shouldConvertToJpeg(false));
  assert(!mr_robot::shouldConvertToJpeg(true));

  char filename[40] = {};
  assert(mr_robot::captureFilenameForIndex(1, filename, sizeof(filename)));
  assert(std::strcmp(filename, "/mr-robot-capture-001.jpg") == 0);
  return 0;
}
