/* ~~~~ Teensey Analog Cap Relay ~~~~
   Notes: Teensey 3.6 has two built in 12 bit dacs.
   Teensey(s) LC,3.1/2, 3.5 have built in cap sensing.
   The cap sensing is awesome! But, it is blocking. 
   So, I sense on a 3.6 teensy and use its nice dacs to stream analog version of the data.
   This assumes you are using a 3.6 and wanting to convert two cap reads to an anlaog signal.

   v1.0
   cdeister@brown.edu
*/
#define tSer Serial1

const int capSensPinL = 29;
const int capSensPinR = 30;
const int dacPinL=A22;
const int dacPinR=A21;


int lickValA = 0;
int lickValB = 0;
int writeValA = 0;
int writeValB = 0;

// teensey cap is 16 bit so max val is 65535;
int maxCapVal = 65536;
int minCapVal = 0;

// teensey dac can do 12 bit of 3.3V.
// so let's round and assume 0.000-3.299 V range
int minDACVal=0;
int maxDACVal=3299;

void setup() {
  analogWriteResolution(12);
  Serial.begin(9600);
  tSer.begin(9600);
}

void loop() {

  if (Serial.available()) {
    Serial1.write(Serial.read());
  }
  if (Serial1.available()) {
    Serial.write(Serial1.read());
  }
  
  // read, map teensey vals into 
  lickValA = touchRead(capSensPinL);
  writeValA = map(lickValA, minCapVal, maxCapVal, minDACVal, maxDACVal);
  analogWrite(dacPinL, lickValA);
  
  lickValB = touchRead(capSensPinR);
  writeValB = map(lickValB, minCapVal, maxCapVal, minDACVal, maxDACVal);
  analogWrite(dacPinR, lickValB);
}
