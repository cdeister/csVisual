#include <FlexiTimer2.h>

#define visSerial Serial4

// Interupt Timing Params.
int sampsPerSecond = 1000;
float evalEverySample = 1.0; // number of times to poll the vStates funtion

// Basic State Flow
uint32_t loopCount = 0;
uint32_t timeOffs;
uint32_t stateTimeOffs;
uint32_t trialTime;
uint32_t stateTime;


int lickSensorL = 0;
int lickSensorR = 0;
int motionSensor = 0;


const int lickPinL = 18;
const int lickPinR = 21;
const int motionPin = 23;
const int rewardPinA = 13;   // 35 is better, 13 is LED so good for debug.

int rewardDelivTypeA = 0; // 0 is solenoid; 1 is syringe pump
int rewardDelivTypeB = 0;

bool blockStateChange = 0;
bool rewarding = 0;

// knownLabels[]={'tState','rewardTime','timeOut','contrast','orientation','sFreq','tFreq','visVariableUpdateBlock'};
char knownHeaders[] = {'a', 'r', 't', 'c', 'o', 's', 'f', 'v'};
int knownValues[] = {0, 200, 4000, 0, 0, 0, 0, 1};
int knownCount = 7;

int headerStates[] = {0, 0, 0, 0, 0, 0};
int stateCount = 6;

int tState = knownValues[0];

int syncPin = 25;

unsigned int trigTime = 10;
bool trigStuff = 0;

void setup() {
  pinMode(syncPin, OUTPUT);
  digitalWrite(syncPin, LOW);

  pinMode(rewardPinA, OUTPUT);
  digitalWrite(rewardPinA, LOW);
  visSerial.begin(9600);
  Serial.begin(115200);
  delay(10000);
  FlexiTimer2::set(1, evalEverySample / sampsPerSecond, vStates);
  FlexiTimer2::start();
}

void loop() {
}

void vStates() {

  // We always first look for variable changes.
  // We always set tState to the serial variable entry it corresponds to.
  int rVar = flagReceive(knownHeaders, knownValues);

  // Some hardware actions need to complete before a state-change.
  // So, we have a latch.
  if (blockStateChange == 0) {
    tState = knownValues[0];
  }

  // **************************
  // State 0: Boot/Init State
  // **************************
  if (tState == 0) {
    if (headerStates[0] == 0) {
      genericHeader(0);
      loopCount = 0;
    }
  }

  // Some things we do for all non-boot states before the state code:
  if (tState != 0) {

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
      Serial.println("triggered");
    }

    //******************************************
    //@@@@@@ Start Non-Boot State Definitions.
    //******************************************

    // **************************
    // State 1: Boot/Init State
    // **************************
    if (tState == 1) {
      if (headerStates[1] == 0) {
        genericHeader(1);
      }
      genericStateBody();
    }

    // **************************
    // State 2: Stim State
    // **************************
    else if (tState == 2) {
      if (headerStates[2] == 0) {
        genericHeader(2);
        visStimOn();
      }
      genericStateBody();
    }

    // **************************************
    // State 3: Catch-Trial (no-stim) State
    // **************************************
    else if (tState == 3) {
      if (headerStates[3] == 0) {
        genericHeader(3);
      }
      genericStateBody();
    }

    // **************************************
    // State 4: Reward State
    // **************************************
    else if (tState == 4) {
      if (headerStates[4] == 0) {
        genericHeader(4);
        visStimOff();
        blockStateChange = 1;
        rewarding = 0;
      }
      genericStateBody();
      if (rewardDelivTypeA == 0 && rewarding == 0) {
        digitalWrite(rewardPinA, HIGH);
        rewarding = 1;
      }
      if (stateTime >= knownValues[1]) {
        digitalWrite(rewardPinA, LOW);
        blockStateChange = 0;
      }
    }

    // **************************************
    // State 5: Time-Out State
    // **************************************
    else if (tState == 5) {
      if (headerStates[5] == 0) {
        genericHeader(5);
        visStimOff();
        blockStateChange = 1;
      }
      genericStateBody();
      // trap the state in time-out til timeout time over.
      if (stateTime >= knownValues[2]) {
        blockStateChange = 0;
      }
    }

    // Stuff we do for all non-boot states.
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
  Serial.print(tState);
  Serial.print(',');
  Serial.print(lickSensorL);
  Serial.print(',');
  Serial.print(lickSensorR);
  Serial.print(',');
  Serial.println(motionSensor);
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
  int newData = 0;
  int selectedVar = 0;

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
        Serial.print(selectedVar);
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
  return selectedVar; // tells us if a valid variable arrived.
}


void resetHeaders() {
  for ( int i = 0; i < stateCount; i++) {
    headerStates[i] = 0;
  }
}

void pollLickSensors() {
  lickSensorR = analogRead(lickPinR);
  lickSensorL = analogRead(lickPinL);
}

void genericHeader(int stateNum) {
  stateTimeOffs = millis();
  resetHeaders();
  headerStates[stateNum] = 1;
}

void genericStateBody() {
  stateTime = millis() - stateTimeOffs;
  pollLickSensors();
  motionSensor = analogRead(motionPin);
}

void visStimOff() {
  visSerial.print('v');
  visSerial.print(',');
  visSerial.print(0);
  visSerial.print(',');
  visSerial.print(0);
  visSerial.print(',');
  visSerial.print(0);
  visSerial.print(',');
  visSerial.print(0);
  visSerial.print(',');
  visSerial.println(knownValues[7]);
}

void visStimOn() {
  visSerial.print('v');
  visSerial.print(',');
  visSerial.print(knownValues[4]);
  visSerial.print(',');
  visSerial.print(knownValues[3]);
  visSerial.print(',');
  visSerial.print(knownValues[5]);
  visSerial.print(',');
  visSerial.print(knownValues[6]);
  visSerial.print(',');
  visSerial.println(knownValues[7]);
}


