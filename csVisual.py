#csVisual v0.5
# 
# Chris Deister - cdeister@brown.edu
# Anything that is licenseable is governed by a MIT License found in the github directory. 
# Get smart by making and sharing.


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

class csVariables(object):
    
    def __init__(self,sesVarDict={},trialVars={},stimVars={}):

        self.sesVarDict={'curSession':1,'comPath_teensy':'/dev/cu.usbmodem3650661','baudRate_teensy':115200,\
        'subjID':'an1','taskType':'detect','totalTrials':10,'logMQTT':1,'mqttUpDel':0.05,\
        'curWeight':20,'rigGMTZoneDif':5,'volPerRwd':0.01,'waterConsumed':0,'consumpTarg':1.5,\
        'dirPath':'/Users/Deister/BData','hashPath':'/Users/cad','trialNum':0}

        self.trialVars={'rewardFired':0,'rewardDur':200,'trialNum':0,'trialDur':0,\
        'lickLatchA':0,'lickAThr':5000,'minNoLickTime':1000}

        self.stimVars={'contrast':1,'sFreq':4,'orientation':0}
    def getRig(self):
        # returns a string that is the hostname
        mchString=socket.gethostname()
        self.hostMachine=mchString.split('.')[0]
        return self.hostMachine
    
    def dictToPandas(self,dictName):
        curKey=[]
        curVal=[]
        for key in list(dictName.keys()):
            curKey.append(key)
            curVal.append(dictName[key])
            self.pdReturn=pd.Series(curVal,index=curKey)
        return self.pdReturn

    def pandasToDict(self,pdName,curDict,colNum):

        varIt=0
        csvNum=0

        for k in list(pdName.index):

            if len(pdName.shape)>1:
                a=pdName[colNum][varIt]
                csvNum=pdName.shape[1]
            elif len(pdName.shape)==1:
                a=pdName[varIt]

            try:
                a=float(a)
                if a.is_integer():
                    a=int(a)
                curDict[k]=a
                varIt=varIt+1

            except:
                curDict[k]=a
                varIt=varIt+1
        
        return curDict
class csHDF(object):

    def __init__(self,a):
        self.a=1
    
    def makeHDF(self,basePath,subID,dateStamp):

        self.sesHDF = h5py.File(basePath+"{}_behav_{}.hdf".format(subID,dateStamp), "a")
        return self.sesHDF
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
        hourDif=22
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
        self.trialFig.suptitle('trial # 0 of ?',fontsize=10)
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

    def quickUpdateTrialFig(self,trialNum,totalTrials):
        self.trialFig.suptitle('trial # {} of {}'.format(trialNum,totalTrials),fontsize=10)
        self.trialFig.canvas.flush_events()


    def updateTrialFig(self,xData,yData,trialNum,totalTrials):
        # try:
        self.trialFig.suptitle('trial # {} of {}'.format(trialNum,totalTrials),fontsize=10)
        self.lA_Line.set_xdata(xData)
        self.lA_Line.set_ydata(yData)
        self.lA_Axes.set_xlim([xData[0],xData[-1]])
        self.lA_Axes.draw_artist(self.lA_Line)
        self.lA_Axes.draw_artist(self.lA_Axes.patch)
        self.trialFig.canvas.draw_idle()
        self.trialFig.canvas.flush_events()
        # except:
        #     a=1
        #     # self.trialFig.canvas.flush_events()

# initialize class instances and some flags.
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
    print(sesVars)
    # if there is a sesVars.csv load it. 
    try:
        tempMeta=pd.read_csv(selectPath +'/' + 'sesVars.csv',index_col=0,header=None)
        for x in range(0,len(tempMeta)):
            varKey=tempMeta.iloc[x].name
            varVal=tempMeta.iloc[x][1]
            
            # now we need to divine curVar's data type.
            # we first try to see if it is numeric.
            try:
                tType=float(varVal)
                try:
                    tType=int(tType)
                except:
                    g=1
            except:
                tType=varVal
            sesVars[varKey]=tType
            # update any text variables that may exist.
            try:
                exec(varKey + '_TV.set({})'.format(tType))
            except:
                g=1
    except:
        g=1

    
    print(sesVars)
def runDetectionTask():
    # make a plot
    detectPlotNum=100
    # get total trials from the gui if available.
    try:
        sesVars['totalTrials']=int(totalTrials_TV.get())
    except:
        a=1
      
    trialVars=csVar.trialVars
    f=csSesHDF.makeHDF(sesVars['dirPath']+'/',sesVars['subjID'] + '_ses{}'.format(sesVars['curSession']),dStamp)
    
    # Update MQTT Feeds
    if sesVars['logMQTT']==1:
        aioHashPath=sesVars['hashPath'] + '/simpHashes/cdIO.txt'
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
    

    # Go ahead and check the state:
    tTeensyState=csSer.checkVariable(tTeensyState,teensy,'a',2,0.005)
    fb=0
    while tTeensyState != 0:
        if fb==0:
            print("not in 0, will force")
            fb=1
        teensy.write('a0>'.encode('utf-8'))
        time.sleep(0.005)
        tTeensyState=csSer.checkVariable(tTeensyState,teensy,'a',2,0.005)

    csSer.flushBuffer(teensy)

    # set up trial data handling.
    sesVars['maxDur']=7200
    sesVars['sampRate']=1000
    npSamps=sesVars['maxDur']*sesVars['sampRate']
    dStreams=9
    sesData=np.zeros([npSamps,dStreams])
    dStreamLables=['interrupt','trialTime','stateTime','teensyState','lick0_Data',\
    'lick1_Data','pythonState','thrLicksA','motion','contrast','orientation']

    # Temp Trial Variability
    sessionOn=1
    trialVars['rewardDur']=250

    preTime=np.random.randint(200,5000)
    trialVars['trialDur']=preTime+trialVars['rewardDur']


    # start pyState at 1

    pyState=1
    lickCo=0  
    lastLick=0
    stateHeader=0
    trialLicks=0
    tContrast=0
    tOrientation = 0

    rwdHead=0
    sHeaders=np.array([0,0,0,0,0,0])
    sList=[0,1,2,3,4,5]
    trialPltUpdate=1
    trialSamps=[0,0]
    sampLog=[]
    # Send to 1, wait state.
    teensy.write('a1>'.encode('utf-8'))  
    contrastList=[]
    orientationList=[]
    loopCnt=0
    while sessionOn:
        # 1) Look for data every loop
        [tString,dNew]=csSer.readSerialData(teensy,'tData',8)
        if dNew:
            tInterrupt=int(tString[1])
            tTrialTime=int(tString[2])
            tStateTime=int(tString[3])
            tTeensyState=int(tString[4])
            tLick0=int(tString[5])
            tLick1=int(tString[6])
            tMotion=int(tString[7])

            tFrameCount=0  # Todo: frame counter in.
            sesData[loopCnt,0]=int(tString[1])
            sesData[loopCnt,1]=int(tString[2])
            sesData[loopCnt,2]=int(tString[3])
            sesData[loopCnt,3]=int(tString[4])
            sesData[loopCnt,4]=pyState
            sesData[loopCnt,5]=int(tString[5])
            sesData[loopCnt,6]=int(tString[6])
            sesData[loopCnt,7]=0
            sesData[loopCnt,8]=int(tString[7])
            loopCnt=loopCnt+1
            if loopCnt>200 and np.mod(loopCnt,500)==0:
                csPlt.updateTrialFig(np.arange(len(sesData[loopCnt-200:loopCnt,8])),sesData[loopCnt-200:loopCnt,8],sesVars['trialNum'],sesVars['totalTrials'])


            # this determines if we keep running
            sesVars['totalTrials']=int(totalTrials_TV.get())
            if sesVars['trialNum']>sesVars['totalTrials']:
                sessionOn=0

            # look for licks
            if tLick0>trialVars['lickAThr'] and trialVars['lickLatchA']==0:
                sesData[-1,7]=1
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
                
                if sHeaders[pyState]==0:
                    trialSamps[0]=loopCnt-1

                    # reset counters that track state stuff.
                    lickCounter=0
                    lastLick=0
                    trialPltUpdate=1

                    # get contrast and orientation
                    tContrast=np.random.randint(0,11)
                    tOrientation=np.random.randint(0,37)
                    preTime=np.random.randint(200,5000)
                    contrastList.append(tContrast)
                    orientationList.append(tOrientation)
                    teensy.write('c{}>'.format(tContrast).encode('utf-8'))
                    teensy.write('o{}>'.format(tOrientation).encode('utf-8'))
                    # update the trial
                    sesVars['trialNum']=sesVars['trialNum']+1
                    print('start trial #{}'.format(sesVars['trialNum']))
                    print('contrast: {} orientation: {}'.format(tContrast,tOrientation))

                    # close the header and flip the others open.
                    sHeaders[pyState]=1
                    sHeaders[np.setdiff1d(sList,pyState)]=0
                # look for licks    
                if sesData[-1,7] == 1:
                    lickCounter=lickCounter+1
                    lastLick=tStateTime
                
                # exit if we've waited long enough (preTime) and animal isn't licking.
                if (tStateTime-lastLick)>trialVars['minNoLickTime'] and tStateTime>preTime:
                    # we know we will be out of sync
                    stateSync=0
                    # we set python to new state.
                    pyState=2
                    # we ask teensy to go to new state.
                    teensy.write('a2>'.encode('utf-8'))

            if pyState == 2 and stateSync==1:
                if sHeaders[pyState]==0:
                    reported=0
                    lickCounter=0
                    lastLick=0
                    minStimTime=1000
                    
                    sHeaders[pyState]=1
                    sHeaders[np.setdiff1d(sList,pyState)]=0
                
                if sesData[-1,7] == 1:
                    lickCounter=lickCounter+1
                    lastLick=tStateTime
                    if tStateTime>0.005:
                        reported=1
                        print("reported")

                if tStateTime>minStimTime:
                    if reported==1:
                        stateSync=0
                        pyState=4
                        teensy.write('a4>'.encode('utf-8'))
                    elif reported==0: #todo: this should go to 0 after some time
                        stateSync=0
                        pyState=4
                        teensy.write('a4>'.encode('utf-8'))
        
            if pyState == 4 and stateSync==1:
                if sHeaders[pyState]==0:
                    sesVars['waterConsumed']=sesVars['waterConsumed']+sesVars['volPerRwd']
                    sHeaders[pyState]=1
                    sHeaders[np.setdiff1d(sList,pyState)]=0
                
                # exit
                if tStateTime>trialVars['rewardDur']:
                    trialSamps[1]=loopCnt
                    sampLog.append(trialSamps[1]-trialSamps[0])
                    stateSync=0
                    pyState=1
                    teensy.write('a1>'.encode('utf-8'))
                    print('last trial took: {} seconds'.format(sampLog[-1]/1000))
                    print(sessionOn)
                    # if trialPltUpdate:
                    #     csPlt.updateTrialFig(sesData[trialSamps[0]:trialSamps[1],1]-sesData[trialSamps[0],1],\
                    #         sesData[trialSamps[0]:trialSamps[1],8],sesVars['trialNum'],sesVars['totalTrials'])
                    #     trialPltUpdate=0                           
    
    f["session_{}".format(sesVars['curSession'])]=sesData[0:loopCnt,:]
    f["session_{}".format(sesVars['curSession'])].attrs['contrasts']=contrastList
    f["session_{}".format(sesVars['curSession'])].attrs['orientations']=orientationList
    f.close()


    sesVars['curSession']=sesVars['curSession']+1
    teensy.write('a0>'.encode('utf-8'))
    time.sleep(0.05)
    teensy.write('a0>'.encode('utf-8'))

    print('finished {} detection trials'.format(sesVars['totalTrials']))
    sesVars['trialNum']=0
    sesVars_bindings=csVar.dictToPandas(sesVars)
    sesVars_bindings.to_csv(sesVars['dirPath'] + '/' +'sesVars.csv')

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

    sesVars_bindings=csVar.dictToPandas(sesVars)
    sesVars_bindings.to_csv(sesVars['dirPath'] + '/' +'sesVars.csv')
    try:
        plt.close(detectPlotNum)
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


