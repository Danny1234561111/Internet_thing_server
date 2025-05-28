#include <Wire.h>
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ESP8266WebServer.h>

#define LIGHT_PIN 2
#define WEIGHTLESS_COEF 0.2 // Коэффициент невесомости
#define ADXL345 0x53

float X_out, Y_out, Z_out;
float X1, Y1, Z1;
float prevX1 = 0, prevY1 = 0, prevZ1 = 0; // Переменные для хранения предыдущих значений
bool light_on = false;

ESP8266WebServer server(80);

// Данные для Wi-Fi
const char* host = "internet-thing-server-1-wtlb.onrender.com"; // Убедитесь, что этот адрес правильный
const int httpsPort = 443; // Порт для HTTPS
const char* device_key = "device_key_123"; // Уникальный ключ устройства
const char* base_url = "/events/";

WiFiClientSecure client;

void setup() {
  Serial.begin(115200);
  pinMode(LIGHT_PIN, OUTPUT);
  digitalWrite(LIGHT_PIN, LOW);

  Wire.begin(4, 5); // SDA на D2 (4), SCL на D1 (5)

  // Инициализация акселерометра
  Wire.beginTransmission(ADXL345);
  Wire.write(0x2D);
  Wire.write(8);
  Wire.endTransmission();

  // Запускаем точку доступа для настройки Wi-Fi
  WiFi.softAP("ESP_AP", "password");
  server.on("/", handleRoot);
  server.on("/connect", handleConnect);
  server.begin();
  Serial.println("HTTP server started");

  client.setInsecure(); // Отключаем проверку сертификата SSL
}

void loop() {
  server.handleClient(); // Обработка входящих запросов

  if (WiFi.status() == WL_CONNECTED) {
    Wire.beginTransmission(ADXL345);
    Wire.write(0x32);
    Wire.endTransmission();
    Wire.requestFrom((uint8_t)ADXL345, (size_t)6, true);

    X_out = (Wire.read() | Wire.read() << 8);
    X1 = X_out / 256.0;
    Y_out = (Wire.read() | Wire.read() << 8);
    Y1 = Y_out / 256.0;
    Z_out = (Wire.read() | Wire.read() << 8);
    Z1 = Z_out / 256.0;

    float acceleration = abs(X1) + abs(Y1);

    // Проверка на значительное изменение
    if (acceleration > WEIGHTLESS_COEF && 
        (abs(X1 - prevX1) > 0.1 || abs(Y1 - prevY1) > 0.1 || abs(Z1 - prevZ1) > 0.1)) {
      sendEvent("accel");
      // Обновляем предыдущие значения
      prevX1 = X1;
      prevY1 = Y1;
      prevZ1 = Z1;
      delay(1000); // чтобы не спамить запросы
    }
  }

  delay(100);
}

void sendEvent(const char* event_type) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, cannot send event");
    return;
  }

  Serial.print("Connecting to server: ");
  Serial.println(host);

  if (!client.connect(host, httpsPort)) {
    Serial.println("Connection to server failed");
    return;
  }

  String json = String("{\"unique_key\":\"") + device_key + "\",\"event_type\":\"" + event_type + "\"}";

  String request = String("POST ") + base_url + " HTTP/1.1\r\n" +
                   "Host: " + host + "\r\n" +
                   "Content-Type: application/json\r\n" +
                   "Content-Length: " + json.length() + "\r\n" +
                   "Connection: close\r\n\r\n" +
                   json;

  client.print(request);

  Serial.println("Request sent:");
  Serial.println(request);

  // Чтение ответа сервера
  while (client.connected()) {
    String line = client.readStringUntil('\n');
    if (line == "\r") {
      break; // headers ended
    }
  }

  String response = client.readString();
  Serial.println("Response:");
  Serial.println(response);

  client.stop();
}

void handleRoot() {
  server.send(200, "text/html", "<form action=\"/connect\" method=\"POST\">"
                                "SSID: <input type=\"text\" name=\"ssid\"><br>"
                                "Password: <input type=\"password\" name=\"password\"><br>"
                                "<input type=\"submit\" value=\"Connect\">"
                                "</form>");
}

void handleConnect() {
  if (server.hasArg("ssid") && server.hasArg("password")) {
    String new_ssid = server.arg("ssid");
    String new_password = server.arg("password");

    server.send(200, "text/html", "Connecting to Wi-Fi...");

    Serial.print("Connecting to new Wi-Fi: ");
    Serial.println(new_ssid);

    WiFi.mode(WIFI_STA); // Переключаемся в режим станции
    WiFi.begin(new_ssid.c_str(), new_password.c_str());

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
      delay(500);
      Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\nConnected to Wi-Fi!");
      Serial.print("IP address: ");
      Serial.println(WiFi.localIP());

      // Отключаем точку доступа, чтобы не мешала
      WiFi.softAPdisconnect(true);
    } else {
      Serial.println("\nFailed to connect to Wi-Fi.");
    }
  } else {
    server.send(400, "text/html", "Bad Request");
  }
}
