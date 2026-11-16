#include <cassert>
#include <cstring>
#include "camera_portal.h"

int main() {
  assert(std::strcmp(mr_robot::cameraPortalSsid(), "MR-Robot") == 0);
  char password[16] = {};
  mr_robot::formatCameraPortalPassword(0x123456ULL, password, sizeof(password));
  assert(std::strcmp(password, "MRRobot123456") == 0);
  assert(std::strcmp(mr_robot::cameraPortalUrl(), "http://192.168.4.1") == 0);
  return 0;
}
