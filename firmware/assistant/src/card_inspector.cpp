#include "card_inspector.h"
#include "board_pins.h"
#include <driver/sdmmc_host.h>
#include <sdmmc_cmd.h>
#include <esp_heap_caps.h>
#include <cstring>

namespace mr_robot {
namespace {
uint32_t littleEndian32(const uint8_t* p) {
  return uint32_t(p[0]) | (uint32_t(p[1]) << 8) | (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24);
}
const char* filesystemSignature(const uint8_t* sector) {
  if (std::memcmp(sector + 3, "EXFAT   ", 8) == 0) return "exfat_signature";
  if (std::memcmp(sector + 82, "FAT32   ", 8) == 0) return "fat32_signature";
  if (std::memcmp(sector + 54, "FAT16   ", 8) == 0) return "fat16_signature";
  return "unknown_signature";
}
}  // namespace

void inspectCard(AppState& state) {
  state.cardInspected = true;
  state.cardRawBytes = 0;
  state.cardFilesystem = "unknown_signature";
  state.cardError = 0;
  sdmmc_host_t host = SDMMC_HOST_DEFAULT();
  host.flags = SDMMC_HOST_FLAG_1BIT;
  host.max_freq_khz = SDMMC_FREQ_PROBING;  // 400 kHz metadata inspection.
  sdmmc_slot_config_t slot = SDMMC_SLOT_CONFIG_DEFAULT();
  slot.width = 1;
  slot.clk = static_cast<gpio_num_t>(board::kSdClock);
  slot.cmd = static_cast<gpio_num_t>(board::kSdCommand);
  slot.d0 = static_cast<gpio_num_t>(board::kSdData0);
  slot.d1 = slot.d2 = slot.d3 = slot.d4 = slot.d5 = slot.d6 = slot.d7 = GPIO_NUM_NC;
  slot.gpio_cd = SDMMC_SLOT_NO_CD;
  slot.gpio_wp = SDMMC_SLOT_NO_WP;
  esp_err_t error = sdmmc_host_init();
  if (error != ESP_OK) { state.cardError = error; return; }
  error = sdmmc_host_init_slot(host.slot, &slot);
  sdmmc_card_t card = {};
  if (error == ESP_OK) error = sdmmc_card_init(&host, &card);
  if (error == ESP_OK) {
    state.cardRawBytes = static_cast<uint64_t>(card.csd.capacity) * card.csd.sector_size;
    if (card.csd.sector_size == 512) {
      auto* sector = static_cast<uint8_t*>(heap_caps_malloc(512, MALLOC_CAP_DMA));
      if (sector == nullptr) error = ESP_ERR_NO_MEM;
      else {
        error = sdmmc_read_sectors(&card, sector, 0, 1);
        if (error == ESP_OK) {
          state.cardFilesystem = filesystemSignature(sector);
          // Read at most the first nonempty MBR partition's boot sector.
          // Do not enumerate files, labels, card serials or personal content.
          if (std::strcmp(state.cardFilesystem, "unknown_signature") == 0 && sector[510] == 0x55 && sector[511] == 0xaa) {
            uint32_t lba = 0;
            for (int i = 0; i < 4; ++i) {
              const uint8_t* entry = sector + 446 + i * 16;
              if (entry[4] != 0 && littleEndian32(entry + 12) > 0) { lba = littleEndian32(entry + 8); break; }
            }
            if (lba > 0 && lba < card.csd.capacity) {
              error = sdmmc_read_sectors(&card, sector, lba, 1);
              if (error == ESP_OK) state.cardFilesystem = filesystemSignature(sector);
            }
          }
        }
        heap_caps_free(sector);
      }
    }
  }
  state.cardError = error;
  sdmmc_host_deinit();
}
}  // namespace mr_robot
