#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// ==== WiFi ====
const char* ssid     = "Redmi"; 
const char* password = "tuetai12";

// ==== MQTT ====
const char* mqtt_server = "192.168.249.191";   // IP của Pi4 trong cùng mạng
const char* topic       = "fall_detection/status";

// ==== LED + BUZZER ====
#define LED_R   D5
#define LED_G   D6
#define LED_B   D7
#define BUZZER  D2    // buzzer

WiFiClient espClient;
PubSubClient client(espClient);

bool alertMode = false;  // trạng thái cảnh báo

// ====== Hàm bật màu LED ======
void ledColor(bool r, bool g, bool b) {
  digitalWrite(LED_R, r ? HIGH : LOW);
  digitalWrite(LED_G, g ? HIGH : LOW);
  digitalWrite(LED_B, b ? HIGH : LOW);
}

// ====== MQTT callback ======
void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.print("MQTT received: ");
  Serial.println(msg);

  if (msg == "1") {
    alertMode = true;           // bật chế độ cảnh báo
    tone(BUZZER, 3000);         // còi kêu
  } else if (msg == "0") {
    alertMode = false;          // tắt cảnh báo
    noTone(BUZZER);
    ledColor(false, true, false);   // LED xanh báo an toàn
  }
}

// ====== MQTT reconnect ======
void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting MQTT...");
    if (client.connect("AlertNode8266")) {
      client.subscribe(topic);
      Serial.println("MQTT connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// ====== SETUP ======
void setup() {
  Serial.begin(115200);

  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  // WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi connected!");
  Serial.print("ESP8266 IP: ");
  Serial.println(WiFi.localIP());

  // MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  // LED mặc định xanh
  ledColor(false, true, false);
}

// ====== LOOP ======
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // ==== Chế độ cảnh báo: LED nháy đỏ ====
  if (alertMode) {
    ledColor(true, false, false);   // bật đỏ
    delay(200); 
    ledColor(false, false, false);  // tắt
    delay(200);
  }
}
