#include <FlexiTimer2.h>
#include <Wire.h>

#include "Adafruit_VL6180X.h"
#include "Adafruit_Si7021.h"
#include "Adafruit_SGP30.h"


#define dashSerial Serial1


// ****** Make Sensor Objects
Adafruit_Si7021 tempSensor = Adafruit_Si7021();
Adafruit_SGP30 gasSensor;
Adafruit_VL6180X lidar = Adafruit_VL6180X();

// ****** PINS
const int forceSensorPin = 20;
const int lickPin = 21;
const int scopePin = 24;
const int motionPin = 23;
const int rewardPinA = 35;
const int syncPin = 25;

// ****** Interupt Timing
int sampsPerSecond = 1000;
float evalEverySample = 1.0; // number of times to poll the vStates funtion

// ****** Time & State Flow
uint32_t loopCount = 0;
uint32_t sensorPoll = 0;
uint32_t timeOffs;
uint32_t stateTimeOffs;
uint32_t trialTime;
uint32_t stateTime;
uint32_t trigTime = 10;
uint32_t weightOffset = 0;
float weightScale = 0;



int rewardDelivTypeA = 0; // 0 is solenoid; 1 is syringe pump
int rewardDelivTypeB = 0;

bool blockStateChange = 0;
bool rewarding = 0;

// knownLabels[]={'tState','rewardTime','timeOut','contrast','orientation',
// 'sFreq','tFreq','visVariableUpdateBlock','loadCell','motion','lickSensor'};

char knownHeaders[] = {'a', 'r', 't', 'c', 'o', 's', 'f', 'v', 'w', 'm', 'l'};
int knownValues[] = {0, 500, 4000, 0, 0, 0, 0, 1, 0, 0, 0};
int knownCount = 11;

// ************ data
bool scopeState = 1;

int headerStates[] = {0, 0, 0, 0, 0, 0, 0};
int stateCount = 7;
int lastState = 0;


bool trigStuff = 0;

void setup() {

  pinMode(syncPin, OUTPUT);
  digitalWrite(syncPin, LOW);
  pinMode(scopePin, INPUT);
  pinMode(rewardPinA, OUTPUT);
  digitalWrite(rewardPinA, LOW);

  dashSerial.begin(115200);
  Serial.begin(115200);

  Serial.println("Adafruit VL6180x test!");
  if (! lidar.begin()) {
    Serial.println("Failed to find sensor");
    while (1);
  }

  Serial.println("Sensor found!");

  if (! gasSensor.begin()) {
    Serial.println("Sensor not found :(");
    while (1);
  }
  Serial.print("Found SGP30 serial #");
  Serial.print(gasSensor.serialnumber[0], HEX);
  Serial.print(gasSensor.serialnumber[1], HEX);
  Serial.println(gasSensor.serialnumber[2], HEX);



  delay(10000);
  FlexiTimer2::set(1, evalEverySample / sampsPerSecond, vStates);
  FlexiTimer2::start();
}

void loop() {
}

void vStates() {

  // sometimes we block state changes, so let's log the last state.
  lastState = knownValues[0];

  // we then look for any changes to variables, or calls for updates
  flagReceive(knownHeaders, knownValues);

  // Some hardware actions need to complete before a state-change.
  // So, we have a latch for state change. We write over any change with lastState
  if (blockStateChange == 1) {
    knownValues[0] = lastState;
  }


  // **************************
  // State 0: Boot/Init State
  // **************************
  if (knownValues[0] == 0) {
    if (headerStates[0] == 0) {
      genericHeader(0);
      loopCount = 0;
    }
    genericStateBody();
    if (sensorPoll >= 100) {
      pollGasSensor();
      pollLuxSensor();
      pollTempSensor();
      pollWeight(weightOffset,weightScale);
      sensorPoll = 0;
    }
  }

  // Some things we do for all non-boot states before the state code:
  if (knownValues[0] != 0) {

    // Get a time offset from when we arrived from 0.
    // This should be the start of the trial, regardless of state we start in.
    // Also, trigger anything that needs to be in sync.
    if (loopCount == 0) {
      timeOffs = millis();
      trigStuff = 0;
      digitalWrite(syncPin, HIGH);
    }

    // This ends the trigger.
    if (loopCount >= trigTime && trigStuff == 0) {
      digitalWrite(syncPin, LOW);
      trigStuff = 1;
    }

    //******************************************
    //@@@@@@ Start Non-Boot State Definitions.
    //******************************************

    // **************************
    // State 1: Boot/Init State
    // **************************
    if (knownValues[0] == 1) {
      if (headerStates[1] == 0) {
        visStimOff();
        genericHeader(1);
        blockStateChange = 0;
      }
      genericStateBody();
    }

    // **************************
    // State 2: Stim State
    // **************************
    else if (knownValues[0] == 2) {
      if (headerStates[2] == 0) {
        genericHeader(2);
        visStimOn();
        blockStateChange = 0;
      }
      genericStateBody();
    }

    // **************************************
    // State 3: Catch-Trial (no-stim) State
    // **************************************
    else if (knownValues[0] == 3) {
      if (headerStates[3] == 0) {
        blockStateChange = 0;
        genericHeader(3);
        visStimOn();
      }
      genericStateBody();
    }

    // **************************************
    // State 4: Reward State
    // **************************************
    else if (knownValues[0] == 4) {
      if (headerStates[4] == 0) {
        genericHeader(4);
        visStimOff();
        rewarding = 0;
        blockStateChange = 1;
      }
      genericStateBody();
      if (rewardDelivTypeA == 0 && rewarding == 0) {
        digitalWrite(rewardPinA, HIGH);
        rewarding = 1;
      }
      if (stateTime >= uint32_t(knownValues[1])) {
        digitalWrite(rewardPinA, LOW);
        blockStateChange = 0;
      }
    }

    // **************************************
    // State 5: Time-Out State
    // **************************************
    else if (knownValues[0] == 5) {
      if (headerStates[5] == 0) {
        genericHeader(5);
        visStimOff();
        blockStateChange = 1;
      }

      genericStateBody();
      // trap the state in time-out til timeout time over.
      if (stateTime >= uint32_t(knownValues[2])) {
        blockStateChange = 0;
      }
    }

    // **************************************
    // State 6: Manual Reward State
    // **************************************
    else if (knownValues[0] == 6) {
      if (headerStates[6] == 0) {
        genericHeader(6);
        //        visStimOff();
        rewarding = 0;
        blockStateChange = 0;
      }
      genericStateBody();
      if (rewardDelivTypeA == 0 && rewarding == 0) {
        digitalWrite(rewardPinA, HIGH);
        rewarding = 1;
      }
      if (stateTime >= uint32_t(knownValues[1])) {
        digitalWrite(rewardPinA, LOW);
        blockStateChange = 0;
      }
    }

    // ******* Stuff we do for all non-boot states.
    trialTime = millis() - timeOffs;
    dataReport();
    loopCount++;
  }
}

void dataReport() {
  Serial.print("tData");
  Serial.print(',');
  Serial.print(loopCount);
  Serial.print(',');
  Serial.print(trialTime);
  Serial.print(',');
  Serial.print(stateTime);
  Serial.print(',');
  Serial.print(knownValues[0]); //state
  Serial.print(',');
  Serial.print(knownValues[8]);  //load cell
  Serial.print(',');
  Serial.print(knownValues[10]); // lick sensor
  Serial.print(',');
  Serial.print(knownValues[9]); // motion
  Serial.print(',');
  Serial.println(scopeState);
}


int flagReceive(char varAr[], int valAr[]) {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char endMarker = '>';
  char feedbackMarker = '<';
  char rc;
  int nVal;
  const byte numChars = 32;
  char writeChar[numChars];
  int selectedVar = 0;
  int newData = 0;

  while (Serial.available() > 0 && newData == 0) {
    rc = Serial.read();
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
        Serial.print("echo");
        Serial.print(',');
        Serial.print(varAr[selectedVar]);
        Serial.print(',');
        Serial.print(valAr[selectedVar]);
        Serial.print(',');
        Serial.println('~');
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


void resetHeaders() {
  for ( int i = 0; i < stateCount; i++) {
    headerStates[i] = 0;
  }
}

void genericHeader(int stateNum) {
  stateTimeOffs = millis();
  resetHeaders();
  headerStates[stateNum] = 1;
}

void genericStateBody() {
  stateTime = millis() - stateTimeOffs;
  knownValues[10] = analogRead(lickPin);
  knownValues[9] = analogRead(motionPin);
  knownValues[8] = analogRead(forceSensorPin);
  scopeState = digitalRead(scopePin);
  sensorPoll++;
}

void visStimOff() {
  dashSerial.print('v');
  dashSerial.print(',');
  dashSerial.print(0);
  dashSerial.print(',');
  dashSerial.print(0);
  dashSerial.print(',');
  dashSerial.print(0);
  dashSerial.print(',');
  dashSerial.print(0);
  dashSerial.print(',');
  dashSerial.println(knownValues[7]);
}

void visStimOn() {
  dashSerial.print('v');
  dashSerial.print(',');
  dashSerial.print(knownValues[4]);
  dashSerial.print(',');
  dashSerial.print(knownValues[3]);
  dashSerial.print(',');
  dashSerial.print(knownValues[5]);
  dashSerial.print(',');
  dashSerial.print(knownValues[6]);
  dashSerial.print(',');
  dashSerial.println(knownValues[7]);
}

void pollGasSensor() {
  gasSensor.IAQmeasure();
  dashSerial.print('z');
  dashSerial.print(gasSensor.TVOC);
  dashSerial.println('>');

  dashSerial.print('y');
  dashSerial.print(gasSensor.eCO2);
  dashSerial.println('>');
}

void pollLuxSensor() {
  float lux = lidar.readLux(VL6180X_ALS_GAIN_5);

  dashSerial.print('l');
  dashSerial.print(int(lux));
  dashSerial.println('>');

  uint8_t range = lidar.readRange();
  uint8_t status = lidar.readRangeStatus();


  if (status == VL6180X_ERROR_NONE) {
    dashSerial.print('r');
    dashSerial.print(int(range));
    dashSerial.println('>');
  }
}

void pollWeight(uint32_t wOffset, float wScale) {
  dashSerial.print('w');
  dashSerial.print(int((knownValues[8] - wOffset)*wScale));
  dashSerial.println('>');
}

void pollTempSensor() {
  dashSerial.print('h');
  dashSerial.print(int(tempSensor.readHumidity()));
  dashSerial.println('>');

  dashSerial.print('t');
  dashSerial.print(int(tempSensor.readTemperature() * 1.8 + 32));
  dashSerial.println('>');
}







