import serial
import numpy as np
import h5py
import os
import datetime
import time

# Seed Session Variables
sesVars={'comPath_teensy':'/dev/cu.usbmodem3650661','baudRate_teensy':115200}
trialVars={'rewardFired':0,'rewardDur':50,'trialNum':0,'trialDur':0,\
'lickLatchA':0,'lickAThr':500,'minNoLickTime':1000}

# Handle hdf5
f = h5py.File('/Users/cad/'+"{}_{}.hdf".format('teztHDF','001'), "a")
exSes=0
for keys in f:
    exSes=exSes+1
curSes=exSes+1
hdfGrp=f.create_group('session_{}'.format(curSes))

# Serial Functions
def connectComObj(comPath,baudRate):
    comObj = serial.Serial(comPath,baudRate)
    return comObj


def readSerialData(comObj,headerString,varCount):
    sR=[]
    newData=0
    if comObj.inWaiting()>0:
        sR=comObj.readline().strip().decode()
        sR=sR.split(',')
        if len(sR)==varCount and sR[0]==headerString:
            newData=1
    return sR,newData

def flushBuffer(comObj):
    while comObj.inWaiting()>0:
        sR=comObj.readline().strip().decode()

# Make a teensy object by connecting to the main teensy.
teensy=connectComObj(sesVars['comPath_teensy'],sesVars['baudRate_teensy'])
teensyState=-1

# Send teensy to state 0 and flush the buffer.
flushBuffer(teensy)
teensy.write('a0>'.encode('utf-8'))
time.sleep(0.005)


while trialVars['trialNum']<10:

    # Go ahead and check the state:
    teensy.write('a<'.encode('utf-8'))
    time.sleep(0.005)
    [tString,dNew]=readSerialData(teensy,'echo',4)
    if dNew:
        if int(tString[1])==0:
            teensyState=int(tString[2])

    while teensyState != 0:
        print("not in 0, will force)")
        teensy.write('a0>'.encode('utf-8'))
        time.sleep(0.005)
        teensy.write('a<'.encode('utf-8'))
        [tString,dNew]=readSerialData(teensy,'echo',4)
        if dNew:
            if int(tString[1])==0:
                teensyState=int(tString[2])
        elif dNew==0:
            time.sleep(0.005)

    # set up trial data handling.
    interrupt=[]
    trialTime=[]
    stateTime=[]
    teensyState=[]
    lick0_Data=[]
    lick1_Data=[]
    pythonState=[]
    thrLicksA=[]


    # Temp Trial Variability
    trialOn=1
    trialVars['rewardFired']=0
    preTime=np.random.randint(200,2000)
    trialVars['rewardDur']=333
    randPad=np.random.randint(1000,3000)

    trialVars['trialDur']=preTime+trialVars['rewardDur']+randPad
    print(trialVars['trialDur']/1000)
    trialVars['trialNum']=trialVars['trialNum']+1
    print('start trial #{}'.format(trialVars['trialNum']))

    # start pyState at 1

    pyState=1
    lickCo=0  
    lastLick=0
    stateHeader=0
    trialLicks=0
    teensy.write('r{}>'.format(trialVars['rewardDur']).encode('utf-8'))
    time.sleep(0.002)
    # Send to 1, wait state.
    teensy.write('a1>'.encode('utf-8'))  


    while trialOn:
        try:
            # 1) Look for data.
            [tString,dNew]=readSerialData(teensy,'tData',7)
            if dNew:
                tInterrupt=int(tString[1])
                tTrialTime=int(tString[2])
                tStateTime=int(tString[3])
                tTeensyState=int(tString[4])
                tLick0=int(tString[5])
                tLick1=int(tString[6])


                interrupt.append(tInterrupt)
                trialTime.append(tTrialTime)
                stateTime.append(tStateTime)
                teensyState.append(tTeensyState)
                lick0_Data.append(tLick0)
                lick1_Data.append(tLick1)
                pythonState.append(pyState)
                thrLicksA.append(0)


                # look for licks
                if tLick0>trialVars['lickAThr'] and trialVars['lickLatchA']==0:
                    thrLicksA[-1]=1
                    trialVars['lickLatchA']=20
                    trialLicks=trialLicks+1
                elif tLick0<=trialVars['lickAThr'] or trialVars['lickLatchA']>0:
                    trialVars['lickLatchA']=trialVars['lickLatchA']-1

                # 2) Does pyState match tState?
                if pyState == tTeensyState:
                    stateSync=1
                elif pyState != tTeensyState:
                    stateSync=0

                # 3) Push state change if off.
                if stateSync==0:
                    teensy.write('a{}>'.format(pyState).encode('utf-8'))  

                # 4) Now look at what state you are in and evaluate accordingly
                if pyState == 1 and stateSync==1:
                    if thrLicksA[-1] == 1:
                        lickCounter=0
                        lastLick=tStateTime
                    if (tStateTime-lastLick)>trialVars['minNoLickTime'] and tStateTime>preTime:
                        stateSync=0
                        pyState=4
                        teensy.write('a4>'.encode('utf-8'))

                if pyState == 4 and stateSync==1:
                    if tStateTime>trialVars['rewardDur']+randPad:
                        stateSync=0
                        trialOn=0


        except:
            trialOn=0


    tNum=trialVars['trialNum']
    tNPA=np.zeros([len(interrupt),8])
    tNPA[:,0]=interrupt
    tNPA[:,1]=trialTime
    tNPA[:,2]=stateTime
    tNPA[:,3]=teensyState
    tNPA[:,4]=lick0_Data
    tNPA[:,5]=lick1_Data
    tNPA[:,6]=pythonState
    tNPA[:,7]=thrLicksA
    hdfGrp['t{}'.format(tNum)]=tNPA

    teensy.write('a0>'.encode('utf-8'))
    time.sleep(0.001)


f.close()
teensy.close()








