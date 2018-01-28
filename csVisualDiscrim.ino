/*
  csTeensyDiscrim
  Main Teensy Script For Discrim Task. 
  Assumes a 3.2,3.5/6 teensy for speed sake.
  Will work with any MC with hardware serial.
  
  v1.1 -- cdeister@brown.edu
  changes: clean up

*/

// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  
// @@@@@@@@@@ Setup Outputs.
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 

/* We make a map of:
  a) device names
  b) interaction methods 
  for later use.
*/
char outputs[]={'scope','behavCam','ephysAmp','visStim',
  'audioDev','rewardA','rewardB'};
char outputType[]={'digital','digital','digital','serial',
  'digital','digital','digital'};

// Now we hardcode some referneces.
#define visSerial Serial1
#define fluidPinA 35
#define fluidPinB 36
#define tonePin 6

// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  
// @@@@@@@@@@ Setup Inputs.
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 

int lickSensorL = 0;
int lickSensorR = 0;
const int lickPinL = 23;
const int lickPinR = 19;

// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  
// @@@@@@@@@@ Setup Timing Related Vars.
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

int loopDelta = 1000; //in microseconds
unsigned long msOffset;
unsigned long s1Offset;

unsigned long trialTimeMicro;
unsigned long stateTimeMicro;

unsigned long pulseTime;
unsigned long delayTime;

unsigned long pulseOffset;
unsigned long delayOffset;


// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  
// @@@@@@@@@@ Setup Reinforcment Vars.
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 

int rewardTime = 50000;  // micros
int rewardBlockTime = 2000000;


// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  
// @@@@@@@@@@ Setup State Vars.
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 

int lastState;
int curState;
int headerState;

bool stateChange = 0;
bool headerFired = 0;

bool inPulse = 0;
bool cueInit = 0;




/* vars for split read */

const byte numChars = 32;
char receivedChars[numChars];
boolean newData = false;

int lastOrient = 0;
int readOrient = 0;
int orientDelta = 0;

/* ~~~~~~~~~~~~~~~~~~~~~~~~ */


void setup() {
  pinMode(fluidPinA, OUTPUT);
  pinMode(fluidPinB, OUTPUT);
  pinMode(tonePin, OUTPUT);
  pinMode(lickPinL, INPUT);
  pinMode(lickPinR, INPUT);


  Serial.begin(115200); // usb serial to python
  visSerial.begin(9600);
  while (!Serial);
  Serial.println("Start");
  delay(500);

  msOffset = micros();
  s1Offset = micros();
  pulseOffset = micros();
  delayOffset = micros();

  headerFired = 0;
}

void loop() {
  if (curState == 0) {
    msOffset=micros(); 
    // sets the total trial time
    genericHeader(curState,0,tonePin,0);
    genericBody(0,0,waterLPin);
  }

  else if (curState == 2) { 
  // init state make a green light by sending cueState = 2
    genericHeader(curState,0,tonePin,0);
    genericBody(0,0,waterLPin);
  }

  else if (curState == 3) { 
  // cue state make a blue light blink sending cueState = 3
    genericHeader(curState,0,tonePin,0);
    genericBody(0,0,waterLPin);
  }

  else if (curState == 4) { 
  // cue state make a blue light blink sending cueState = 4
    genericHeader(curState,0,tonePin,0);
    genericBody(0,0,waterLPin);
  }

  if (curState == 5) { 
  // tone state; play a tone
    genericHeader(curState,1,tonePin, toneLow);
    genericBody(0,0,waterLPin);
  }

  else if (curState == 6) { // tone state; play a tone
    genericHeader(curState,1,tonePin, toneHigh);
    genericBody(0,0,waterLPin);
  }

  else if (curState == 21) {
    genericHeader(curState,0,tonePin,0);
    genericBody(1,60,waterLPin);
  }

  else if (curState == 22) {
    genericHeader(curState,0,tonePin,0);
    genericBody(1,60,waterRPin);
  }

  else if (curState == 24) { // punish and signal with a violet light blink
    genericHeader(curState,0,tonePin,0);
    genericBody(0,0,waterLPin);
  }
  else {
    genericHeader(curState,0,tonePin,0);
    genericBody(0,0,waterLPin);
  }
}


int lookForSerialState() {
  int pyState;
  if (Serial.available() > 0) {
    pyState = Serial.read();
    lastState = pyState;
    stateChange = 1;  
    // you can use this! to trigger a header etc.
  }
  else if (Serial.available() <= 0) {
    pyState = lastState;
    stateChange = 0;
  }
  return pyState;
}

void spitData() {
  Serial.print("data,"); Serial.print(trialTimeMicro); 
  Serial.print(','); Serial.print(stateTimeMicro);
  Serial.print(','); Serial.print(readOrient); 
  Serial.print(','); Serial.print(curState);
  Serial.print(','); Serial.print(lickSensorL); 
  Serial.print(','); Serial.print(lickSensorR);
  Serial.println();
}

void genericHeader(int cueOut, bool useTone, int fPin, int fFreq) {
  noTone(tonePin);
  digitalWrite(waterLPin, LOW);
  digitalWrite(waterRPin, LOW);
  pulseOffset = millis();
  delayOffset = micros();
  s1Offset = micros();
  
  updateCueLight(cueOut);

  if (useTone == 1) {
    tone(fPin, fFreq);
  }

  headerState = curState;
  headerFired = 1;
}

void genericBody(int reward, unsigned long rewardTime, int rPin) {
  while (headerFired == 1 and headerState == curState){
    trialTimeMicro = micros() - msOffset;
    stateTimeMicro = micros() - s1Offset;
    pollLickSensors();
    if (reward){
      nonBlockPulse(rewardTime,rPin);
    }
    flagReceive('o', '>');
    showSetNewData();
    spitData();
    delayMicroseconds(loopDelta);
    curState = lookForSerialState();
  }
}

void pollLickSensors() {
  lickSensorR = analogRead(lickPinR);
  lickSensorL = analogRead(lickPinL);
}

void flagReceive(char startChars, char endChars) {
  static boolean recvInProgress = false;
  static byte ndx = 0; char startMarker = startChars;
  char endMarker = endChars; char rc;

  while (motionSerial.available() > 0 && newData == false) {
    rc = motionSerial.read();

    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      else if (rc == endMarker ) {
        receivedChars[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    }
    else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
}

void updateCueLight(int cueOut){
  cueSerialOut.print('c');
  cueSerialOut.print(cueOut);
  cueSerialOut.println('$');
}

void showSetNewData() {
  if (newData == true) {
    readOrient = int(String(receivedChars).toInt());
    lastOrient = readOrient;
    newData = false;
  }
}

void nonBlockPulse(unsigned long pulseDur, int targPin){
  pulseTime=millis()-pulseOffset;
  if (pulseTime<=pulseDur){
    digitalWrite(targPin,HIGH);
  }
  else{
    digitalWrite(targPin,LOW);
  }
  
}

