#include <WiFiClientSecure.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <DNSServer.h> 
#include <ESP8266WiFi.h>

const char* ssid = "phone1";
const char* password = "11223344";

const char* serverURL = "https://internet-thing-server.onrender.com"; // пример URL
const int httpsPort = 443;
const char* uniqueKey = "device_key_123";

#define TRIG_PIN D1
#define ECHO_PIN D2

unsigned long lastDistanceSendTime = 0;
const unsigned long distanceSendInterval = 1000; // 1 секунда

float lastDistance = -1.0; // для сравнения

void setup() {
  Serial.begin(115200);
  Serial.println("Serial test started");

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi");
  }
}

float measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // таймаут 30 мс
  Serial.print("Duration: ");
  Serial.println(duration);

  if (duration == 0) {
    return -1.0; // ошибка
  }

  float distanceCm = duration / 58.0;
  return distanceCm;
}

void sendDistanceEvent(float distance) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, cannot send data");
    return;
  }

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient https;

  String url = String(serverURL) + "/events/";

  https.begin(client, url);
  https.addHeader("Content-Type", "application/json");

  String json = "{\"unique_key\":\"" + String(uniqueKey) + "\",\"event_type\":\"move\"";


  json += "}";

  int httpResponseCode = https.POST(json);

  if (httpResponseCode > 0) {
    Serial.print("Distance event sent, response code: ");
    Serial.println(httpResponseCode);
    String payload = https.getString();
    Serial.println(payload);
  } else {
    Serial.print("Error sending distance event: ");
    Serial.println(httpResponseCode);
  }

  https.end();
}



void loop() {
  unsigned long currentMillis = millis();

  if (WiFi.status() == WL_CONNECTED && (currentMillis - lastDistanceSendTime >= distanceSendInterval)) {
    float distance = measureDistance();
    if (distance >= 0) {
      if (lastDistance < 0 || abs(distance - lastDistance) > 3.0) {
        Serial.print("Distance changed: ");
        Serial.print(lastDistance);
        Serial.print(" -> ");
        Serial.println(distance);
        sendDistanceEvent(distance);
        lastDistance = distance;
      }
    } else {
      Serial.println("Distance measurement error");
    }
    lastDistanceSendTime = currentMillis;
  }
}
