#include <Q2HX711.h>

const byte hx711_data_pin = A6;
const byte hx711_clock_pin = A0;
const int dacOut=A14;

float loadVal = 0;

int writeValA = 0;

Q2HX711 hx711(hx711_data_pin, hx711_clock_pin);

void setup() {
  Serial.begin(9600);
}

void loop() {
  loadVal=(hx711.read()*0.0001);
  writeValA = map(loadVal, 800, 10000, 0, 4095);
  analogWrite(dacOut, writeValA);
  delay(50);
}
