#pragma once
// Host-only vector recorder for the actual renderer. Text uses the pinned
// library's real 5x7 glyphs. This does not simulate SPI, timing or panel hardware.
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <string>
#include <vector>
#include <font/glcdfont.h>

namespace preview {
extern std::ostringstream shapes;
extern std::vector<std::string> labels;
inline std::string color(uint16_t rgb) {
  char hex[8];
  std::snprintf(hex, sizeof(hex), "#%02x%02x%02x", ((rgb >> 11) & 31) * 255 / 31,
                ((rgb >> 5) & 63) * 255 / 63, (rgb & 31) * 255 / 31);
  return hex;
}
}
class Arduino_ESP32QSPI { public: Arduino_ESP32QSPI(int,int,int,int,int,int) {} };
class Arduino_CO5300 {
 public:
  Arduino_CO5300(Arduino_ESP32QSPI*,int,int,bool,int,int,int,int,int,int) {}
  int width() const { return 466; }
  int height() const { return 466; }
  void setBrightness(uint8_t) {}
};
class Arduino_Canvas {
 public:
  Arduino_Canvas(int,int,Arduino_CO5300*) {}
  virtual ~Arduino_Canvas() { std::free(_framebuffer); }
  virtual bool begin(int32_t) { return true; }
  void setTextWrap(bool) {}
  void setTextSize(uint8_t size) { size_ = size; }
  void setTextColor(uint16_t value) { color_ = value; }
  void setCursor(int x,int y) { x_ = x; y_ = y; }
  void flush() {}
  void draw16bitRGBBitmap(int x,int y,const uint16_t* pixels,int w,int h) { fillRect(x,y,w,h,*pixels); }
  void fillScreen(uint16_t color) {
    preview::shapes.str(""); preview::shapes.clear(); preview::labels.clear();
    preview::shapes << "<circle cx='233' cy='233' r='232' fill='" << preview::color(color) << "'/>";
  }
  void fillRect(int x,int y,int w,int h,uint16_t color) { rect(x,y,w,h,0,color,true); }
  void fillRoundRect(int x,int y,int w,int h,int r,uint16_t color) { rect(x,y,w,h,r,color,true); }
  void drawRoundRect(int x,int y,int w,int h,int r,uint16_t color) { rect(x,y,w,h,r,color,false); }
  void fillCircle(int x,int y,int r,uint16_t color) {
    preview::shapes << "<circle cx='" << x << "' cy='" << y << "' r='" << r << "' fill='" << preview::color(color) << "'/>";
  }
  void drawLine(int x1,int y1,int x2,int y2,uint16_t color) {
    preview::shapes << "<path d='M" << x1 << ',' << y1 << " L" << x2 << ',' << y2 << "' stroke='" << preview::color(color) << "'/>";
  }
  void print(const char* value) {
    preview::labels.emplace_back(value);
    const int width = static_cast<int>(std::string(value).size()) * 6 * size_;
    // The entire text cell remains within a 222 px radius (11 px inset).
    for (const int x : {x_, x_ + width - 1}) for (const int y : {y_, y_ + 8 * size_ - 1}) {
      if ((x-233)*(x-233)+(y-233)*(y-233)>222*222) {
        std::fprintf(stderr,"Unsafe circular text: %s at %d,%d\n", value,x,y);
        std::abort();
      }
    }
    for (const unsigned char c : std::string(value)) {
      for (int column=0;column<5;++column) for (int row=0;row<8;++row)
        if (font[c*5+column] & (1<<row)) fillRect(x_+column*size_,y_+row*size_,size_,size_,color_);
      x_ += 6*size_;
    }
  }
 protected:
  uint16_t* _framebuffer = nullptr;
 private:
  int x_ = 0, y_ = 0; uint8_t size_ = 1; uint16_t color_ = 0;
  void rect(int x,int y,int w,int h,int radius,uint16_t color,bool fill) {
    assert(w>0 && h>0);
    preview::shapes << "<rect x='" << x << "' y='" << y << "' width='" << w << "' height='" << h << "' rx='" << radius << "' "
      << (fill ? "fill='" : "fill='none' stroke='") << preview::color(color) << "'/>";
  }
};
