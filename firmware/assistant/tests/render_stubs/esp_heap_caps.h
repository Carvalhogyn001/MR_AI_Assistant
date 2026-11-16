#pragma once
#include <cstdlib>
constexpr int MALLOC_CAP_SPIRAM = 1, MALLOC_CAP_8BIT = 2;
inline void* heap_caps_aligned_alloc(size_t alignment, size_t bytes, int) {
  void* memory = nullptr;
  return posix_memalign(&memory, alignment, bytes) == 0 ? memory : nullptr;
}
inline void* heap_caps_malloc(size_t bytes, int) { return std::malloc(bytes); }
inline void heap_caps_free(void* memory) { std::free(memory); }
