#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define OLED_RESET 4
Adafruit_SSD1306 display(OLED_RESET);


#if (SSD1306_LCDHEIGHT != 32)
#error("Height incorrect, please fix Adafruit_SSD1306.h!");
#endif

char knownHeaders[] = {'t', 'o', 's', 'f', 'r'};
int knownReset[] = {0, 0, 0, 0, 0};
int knownValues[] = { -1, -1, -1, -1, -1};
int varCount = 5;

int varRec = 0;
int useDisplay=1;

int curTrial = knownValues[0];
int orientation = knownValues[1];
int sFreq = knownValues[2];
int tFreq = knownValues[3];
int vReset = knownValues[4];



void setup()   {
  Serial.begin(9600);
  if (useDisplay) {
    // ** Initialize the i2c, by pulling the pin high (you can call the pull up).
    display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
    // initialize with the I2C addr 0x3C (for the 128x32)
    display.display();
    delay(100);
    updateDisp();
  }
}


void loop() {
  bool p = flagReceive();
  if (p == 1) {
    assignVars();
    updateDisp();

    // example 'state'
    if (vReset == 1) {
      resetVars();
    }
  }
  delay(5);
}



// This function listens for things on the serial line
// It's a pile of mess, various globals etc. Will clean up later.

bool flagReceive() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char endMarker = '>';
  char rc;

  int nVal;

  const byte numChars = 32;
  char writeChar[numChars];
  bool newData = 0;
  int selectedVar = 0;



  while (Serial.available() > 0 && newData == 0) {


    rc = Serial.read();


    if (recvInProgress == false) {
      for ( int i = 0; i < varCount; i++) {
        if (rc == knownHeaders[i]) {
          selectedVar = i;
          recvInProgress = true;
          Serial.println(selectedVar);
        }
      }
    }


    else if (recvInProgress == true) {
      if (rc != endMarker) {
        writeChar[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }

      else if (rc == endMarker ) {
        writeChar[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = 1;

        nVal = int(String(writeChar).toInt());
        knownValues[selectedVar] = nVal;
        knownReset[selectedVar] = 1;

      }
    }
  }
  return newData;
}

//janky function that works on globals (was interupt function).
void assignVars() {
  curTrial = knownValues[0];
  orientation = knownValues[1];
  sFreq = knownValues[2];
  tFreq = knownValues[3];
  vReset = knownValues[4];
}

void updateDisp() {
  display.clearDisplay();

  display.setTextSize(1);
  display.setTextColor(WHITE);

  display.setCursor(0, 0);
  display.print("Trial: ");
  display.println(curTrial);


  display.setCursor(0, 10);
  display.print("Orient: ");
  display.println(orientation);


  display.setCursor(0, 20);
  display.print("SFreq:");
  display.println(sFreq);

  display.setCursor(65, 20);
  display.print("TFreq:");
  display.println(tFreq);

  display.display();

}

void resetVars() {
  for ( int i = 0; i < varCount; i++) {
    knownReset[i] = 0;
    knownValues[i] = -1;
    assignVars();
    updateDisp();
  }
}
