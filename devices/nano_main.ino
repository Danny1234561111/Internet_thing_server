const byte colPins[3] = {10, 12, 2};  // пины колонок
const byte rowPins[4] = {9, 11, 5, 6};  // пины строк


const byte numCols = 3;
const byte numRows = 4;

bool buttonState[4][3];
bool lastButtonState[4][3];

void setup() {
  Serial.begin(115200);

  for (byte c = 0; c < numCols; c++) {
    pinMode(colPins[c], OUTPUT);
    digitalWrite(colPins[c], HIGH);
  }

  for (byte r = 0; r < numRows; r++) {
    pinMode(rowPins[r], INPUT_PULLUP);
  }

  for (byte r = 0; r < numRows; r++) {
    for (byte c = 0; c < numCols; c++) {
      buttonState[r][c] = false;
      lastButtonState[r][c] = false;
    }
  }
}

void loop() {
  for (byte c = 0; c < numCols; c++) {
    digitalWrite(colPins[c], LOW);
    delayMicroseconds(5);

    for (byte r = 0; r < numRows; r++) {
      bool pressed = (digitalRead(rowPins[r]) == LOW);
      buttonState[r][c] = pressed;

      // При нажатии (переход с false на true) — выводим номер кнопки в Serial
      if (!lastButtonState[r][c] && buttonState[r][c]) {
        int buttonNumber = r * numCols + c + 1;
        Serial.println(buttonNumber);
      }

      // При отпускании (переход с true на false) — отправляем номер или 0 если 11
      if (lastButtonState[r][c] && !buttonState[r][c]) {
        int buttonNumber = r * numCols + c + 1;
        int toSend = (buttonNumber == 11) ? 0 : buttonNumber;
        Serial.print("Send to ESP: ");
        Serial.println(toSend);
      }

      lastButtonState[r][c] = buttonState[r][c];
    }

    digitalWrite(colPins[c], HIGH);
  }
}
