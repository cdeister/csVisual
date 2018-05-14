
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_ILI9341.h>
#include <Adafruit_STMPE610.h>
#include <Adafruit_GFX.h>

// This is calibration data for the raw touch data to the screen coordinates
#define TS_MINX 150
#define TS_MAXY 130
#define TS_MAXX 3800
#define TS_MINY 4000

// these define screen related pins
#define STMPE_CS PC7
#define TFT_CS PA15
#define TFT_DC PB4

// make a touch screen object and a screen.
Adafruit_STMPE610 ts = Adafruit_STMPE610(STMPE_CS);
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);


const int baudrate = 115200;


bool sHead[] = {0, 0, 0};

// home state stuff
char home_knownHeaders[] = {'l', 'r', 't', 'h', 'z', 'y', 'w'};
int home_knownValues[] = {0, 0, 0, 0, 0, 0, 0};
int home_lastValues[] = {0, 0, 0, 0, 0, 0, 0};
int home_labCount[] = {5, 7, 6, 7, 5, 5, 8};
int home_knownCount = 7;


int rowBuf = 5;
int textScale = 1;
int textHeight = 10 * textScale;
int textWidth = 5 * textScale;

int dashState = 0;

// variables related to button rendering
int bWidth = 50;
int bHeight = 30;
int bBuf = 10;
int bTBuf = 5;
int bRow = 190;

char motor_knownHeaders[] = {'s', 'a', 'v', 'm'};
int motor_knownValues[] = {0, 0, 0, 0};
int motor_lastValues[] = {0, 0, 0, 0};
int motor_labCount[] = {7, 5, 8, 7};
int motor_knownCount = 4;

void createHome() {

  tft.fillScreen(ILI9341_BLACK);
  tft.setRotation(1);

  s0Btn(1);
  s1Btn(0);
  s2Btn(0);

  // a) SSID INFO
  tft.setCursor(0, 0);
  tft.setTextColor(ILI9341_RED);
  tft.setTextSize(textScale);
  tft.print("ssid: Not Connected");

  tft.setCursor(0, (textHeight + rowBuf) * 1);
  tft.print("lux:");


  tft.setCursor(0, (textHeight + rowBuf) * 2);
  tft.print("range:");


  tft.setCursor(0, (textHeight + rowBuf) * 3);
  tft.print("temp:");

  tft.setCursor(0, (textHeight + rowBuf) * 4);
  tft.print("humid:");

  tft.setCursor(0, (textHeight + rowBuf) * 5);
  tft.print("voc:");

  tft.setCursor(0, (textHeight + rowBuf) * 6);
  tft.print("co2:");

  tft.setCursor(0, (textHeight + rowBuf) * 7);
  tft.print("weight:");

}



void createMotor() {
  int motorTextScale=2;
  tft.fillScreen(ILI9341_BLACK);
  tft.setRotation(1);

  s0Btn(0);
  s1Btn(1);
  s2Btn(0);

  // a) SSID INFO
  tft.setCursor(0, 0);
  tft.setTextColor(ILI9341_RED);
  tft.setTextSize(textScale);
  tft.print("ssid: Totes Moat");

  tft.setTextSize(motorTextScale);
  tft.setCursor(0, (textHeight + rowBuf) * 1);
  tft.print("speed:");


  tft.setCursor(0, (textHeight + rowBuf) * 2);
  tft.print("acel:");


  tft.setCursor(0, (textHeight + rowBuf) * 3);
  tft.print("volume:");
  tft.setTextSize(textScale);
}

void createDetect() {

  tft.fillScreen(ILI9341_BLACK);
  tft.setRotation(1);

  s0Btn(0);
  s1Btn(0);
  s2Btn(1);

  // a) SSID INFO
  tft.setCursor(0, 0);
  tft.setTextColor(ILI9341_RED);
  tft.setTextSize(textScale);
  tft.print("ssid: Not Connected");

  tft.setCursor(0, (textHeight + rowBuf) * 1);
  tft.print("Running Detection Task: Relaying Serial Only");

}

// ******** Menu Buttons
void s0Btn(bool selState) {
  int bLoc = ((1 * bBuf) + (0 * bWidth));
  if (selState == 0) {
    tft.fillRect(bLoc, bRow, bWidth, bHeight, ILI9341_RED);
    // col,row || width, height
    tft.setCursor(bLoc + bTBuf, bRow + bTBuf);
    tft.setTextColor(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.print("home");
  }
  else if (selState == 1) {
    tft.fillRect(bLoc, bRow, bWidth, bHeight, ILI9341_GREEN);
    // col,row || width, height
    tft.setCursor(bLoc + bTBuf, bRow + bTBuf);
    tft.setTextColor(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.print("home");
  }
}

void s1Btn(bool selState) {
  int bLoc = ((2 * bBuf) + (1 * bWidth));
  if (selState == 0) {
    tft.fillRect(bLoc, bRow, bWidth, bHeight, ILI9341_RED);
    // col,row || width, height
    tft.setCursor(bLoc + bTBuf, bRow + bTBuf);
    tft.setTextColor(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.print("motor");
  }
  if (selState == 1) {
    tft.fillRect(bLoc, bRow, bWidth, bHeight, ILI9341_GREEN);
    // col,row || width, height
    tft.setCursor(bLoc + bTBuf, bRow + bTBuf);
    tft.setTextColor(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.print("motor");
  }
}

void s2Btn(bool selState) {
  int bLoc = ((3 * bBuf) + (2 * bWidth));
  if (selState == 0) {
    tft.fillRect(bLoc, bRow, bWidth, bHeight, ILI9341_RED);
    // col,row || width, height
    tft.setCursor(bLoc + bTBuf, bRow + bTBuf);
    tft.setTextColor(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.print("detect");
  }
  if (selState == 1) {
    tft.fillRect(bLoc, bRow, bWidth, bHeight, ILI9341_GREEN);
    // col,row || width, height
    tft.setCursor(bLoc + bTBuf, bRow + bTBuf);
    tft.setTextColor(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.print("detect");
  }
}


void setup(void) {
  Serial.begin (baudrate);  // USB monitor
  Serial1.begin(baudrate);  // HW UART1
  Serial2.begin(baudrate);  // HW UART2

  tft.begin();
  if (!ts.begin()) {
    Serial.println("Unable to start touchscreen.");
  }
  else {
    Serial.println("Touchscreen started.");
  }
  dashState = 0;
}


void detectStateBody(){
  if (Serial.available()) {
    Serial1.write(Serial.read());
  }

  if (Serial1.available()) {
    Serial.write(Serial1.read());
  }
}



void loop() {

  // ***** Check for new interaction
  if (!ts.bufferEmpty()) {
    // Retrieve a point
    TS_Point p = ts.getPoint();
    // Scale using the calibration #'s
    // and rotate coordinate system
    p.x = map(p.x, TS_MINY, TS_MAXY, 0, tft.height());
    p.y = map(p.y, TS_MINX, TS_MAXX, 0, tft.width());
    int y = tft.height() - p.x;
    int x = p.y;
    Serial.print("x=");
    Serial.print(y);
    Serial.print(" y=");
    Serial.println(x);

    if ((y > 180) && (y <= 200)) {
      if ((x > 10) && (x <= 60)) {
        dashState = 0;
      }
      else if ((x > 70) && (x <= 120)) {
        dashState = 1;
      }
      else if ((x > 140) && (x <= 190)) {
        dashState = 2;
      }
    }
  }



  // *********** S0: Default Info State
  if (dashState == 0) {
    if (sHead[0] == 0) {
      sHead[0] = 1;
      sHead[1] = 0;
      sHead[2] = 0;
      createHome();
    }

    flagReceive(home_knownHeaders, home_knownValues, home_knownCount);
    for ( int i = 0; i < home_knownCount; i++) {
      if (home_knownValues[i] != home_lastValues[i]) {
        updateHomeDispVal(home_labCount[i], i + 1, i);
      }
      home_lastValues[i] = home_knownValues[i];
    }
  }

  // *********** S1: Motor State
  if (dashState == 1) {
    if (sHead[1] == 0) {
      sHead[0] = 0;
      sHead[1] = 1;
      sHead[2] = 0;
      createMotor();
    }


    flagReceive(motor_knownHeaders, motor_knownValues, motor_knownCount);
    for ( int i = 0; i < motor_knownCount; i++) {
      if (motor_knownValues[i] != motor_lastValues[i]) {
        updateMotorDispVal(motor_labCount[i], i + 1, i);
      }
      motor_lastValues[i] = motor_knownValues[i];
    }
  }

  // *********** S2: Detection State
  if (dashState == 2) {
    if (sHead[2] == 0) {
      sHead[0] = 0;
      sHead[1] = 0;
      sHead[2] = 1;
      createDetect();
    }
    detectStateBody();
  }
}

void updateHomeDispVal(int gap, int row, int valID) {
  tft.setCursor(gap * textWidth, (textHeight + rowBuf) * row);
  tft.setTextColor(ILI9341_BLACK);
  tft.print(home_lastValues[valID]);
  tft.setTextColor(ILI9341_RED);
  tft.setCursor(gap * textWidth, (textHeight + rowBuf) * row);
  tft.print(home_knownValues[valID]);
}

void updateMotorDispVal(int gap, int row, int valID) {
  tft.setCursor(gap * textWidth, (textHeight + rowBuf) * row);
  tft.setTextColor(ILI9341_BLACK);
  tft.print(motor_lastValues[valID]);
  tft.setTextColor(ILI9341_RED);
  tft.setCursor(gap * textWidth, (textHeight + rowBuf) * row);
  tft.print(home_knownValues[valID]);
}


int flagReceive(char varAr[], int valAr[], int knownCount) {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char endMarker = '>';
  char feedbackMarker = '<';
  char rc;
  int nVal;
  const byte numChars = 32;
  char writeChar[numChars];
  static int selectedVar;
  int newData = 0;

  while (Serial1.available() > 0 && newData == 0) {
    rc = Serial1.read();
    if (recvInProgress == false) {
      for ( int i = 0; i < knownCount; i++) {
        if (rc == varAr[i]) {
          selectedVar = i;
          recvInProgress = true;
        }
      }
    }

    else if (recvInProgress == true) {
      if (rc == endMarker ) {
        writeChar[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = 1;

        nVal = int(String(writeChar).toInt());
        valAr[selectedVar] = nVal;

      }
      else if (rc == feedbackMarker) {
        writeChar[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = 1;
        Serial1.print("echo");
        Serial1.print(',');
        Serial1.print(varAr[selectedVar]);
        Serial1.print(',');
        Serial1.print(valAr[selectedVar]);
        Serial1.print(',');
        Serial1.print(selectedVar);
        Serial1.println('~');
      }

      else if (rc != feedbackMarker || rc != endMarker) {
        writeChar[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
    }
  }
  return newData; // tells us if a valid variable arrived.
}
