/* Dead simple serial relay. Load onto any arduino type board with a hardware serial line.

*/
#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define OLED_RESET 4
Adafruit_SSD1306 display(OLED_RESET);



void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  // initialize with the I2C addr 0x3C (for the 128x32)
  display.display();
  delay(200);
  //
  display.setTextSize(2);
  display.setTextColor(WHITE);
  display.setCursor(10, 0);
  display.clearDisplay();
  display.println("a");
  display.display();
  delay(1);
}

void loop() {
  if (Serial.available()) {
    Serial1.write(Serial.read());
    display.setTextSize(2);
    display.setTextColor(WHITE);
    display.setCursor(10, 0);
    display.clearDisplay();
    display.println("usb");
    display.display();
    delay(1);
  }
  if (Serial1.available()) {
    Serial.write(Serial1.read());
    display.setTextSize(2);
    display.setTextColor(WHITE);
    display.setCursor(10, 0);
    display.clearDisplay();
    display.println("hw");
    display.display();
    delay(1);
  }
}
