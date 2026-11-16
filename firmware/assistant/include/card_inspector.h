#pragma once
#include "app_state.h"

namespace mr_robot {
// Raw reads only: no filesystem mount, directory access, writes or format.
void inspectCard(AppState& state);
}
