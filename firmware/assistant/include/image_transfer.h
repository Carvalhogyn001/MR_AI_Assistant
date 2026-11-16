#pragma once
#include "control_protocol.h"

namespace mr_robot {
bool imageOperation(Operation operation);
ParseError receiveImage(const Command& command, AppState& state, uint32_t now);
void expireImageTransfer(uint32_t now);
}
