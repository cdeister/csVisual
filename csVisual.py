#csVisual v0.3


from tkinter import *
import tkinter.filedialog as fd
import serial
import numpy as np
import h5py
import os
import datetime
import time
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import socket
import sys
# import pygsheets
from Adafruit_IO import Client
import pandas as pd

root = Tk()

#todo list:
# weight auto
# month boundary
# sheet log
# reset mq

class csVariables(object):
    
    def __init__(self,sesVarDict={},trialVars={},stimVars={}):

        self.sesVarDict={'comPath_teensy':'/dev/cu.usbmodem2762721','baudRate_teensy':115200,\
        'subjID':'an1','taskType':'detect','totalTrials':10,'logMQTT':0,'mqttUpDel':0.05,\
        'curWeight':20,'rigGMTZoneDif':5,'volPerRwd':0.01,'waterConsumed':0,'consumpTarg':1.5,'dirPath':'/'}
        
        self.trialVars={'rewardFired':0,'rewardDur':50,'trialNum':0,'trialDur':0,\
        'lickLatchA':0,'lickAThr':500,'minNoLickTime':1000}

        self.stimVars={'contrast':1,'sFreq':4,'orientation':0}

    def getRig(self):
        # returns a string that is the hostname
        mchString=socket.gethostname()
        self.hostMachine=mchString.split('.')[0]
        return self.hostMachine

class csHDF(object):

    def __init__(self,a):
        self.a=1
    
    def makeHDF(self,basePath,subID,dateStamp):

        self.sesHDF = h5py.File(basePath+"{}_behav_{}.hdf".format(subID,dateStamp), "a")
        return self.sesHDF
    
    def makeSesGroup(self,hdfObj,sessionNum):

        # if sessionNum is -1 it will guess.
        curSes=sessionNum
        if sessionNum==-1:
            exSes=0
            for keys in hdfObj:
                exSes=exSes+1
            curSes=exSes+1
        try:
            hdfGrp=hdfObj.create_group('session_{}'.format(curSes))
            self.hdfGrp=hdfGrp
        except:
            print("failed to make group; wrong hdf?")
            self.hdfGrp=[]

        return self.hdfGrp

class csMQTT(object):

    def __init__(self,dStamp):
        self.dStamp=datetime.datetime.now().strftime("%m_%d_%Y")

    def connectBroker(self,hashPath):
        
        simpHash=open(hashPath)
        self.aio = Client(simpHash.read())
        return self.aio

    def getDailyConsumption(self,mqObj,sID,rigGMTDif,hourThresh):
        # Get last reward count logged.
        # assume nothing
        waterConsumed=0
        # I assume the mqtt gmt day is the same as our rigs day for now.
        dayOffset=0
        monthOffset=0

        # but grab the last point logged on the MQTT feed.
        gDP=mqObj.receive('{}_waterConsumed'.format(sID))
        # Look at when it was logged.
        crStr=gDP.created_at[0:10]

        rigHr=int(datetime.datetime.fromtimestamp(time.time()).strftime('%H'))
        rigHr=rigHr+rigGMTDif
        # if you offset the rig for GMT and go over 24,
        # that means GMT has crossed the date line. 
        # thus, we need to add a day to our rig's day
        if rigHr>24:
            rigHr=rigHr-24
            dayOffset=1


        # add the GMT diff to the current time in our time zone.
        mqHr=int(gDP.created_at[11:13])

        #compare year (should be a given, but never know)
        if crStr[0:4]==dStamp[6:10]:

            #compare month (less of a given)
            # I allow for a month difference of 1 in case we are on a month boundary before GMT correction.
            if abs(int(crStr[5:7])-int(dStamp[0:2]))<2:
                # todo: add month boundary logic.

                #compare day if there is more than a dif of 1 then can't be 12-23.9 hours dif.
                dayDif=(int(dStamp[3:5])+dayOffset)-int(crStr[8:10])

                if abs(dayDif)<2:
                    hourDif=rigHr-mqHr

                    if hourDif<=hourThresh:
                        waterConsumed=float('{:0.3f}'.format(float(gDP.value)))
        
        self.waterConsumed=waterConsumed
        self.hourDif=hourDif
        
        return self.waterConsumed,self.hourDif

    def rigOnLog(self,mqObj,sID,sWeight,hostName,mqDel):
        
        # a) log on to the rig's on-off feed.
        mqObj.send('rig_{}'.format(hostName),1)
        time.sleep(mqDel)

        # b) log the rig string the subject is on to the subject's rig tracking feed.
        mqObj.send('{}_rig'.format(sID),'{}_on'.format(hostName))
        time.sleep(mqDel)

        # c) log the weight to subject's weight tracking feed.
        mqObj.send('{}_weight'.format(sID,sWeight),sWeight)

    def rigOffLog(self,mqObj,sID,sWeight,hostName,mqDel):
        
        # a) log off to the rig's on-off feed.
        mqObj.send('rig_{}'.format(hostName),0)
        time.sleep(mqDel)

        # b) log the rig string the subject is on to the subject's rig tracking feed.
        mqObj.send('{}_rig'.format(sID),'{}_off'.format(hostName))
        time.sleep(mqDel)

        # c) log the weight to subject's weight tracking feed.
        mqObj.send('{}_weight'.format(sID,sWeight),sWeight)

class csSerial(object):

    def __init__(self,a):
        self.a=1

    def connectComObj(self,comPath,baudRate):
        self.comObj = serial.Serial(comPath,baudRate)
        return self.comObj


    def readSerialData(self,comObj,headerString,varCount):
        sR=[]
        newData=0
        if comObj.inWaiting()>0:
            sR=comObj.readline().strip().decode()
            sR=sR.split(',')
            if len(sR)==varCount and sR[0]==headerString:
                newData=1
        self.sR=sR
        self.newData=newData
        return self.sR,self.newData

    def flushBuffer(self,comObj):
        while comObj.inWaiting()>0:
            sR=comObj.readline().strip().decode()
            sR=[]

    def checkVariable(self,varToCheck,comObj,headChar,varNumInd,fltDelay):
        returnVar=varToCheck
        comObj.write('{}<'.format(headChar).encode('utf-8'))
        time.sleep(fltDelay)
        [tString,dNew]=self.readSerialData(comObj,'echo',4)
        if dNew:
            if int(tString[1])==0:
                returnVar=int(tString[varNumInd])
        self.returnVar=returnVar
        return self.returnVar

class csPlot(object):

    def __init__(self,a):
        self.a=1

    # todo: pass list of plots to add.
    # then abstract each component.
    def makeTrialFig(self,fNum):
        
        # Make feedback figure.
        self.trialFig = plt.figure(fNum)
        plt.show(block=False)
        self.trialFig.canvas.flush_events()

        # add the lickA axes and lines.
        lA_YMin=0
        lA_YMax=1000
        self.lA_Axes=self.trialFig.add_subplot(2,2,1) #col,rows
        self.lA_Axes.set_ylim([lA_YMin,lA_YMax])
        self.lA_Axes.set_yticks([])
        self.lA_Line,=self.lA_Axes.plot([],color="olive",lw=1)

        self.trialFig.canvas.draw_idle()
        plt.show(block=False)
        self.trialFig.canvas.flush_events()
        self.lA_Axes.draw_artist(self.lA_Line)
        self.lA_Axes.draw_artist(self.lA_Axes.patch)
        self.trialFig.canvas.flush_events()

    def updateTrialFig(self,xData,yData):
        try:
            self.lA_Line.set_xdata(xData)
            self.lA_Line.set_ydata(yData)
            self.lA_Axes.set_xlim([xData[0],xData[-1]])
            self.lA_Axes.draw_artist(self.lA_Line)
            self.lA_Axes.draw_artist(self.lA_Axes.patch)
            self.trialFig.canvas.draw_idle()
            self.trialFig.canvas.flush_events()
        except:
            a=1

makeBar=0
csVar=csVariables(1)
csSesHDF=csHDF(1)
csAIO=csMQTT(1)
csSer=csSerial(1)
csPlt=csPlot(1)

# datestamp
cTime = datetime.datetime.now()
dStamp=cTime.strftime("%m_%d_%Y")

curMachine=csVar.getRig()
sesVars=csVar.sesVarDict

def getPath():
    try:
        selectPath = fd.askdirectory(title ="what what?")
    except:
        selectPath='/'

    dirPath_TV.set(selectPath)
    subjID_TV.set(os.path.basename(selectPath))
    sesVars['dirPath']=selectPath
    sesVars['subjID']=os.path.basename(selectPath)




def runDetectionTask():
    detectPlotNum=100
    sesVars['totalTrials']=int(totalTrials_TV.get())
    # make an instances of all necessary classes.
    
    
    trialVars=csVar.trialVars
    f=csSesHDF.makeHDF(sesVars['dirPath']+'/',sesVars['subjID'],dStamp)
    hdfGrp=csSesHDF.makeSesGroup(f,-1)


    # Update MQTT Feeds
    if sesVars['logMQTT']==1:
        aioHashPath='/Users/cad/simpHashes/cdIO.txt'
        # aio is csAIO's mq broker object.
        aio=csAIO.connectBroker(aioHashPath)

        sesVars['curWeight']=20 # todo: this is temporary
        try:
            csAIO.rigOnLog(aio,sesVars['subjID'],sesVars['curWeight'],curMachine,sesVars['mqttUpDel'])
        except:
            print('no mqtt logging')
            sesVars['logMQTT']=0
        
        [sesVars['waterConsumed'],hrDiff]=csAIO.getDailyConsumption(aio,sesVars['subjID'],sesVars['rigGMTZoneDif'],12)
        print(hrDiff)
        print(sesVars['waterConsumed'])


    # Make a teensy object by connecting to the main teensy.
    sesVars['comPath_teensy']=comPath_teensyTV.get()
    teensy=csSer.connectComObj(sesVars['comPath_teensy'],sesVars['baudRate_teensy'])

    # Send teensy to state 0 and flush the buffer.
    csSer.flushBuffer(teensy)
    teensy.write('a0>'.encode('utf-8'))
    time.sleep(0.01)

    csPlt.makeTrialFig(detectPlotNum)


    # Initialize some stuff
    tTeensyState=-1

    while trialVars['trialNum']<sesVars['totalTrials']:

        # Go ahead and check the state:
        tTeensyState=csSer.checkVariable(tTeensyState,teensy,'a',2,0.005)

        while tTeensyState != 0:
            print("not in 0, will force")
            teensy.write('a0>'.encode('utf-8'))
            time.sleep(0.005)
            tTeensyState=csSer.checkVariable(tTeensyState,teensy,'a',2,0.005)

        csSer.flushBuffer(teensy)

        # set up trial data handling.
        interrupt=[]
        trialTime=[]
        stateTime=[]
        teensyState=[]
        lick0_Data=[]
        lick1_Data=[]
        pythonState=[]
        thrLicksA=[]
        motion=[]

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

        rwdHead=0
        while trialOn:
            try:
                # 1) Look for data.
                [tString,dNew]=csSer.readSerialData(teensy,'tData',8)
                if dNew:
                    tInterrupt=int(tString[1])
                    tTrialTime=int(tString[2])
                    tStateTime=int(tString[3])
                    tTeensyState=int(tString[4])
                    tLick0=int(tString[5])
                    tLick1=int(tString[6])
                    tMotion=int(tString[7])


                    interrupt.append(tInterrupt)
                    trialTime.append(tTrialTime)
                    stateTime.append(tStateTime)
                    teensyState.append(tTeensyState)
                    pythonState.append(pyState)
                    lick0_Data.append(tLick0)
                    lick1_Data.append(tLick1)
                    thrLicksA.append(0)
                    motionData.append(tMotion)


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
                        if rwdHead==0:
                            sesVars['waterConsumed']=sesVars['waterConsumed']+sesVars['volPerRwd']
                            rwdHead=1
                        if tStateTime>trialVars['rewardDur']+randPad:
                            stateSync=0
                            trialOn=0

            except:
                trialOn=0


        tNum=trialVars['trialNum']
        tNPA=np.zeros([len(interrupt),9])
        tNPA[:,0]=interrupt
        tNPA[:,1]=trialTime
        tNPA[:,2]=stateTime
        tNPA[:,3]=teensyState
        tNPA[:,4]=pythonState
        tNPA[:,5]=lick0_Data
        tNPA[:,6]=lick1_Data
        tNPA[:,7]=thrLicksA
        tNPA[:,8]=motion
        hdfGrp['t{}'.format(tNum)]=tNPA
        
        
        csPlt.updateTrialFig(trialTime,lick0_Data)

        teensy.write('a0>'.encode('utf-8'))
        time.sleep(0.005)

    print('finished {} detection trials'.format(sesVars['totalTrials']))

    # Update MQTT Feeds
    if sesVars['logMQTT']==1:
        sesVars['curWeight']=21
        csAIO.rigOffLog(aio,sesVars['subjID'],sesVars['curWeight'],curMachine,sesVars['mqttUpDel'])

        # update animal's water consumed feed.
        sesVars['waterConsumed']=int(sesVars['waterConsumed']*10000)/10000
        aio.send('{}_waterConsumed'.format(sesVars['subjID']),sesVars['waterConsumed'])
        topAmount=sesVars['consumpTarg']-sesVars['waterConsumed']
        topAmount=int(topAmount*10000)/10000
        if topAmount<0:
            topAmount=0
     
        print('give {:0.3f} ml later by 12 hrs from now'.format(topAmount))
        aio.send('{}_topVol'.format(sesVars['subjID']),topAmount)
        
    teensy.close()

def closeup():
    try:
        plt.close(detectPlotNum)
        f.close()
        os._exit(1)
    except:
        os._exit(1)

# Make the main window
if makeBar==0:
    c1Wd=14
    c2Wd=8
    taskBar = Frame(root)
    root.title("csVisual")

    # blank=Label(taskBar, text="", justify=LEFT)
    # blank.grid(row=0, column=0,padx=0)

    cpRw=0
    tb = Button(taskBar,text="set path",width=8,command=getPath)
    tb.grid(row=cpRw,column=1)
    dirPath_label=Label(taskBar, text="Save Path:", justify=LEFT)
    dirPath_label.grid(row=cpRw,column=0,padx=0,sticky=W)
    dirPath_TV=StringVar(taskBar)
    dirPath_TV.set(sesVars['dirPath'])
    dirPath_entry=Entry(taskBar, width=24, textvariable=dirPath_TV)
    dirPath_entry.grid(row=cpRw+1,column=0,padx=0,columnspan=2,sticky=W)

    cpRw=2
    comPath_teensy_label=Label(taskBar, text="COM (Teensy) path:", justify=LEFT)
    comPath_teensy_label.grid(row=cpRw,column=0,padx=0,sticky=W)
    comPath_teensyTV=StringVar(taskBar)
    comPath_teensyTV.set(sesVars['comPath_teensy'])
    comPath_teensy_entry=Entry(taskBar, width=24, textvariable=comPath_teensyTV)
    comPath_teensy_entry.grid(row=cpRw+1,column=0,padx=0,columnspan=2,sticky=W)
    

    beRW=4
    baudEntry_label = Label(taskBar,text="BAUD Rate:",justify=LEFT)
    baudEntry_label.grid(row=beRW, column=0,sticky=W)
    baudSelected=IntVar(taskBar)
    baudSelected.set(115200)
    baudPick = OptionMenu(taskBar,baudSelected,115200,19200,9600)
    baudPick.grid(row=beRW, column=1,sticky=W)
    baudPick.config(width=8)

    sbRw=6
    subjID_label=Label(taskBar, text="subject id:", justify=LEFT)
    subjID_label.grid(row=sbRw,column=0,padx=0,sticky=W)
    subjID_TV=StringVar(taskBar)
    subjID_TV.set(sesVars['subjID'])
    subjID_entry=Entry(taskBar, width=10, textvariable=subjID_TV)
    subjID_entry.grid(row=sbRw,column=1,padx=0,sticky=W)
    
    
    
    ttRw=8
    teL=Label(taskBar, text="total trials:",justify=LEFT)
    teL.grid(row=ttRw,column=0,padx=0,sticky=W)
    totalTrials_TV=StringVar(taskBar)
    totalTrials_TV.set(sesVars['totalTrials'])
    te = Entry(taskBar, text="quit",width=10,textvariable=totalTrials_TV)
    te.grid(row=ttRw,column=1,padx=0,sticky=W)
    

    btnRw=10
    tb = Button(taskBar,text="shape: detection",width=c1Wd,command=runDetectionTask)
    tb.grid(row=btnRw,column=0)
    tc = Button(taskBar,text="task: detection",width=c1Wd,command=runDetectionTask)
    tc.grid(row=btnRw+1,column=0)
    td = Button(taskBar,text="quit",width=c1Wd,command=closeup)
    td.grid(row=btnRw+2,column=0)
    
    taskBar.pack(side=TOP, fill=X)
    

    makeBar=1

mainloop()


