#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"
#include "esp_sleep.h"

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// ================= WIFI =================
const char* ssid     = "Redmi";
const char* password = "tuetai12";

// ================= SERVER ===============
const char* serverUrl = "http://192.168.106.191:5000/upload";

// ================= PIR ==================
#define PIR_PIN 13
#define SEND_INTERVAL 5000   // ms

// ================= CAMERA INIT ==========
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk  = XCLK_GPIO_NUM;
  config.pin_pclk  = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href  = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn  = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size   = FRAMESIZE_QVGA; // tiết kiệm điện + nhanh
  config.jpeg_quality = 12;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Camera init failed");
    ESP.restart();
  }
}

// ================= SEND PHOTO ===========
void sendPhotoToPi() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Capture failed");
    return;
  }

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "image/jpeg");

  Serial.println("📤 Sending photo...");
  int code = http.POST(fb->buf, fb->len);
  Serial.printf("📡 Server response: %d\n", code);

  http.end();
  esp_camera_fb_return(fb);
}

// ================= LIGHT SLEEP ==========
void lightSleepUntilPIR() {
  Serial.println("😴 Light sleep (WiFi kept)");

  esp_sleep_enable_ext0_wakeup((gpio_num_t)PIR_PIN, 1);
  delay(50);
  esp_light_sleep_start();

  Serial.println("⚡ Wakeup by PIR");
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);

  initCamera();

  WiFi.begin(ssid, password);
  Serial.print("📶 Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }
  Serial.println("\n✅ WiFi connected");

  // BẬT MODEM SLEEP → giữ kết nối nhưng tiết kiệm điện
  WiFi.setSleep(true);
}

// ================= LOOP ==================
void loop() {
  if (digitalRead(PIR_PIN) == HIGH) {
    sendPhotoToPi();
    delay(SEND_INTERVAL);
  } else {
    lightSleepUntilPIR();
  }
}
