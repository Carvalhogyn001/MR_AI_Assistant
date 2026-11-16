#include <Arduino.h>
#include <WiFi.h>
#include <esp_camera.h>
#include <esp_http_server.h>
#include <img_converters.h>
#include "camera_portal.h"

namespace {
constexpr int kCameraPinD0 = 4;
constexpr int kCameraPinD1 = 5;
constexpr int kCameraPinD2 = 18;
constexpr int kCameraPinD3 = 19;
constexpr int kCameraPinD4 = 36;
constexpr int kCameraPinD5 = 39;
constexpr int kCameraPinD6 = 34;
constexpr int kCameraPinD7 = 35;
constexpr int kCameraPinXclk = 21;
constexpr int kCameraPinPclk = 22;
constexpr int kCameraPinVsync = 25;
constexpr int kCameraPinHref = 23;
constexpr int kCameraPinSiod = 26;
constexpr int kCameraPinSioc = 27;

constexpr char kStreamBoundary[] = "mrrobotframe";
constexpr char kStreamContentType[] = "multipart/x-mixed-replace;boundary=mrrobotframe";

bool initializeCamera() {
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = kCameraPinD0;
  config.pin_d1 = kCameraPinD1;
  config.pin_d2 = kCameraPinD2;
  config.pin_d3 = kCameraPinD3;
  config.pin_d4 = kCameraPinD4;
  config.pin_d5 = kCameraPinD5;
  config.pin_d6 = kCameraPinD6;
  config.pin_d7 = kCameraPinD7;
  config.pin_xclk = kCameraPinXclk;
  config.pin_pclk = kCameraPinPclk;
  config.pin_vsync = kCameraPinVsync;
  config.pin_href = kCameraPinHref;
  config.pin_sccb_sda = kCameraPinSiod;
  config.pin_sccb_scl = kCameraPinSioc;
  config.pin_pwdn = -1;
  config.pin_reset = -1;
  config.xclk_freq_hz = 10000000;
  config.frame_size = FRAMESIZE_QVGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t result = esp_camera_init(&config);
  if (result == ESP_ERR_NOT_SUPPORTED) {
    Serial.println("Camera has no native JPEG mode. Using RGB565 conversion.");
    config.pixel_format = PIXFORMAT_RGB565;
    result = esp_camera_init(&config);
  }
  if (result != ESP_OK) {
    Serial.printf("Camera initialization failed: 0x%x\n", result);
    return false;
  }

  const sensor_t* sensor = esp_camera_sensor_get();
  Serial.printf("Camera ready. Sensor PID: 0x%04x\n", sensor->id.PID);
  return true;
}

bool acquireJpeg(camera_fb_t** frame, uint8_t** jpeg, size_t* jpegLength) {
  *frame = esp_camera_fb_get();
  if (*frame == nullptr) {
    return false;
  }
  if ((*frame)->format == PIXFORMAT_JPEG) {
    *jpeg = (*frame)->buf;
    *jpegLength = (*frame)->len;
    return true;
  }

  if (!frame2jpg(*frame, 80, jpeg, jpegLength)) {
    esp_camera_fb_return(*frame);
    *frame = nullptr;
    return false;
  }
  esp_camera_fb_return(*frame);
  *frame = nullptr;
  return true;
}

void releaseJpeg(camera_fb_t* frame, uint8_t* jpeg) {
  if (frame != nullptr) {
    esp_camera_fb_return(frame);
  } else {
    free(jpeg);
  }
}

esp_err_t indexHandler(httpd_req_t* request) {
  Serial.println("HTTP_ROOT_REQUEST");
  static const char page[] =
      "<!doctype html><html><head><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
      "<title>MR. Robot Camera</title></head><body><h1>MR. Robot Camera</h1>"
      "<img src=\"/stream\" style=\"width:100%;max-width:640px\" alt=\"Live camera stream\">"
      "<p><a href=\"/capture.jpg\">Capture a still image</a></p></body></html>";
  httpd_resp_set_type(request, "text/html");
  return httpd_resp_send(request, page, HTTPD_RESP_USE_STRLEN);
}

esp_err_t captureHandler(httpd_req_t* request) {
  Serial.println("HTTP_CAPTURE_REQUEST");
  camera_fb_t* frame = nullptr;
  uint8_t* jpeg = nullptr;
  size_t jpegLength = 0;
  if (!acquireJpeg(&frame, &jpeg, &jpegLength)) {
    return httpd_resp_send_500(request);
  }
  httpd_resp_set_type(request, "image/jpeg");
  const esp_err_t result = httpd_resp_send(request, reinterpret_cast<const char*>(jpeg), jpegLength);
  releaseJpeg(frame, jpeg);
  return result;
}

esp_err_t streamHandler(httpd_req_t* request) {
  Serial.println("HTTP_STREAM_REQUEST");
  httpd_resp_set_type(request, kStreamContentType);
  while (true) {
    camera_fb_t* frame = nullptr;
    uint8_t* jpeg = nullptr;
    size_t jpegLength = 0;
    if (!acquireJpeg(&frame, &jpeg, &jpegLength)) {
      return ESP_FAIL;
    }
    char header[96] = {};
    const int headerLength = snprintf(header, sizeof(header), "\r\n--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", kStreamBoundary, static_cast<unsigned>(jpegLength));
    esp_err_t result = httpd_resp_send_chunk(request, header, headerLength);
    if (result == ESP_OK) {
      result = httpd_resp_send_chunk(request, reinterpret_cast<const char*>(jpeg), jpegLength);
    }
    releaseJpeg(frame, jpeg);
    if (result != ESP_OK) {
      return result;
    }
  }
}

bool startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.max_uri_handlers = 3;
  httpd_handle_t server = nullptr;
  if (httpd_start(&server, &config) != ESP_OK) {
    return false;
  }
  const httpd_uri_t indexUri = { .uri = "/", .method = HTTP_GET, .handler = indexHandler, .user_ctx = nullptr };
  const httpd_uri_t captureUri = { .uri = "/capture.jpg", .method = HTTP_GET, .handler = captureHandler, .user_ctx = nullptr };
  const httpd_uri_t streamUri = { .uri = "/stream", .method = HTTP_GET, .handler = streamHandler, .user_ctx = nullptr };
  return httpd_register_uri_handler(server, &indexUri) == ESP_OK &&
         httpd_register_uri_handler(server, &captureUri) == ESP_OK &&
         httpd_register_uri_handler(server, &streamUri) == ESP_OK;
}
}

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("MR. Robot: local camera portal");
  if (!initializeCamera()) {
    return;
  }
  WiFi.mode(WIFI_AP);
  char accessPointPassword[16] = {};
  mr_robot::formatCameraPortalPassword(ESP.getEfuseMac(), accessPointPassword, sizeof(accessPointPassword));
  if (!WiFi.softAP(mr_robot::cameraPortalSsid(), accessPointPassword)) {
    Serial.println("Camera access point failed to start.");
    return;
  }
  if (!startCameraServer()) {
    Serial.println("Camera web server failed to start.");
    return;
  }
  Serial.printf("CAMERA_AP_READY ssid=%s password=%s url=%s\n", mr_robot::cameraPortalSsid(), accessPointPassword, mr_robot::cameraPortalUrl());
}

void loop() { delay(1000); }
