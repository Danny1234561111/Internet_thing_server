// ESP8266 (NodeMCU)
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <DNSServer.h>
const char* apSSID = "ESP8266_Setup";
const char* apPassword = "password";
---
const char* serverURL = "https://internet-thing-server.onrender.com/devices/change_pin";
const char* token = "YOUR_AUTH_TOKEN";
const char* uniqueKey = "YOUR_DEVICE_UNIQUE_KEY";

const int greenLedPin = D4;
const int redLedPin = D7;

const int serialBaudRate = 115200;

const int passwordLength = 4;
char passwordBuffer[passwordLength + 1]; // +1 for null terminator '\0'
int passwordIndex = 0;

String savedSSID = "";
String savedPassword = "";

ESP8266WebServer server(80);
DNSServer dnsServer;

void setup() {
  Serial.begin(115200);
  Serial.println("Serial test started");
  Serial.begin(serialBaudRate);
  delay(10);
  Serial.println();

  pinMode(greenLedPin, OUTPUT);
  pinMode(redLedPin, OUTPUT);

  setupAccessPoint();
  delay(1000);

  loadWiFiCredentials();
  connectToSavedWiFi();

  // Запускаем веб-сервер и настраиваем обработчики
  server.on("/", handleRoot);
  server.on("/connect", HTTP_POST, handleConnect);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  // Обработка входящих байт с Serial (для ввода пароля)
  while (Serial.available() > 0) {
    int incomingByte = Serial.read();
    if (incomingByte >= '0' && incomingByte <= '9') {
      if (passwordIndex < passwordLength) {
        passwordBuffer[passwordIndex] = (char)incomingByte;
        passwordIndex++;
        Serial.print("*");
      }
    } else if (incomingByte == 10) { // LF (Enter)
      Serial.println("\nResetting password entry.");
      resetPassword();
    }
  }

  if (passwordIndex == passwordLength) {
    passwordBuffer[passwordLength] = '\0';
    Serial.println("\nSending password for verification...");
    checkPassword(passwordBuffer);
    resetPassword();
  }

  server.handleClient();
  dnsServer.processNextRequest();
}
void setupAccessPoint() {
  Serial.print("Setting up Access Point...");
  WiFi.mode(WIFI_AP);
  WiFi.softAP(apSSID, apPassword);
  Serial.println("OK");

  dnsServer.start(53, "*", WiFi.softAPIP()); // Перенаправляем все DNS-запросы на IP точки доступа
}

void connectToSavedWiFi() {
  if (savedSSID.length() > 0 && savedPassword.length() > 0) {
    Serial.print("Connecting to saved WiFi: ");
    Serial.println(savedSSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(savedSSID.c_str(), savedPassword.c_str());

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(500);
      Serial.print(".");
      attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\nWiFi connected!");
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
    } else {
      Serial.println("\nFailed to connect. Staying in AP mode.");
      WiFi.mode(WIFI_AP);
      dnsServer.start(53, "*", WiFi.softAPIP());
    }
  } else {
    Serial.println("No saved WiFi credentials. Staying in AP mode.");
  }
}


void resetPassword() {
  memset(passwordBuffer, 0, sizeof(passwordBuffer));
  passwordIndex = 0;
}


void checkPassword(const char* enteredPin) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, cannot check password.");
    digitalWrite(redLedPin, HIGH);
    digitalWrite(greenLedPin, LOW);
    delay(2000);
    digitalWrite(redLedPin, LOW);
    return;
  }

  WiFiClientSecure client;
  client.setInsecure();  // Отключаем проверку сертификата (используйте с осторожностью)

  HTTPClient https;

  String url = String(serverURL) + "/check_password/"; // Укажите нужный путь, если есть

  https.begin(client, url);
  https.addHeader("Authorization", "Bearer " + String(token));
  https.addHeader("Content-Type", "application/json");

  // Формируем JSON с нужными данными
  String json = "{\"unique_key\":\"" + String(uniqueKey) + "\","
                "\"old_pin\":\"" + String(enteredPin) + "\","
                "\"new_pin\":\"" + String(enteredPin) + "\"}";

  int httpResponseCode = https.POST(json);

  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    String payload = https.getString();
    Serial.println(payload);

    if (payload.indexOf("\"status\": \"success\"") != -1) {
      Serial.println("Password correct!");
      digitalWrite(greenLedPin, HIGH);
      digitalWrite(redLedPin, LOW);
    } else {
      Serial.println("Password incorrect!");
      digitalWrite(redLedPin, HIGH);
      digitalWrite(greenLedPin, LOW);
    }
  } else {
    Serial.print("Error sending data: ");
    Serial.println(httpResponseCode);
    digitalWrite(redLedPin, HIGH);
    digitalWrite(greenLedPin, LOW);
  }

  https.end();

  delay(2000);
  digitalWrite(greenLedPin, LOW);
  digitalWrite(redLedPin, LOW);
}

void handleRoot() {
  String html = R"rawliteral(
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Настройка Wi-Fi</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f0f0f0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .container {
      background: white;
      padding: 30px 40px;
      border-radius: 8px;
      box-shadow: 0 0 15px rgba(0,0,0,0.2);
      max-width: 400px;
      width: 100%;
    }
    h1 {
      text-align: center;
      color: #333;
    }
    label {
      display: block;
      margin-top: 15px;
      color: #555;
      font-weight: bold;
    }
    input[type="text"], input[type="password"] {
      width: 100%;
      padding: 10px;
      margin-top: 5px;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-sizing: border-box;
      font-size: 16px;
    }
    input[type="submit"] {
      margin-top: 25px;
      width: 100%;
      padding: 12px;
      background-color: #28a745;
      border: none;
      color: white;
      font-size: 18px;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }
    input[type="submit"]:hover {
      background-color: #218838;
    }
    .footer {
      margin-top: 20px;
      font-size: 12px;
      color: #aaa;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Настройка Wi-Fi</h1>
    <form method="POST" action="/connect">
            <label for="ssid">SSID:</label>
      <input type="text" id="ssid" name="ssid" required maxlength="32" />
      <label for="password">Пароль:</label>
      <input type="password" id="password" name="password" maxlength="64" />
      <input type="submit" value="Подключиться" />
    </form>
    <div class="footer">Подключитесь к Wi-Fi сети ESP8266_Setup и откройте эту страницу</div>
  </div>
</body>
</html>
)rawliteral";

  server.send(200, "text/html", html);
}

void handleConnect() {
  if (server.hasArg("ssid") && server.hasArg("password")) {
    String ssid = server.arg("ssid");
    String password = server.arg("password");

    Serial.print("Received SSID: ");
    Serial.println(ssid);
    Serial.print("Received Password: ");
    Serial.println(password);

    // Сохраняем в переменные (здесь можно добавить сохранение в EEPROM/SPIFFS)
    savedSSID = ssid;
    savedPassword = password;

    String response = "<html><body><h1>Попытка подключения к Wi-Fi...</h1>";
    response += "<p>SSID: " + ssid + "</p>";
    response += "<p>Если подключение успешно, устройство перезагрузится.</p>";
    response += "</body></html>";

    server.send(200, "text/html", response);

    // Пытаемся подключиться к Wi-Fi с новыми данными
    WiFi.mode(WIFI_STA);
    WiFi.begin(savedSSID.c_str(), savedPassword.c_str());

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(500);
      Serial.print(".");
      attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\nWiFi connected!");
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
      delay(2000);
      ESP.restart();
    } else {
      Serial.println("\nFailed to connect.");
      WiFi.mode(WIFI_AP);
      WiFi.softAP(apSSID, apPassword);
      dnsServer.start(53, "*", WiFi.softAPIP());
    }
  } else {
    server.send(400, "text/plain", "Bad Request: SSID and Password required");
  }
}

void handleNotFound() {
  server.sendHeader("Location", "/");
  server.send(302, "text/plain", "");
}

