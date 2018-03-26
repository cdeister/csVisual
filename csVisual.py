# csVisual v0.8
# 
# -- fixed bug causing intermitent jitter on the order of 0.2%.
#
# Chris Deister - cdeister@brown.edu
# Anything that is licenseable is governed by a MIT License found in the github directory. 


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
from scipy.stats import norm

root = Tk()

class csVariables(object):
    def __init__(self,sesVarDict={},stimVars={}):

        self.sesVarDict={'curSession':1,'comPath_teensy':'/dev/cu.usbmodem4041951','baudRate_teensy':115200,\
        'subjID':'an1','taskType':'detect','totalTrials':10,'logMQTT':1,'mqttUpDel':0.05,\
        'curWeight':20,'rigGMTZoneDif':5,'volPerRwd':0.01,'waterConsumed':0,'consumpTarg':1.5,\
        'dirPath':'/Users/Deister/BData','hashPath':'/Users/cad','trialNum':0,'sessionOn':1,'canQuit':1,\
        'contrastChange':0,'orientationChange':1,'spatialChange':1,'dStreams':10,'rewardDur':500,'lickAThr':900,\
        'lickLatchA':0,'minNoLickTime':1000,'toTime':4000,'shapingTrial':1,'chanPlot':5,'minStimTime':1500,\
        'minTrialVar':200,'maxTrialVar':11000,'loadBaseline':114,'loadScale':0.42}

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
    def updateDictFromGUI(self,dictName):
        for key in list(dictName.keys()):
            try:
                a=eval('{}_TV.get()'.format(key))                
                try:
                    a=float(a)
                    if a.is_integer():
                        a=int(a)
                    exec('dictName["{}"]={}'.format(key,a))
                except:
                    exec('dictName["{}"]="{}"'.format(key,a))
            except:
                g=1
class csHDF(object):
    def __init__(self,a):
        self.a=1
    
    def makeHDF(self,basePath,subID,dateStamp):
        fe=os.path.isfile(basePath+"{}_behav_{}.hdf".format(subID,dateStamp))
        if fe:
            print('dupe hdf')
            os.path.isfile(basePath+"{}_behav_{}.hdf".format(subID,dateStamp))
            self.sesHDF = h5py.File(basePath+"{}_behav_{}_dup.hdf".format(subID,dateStamp), "a")
        elif fe==0:
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

    def checkVariable(self,comObj,headChar,fltDelay):
        comObj.write('{}<'.format(headChar).encode('utf-8'))
        time.sleep(fltDelay)
        [tString,self.dNew]=self.readSerialData(comObj,'echo',4)
        if self.dNew:
            if tString[1]==headChar:
                self.returnVar=int(tString[2])
        elif self.dNew==0:
            self.returnVar=0
        return self.returnVar,self.dNew
class csPlot(object):
    def __init__(self,stPlotX={},stPlotY={},stPlotRel={},pClrs={},pltX=[],pltY=[]):
        #start state
        self.stPlotX={'init':0.10,'wait':0.10,'stim':0.30,'catch':0.30,'rwd':0.50,'TO':0.50}
        self.stPlotY={'init':0.65,'wait':0.40,'stim':0.52,'catch':0.28,'rwd':0.52,'TO':0.28}
        # # todo:link actual state dict to plot state dict, now its a hack
        self.stPlotRel={'0':0,'1':1,'2':2,'3':3,'4':4,'5':5}
        self.pClrs={'right':'#D9220D','cBlue':'#33A4F3','cPurp':'#6515D9',\
        'cOrange':'#F7961D','left':'cornflowerblue','cGreen':'#29AA03'}

        self.pltX=[]
        for xVals in list(self.stPlotX.values()):
            self.pltX.append(xVals)
        self.pltY=[]
        for yVals in list(self.stPlotY.values()):
            self.pltY.append(yVals)


    def makeTrialFig(self,fNum):
        self.binDP=[]
        # Make feedback figure.
        self.trialFig = plt.figure(fNum)
        self.trialFig.suptitle('trial # 0 of  ; State # ',fontsize=10)
        self.trialFramePosition='+250+0' # can be specified elsewhere
        mng = plt.get_current_fig_manager()
        eval('mng.window.wm_geometry("{}")'.format(self.trialFramePosition))
        plt.show(block=False)
        self.trialFig.canvas.flush_events()
        
        # add the lickA axes and lines.
        lA_YMin=-100
        lA_YMax=1200
        self.lA_Axes=self.trialFig.add_subplot(2,2,1) #col,rows
        self.lA_Axes.set_ylim([lA_YMin,lA_YMax])
        self.lA_Axes.set_xticks([])
        # self.lA_Axes.set_yticks([])
        self.lA_Line,=self.lA_Axes.plot([],color="cornflowerblue",lw=1)
        self.trialFig.canvas.draw_idle()
        plt.show(block=False)
        self.trialFig.canvas.flush_events()
        self.lA_Axes.draw_artist(self.lA_Line)
        self.lA_Axes.draw_artist(self.lA_Axes.patch)
        self.trialFig.canvas.flush_events()

        # STATE AXES
        self.stAxes = self.trialFig.add_subplot(2,2,2) #col,rows
        self.stAxes.set_ylim([-0.02,1.02])
        self.stAxes.set_xlim([-0.02,1.02])
        self.stAxes.set_axis_off()
        self.stMrkSz=28
        self.txtOff=-0.02
        self.stPLine,=self.stAxes.plot(self.pltX,self.pltY,marker='o',\
            markersize=self.stMrkSz,markeredgewidth=2,\
            markerfacecolor="white",markeredgecolor="black",lw=0)
        k=0
        for stAnTxt in list(self.stPlotX.keys()):
            tASt="{}".format(stAnTxt)
            self.stAxes.text(self.pltX[k],self.pltY[k]+self.txtOff,tASt,\
                horizontalalignment='center',fontsize=9,fontdict={'family': 'monospace'})
            k=k+1

        self.curStLine,=self.stAxes.plot(self.pltX[1],self.pltY[1],marker='o',markersize=self.stMrkSz+2,\
            markeredgewidth=2,markerfacecolor=self.pClrs['cBlue'],markeredgecolor='black',lw=0,alpha=0.5)
        plt.show(block=False)
        
        self.trialFig.canvas.flush_events()
        self.stAxes.draw_artist(self.stPLine)
        self.stAxes.draw_artist(self.curStLine)
        self.stAxes.draw_artist(self.stAxes.patch)

        # OUTCOME AXES
        self.outcomeAxis=self.trialFig.add_subplot(2,2,3) #col,rows
        self.outcomeAxis.axis([-2,100,-0.2,5.2])
        self.outcomeAxis.yaxis.tick_left()

        self.stimOutcomeLine,=self.outcomeAxis.plot([],[],marker="o",markeredgecolor="black",\
            markerfacecolor="cornflowerblue",markersize=12,lw=0,alpha=0.5,markeredgewidth=2)
        
        self.noStimOutcomeLine,=self.outcomeAxis.plot([],[],marker="o",markeredgecolor="black",\
            markerfacecolor="red",markersize=12,lw=0,alpha=0.5,markeredgewidth=2)
        self.outcomeAxis.set_title('dprime: ',fontsize=10)
        self.binDPOutcomeLine,=self.outcomeAxis.plot([],[],color="black",lw=1)
        plt.show(block=False)
        self.trialFig.canvas.flush_events()
        self.outcomeAxis.draw_artist(self.stimOutcomeLine)
        self.outcomeAxis.draw_artist(self.noStimOutcomeLine)
        self.outcomeAxis.draw_artist(self.binDPOutcomeLine)
        self.outcomeAxis.draw_artist(self.outcomeAxis.patch)

    def quickUpdateTrialFig(self,trialNum,totalTrials,curState):
        self.trialFig.suptitle('trial # {} of {}; State # {}'.format(trialNum,totalTrials,curState),fontsize=10)
        self.trialFig.canvas.flush_events()

    def updateTrialFig(self,xData,yData,trialNum,totalTrials,curState):
        try:
            self.trialFig.suptitle('trial # {} of {}; State # {}'.format(trialNum,totalTrials,curState),fontsize=10)
            self.lA_Line.set_xdata(xData)
            self.lA_Line.set_ydata(yData)
            self.lA_Axes.set_xlim([xData[0],xData[-1]])
            self.lA_Axes.draw_artist(self.lA_Line)
            self.lA_Axes.draw_artist(self.lA_Axes.patch)
            

            self.trialFig.canvas.draw_idle()
            self.trialFig.canvas.flush_events()

        except:
             a=1
    
    def updateStateFig(self,curState):
        try:
            self.curStLine.set_xdata(self.pltX[curState])
            self.curStLine.set_ydata(self.pltY[curState])
            self.stAxes.draw_artist(self.stPLine)
            self.stAxes.draw_artist(self.curStLine)
            self.stAxes.draw_artist(self.stAxes.patch)

            self.trialFig.canvas.draw_idle()
            self.trialFig.canvas.flush_events()

        except:
             a=1

    def updateOutcome(self,stimTrials,stimResponses,noStimTrials,noStimResponses,totalTrials):
        sM=0.001
        nsM=0.001
        dpBinSz=10

        if len(stimResponses)>0:
            sM=int(np.mean(stimResponses)*100)*0.01
        if len(noStimResponses)>0:
            nsM=int(np.mean(noStimResponses)*100)*0.01
        


        dpEst=norm.ppf(max(sM,0.0001))-norm.ppf(max(nsM,0.0001))
        # self.outcomeAxis.set_title('CR: {} , FR: {}'.format(sM,nsM),fontsize=10)
        self.outcomeAxis.set_title('dprime: {}'.format(dpEst),fontsize=10)
        self.stimOutcomeLine.set_xdata(stimTrials)
        self.stimOutcomeLine.set_ydata(stimResponses)
        self.noStimOutcomeLine.set_xdata(noStimTrials)
        self.noStimOutcomeLine.set_ydata(noStimResponses)
        
        if (len(noStimResponses)+len(stimResponses))>=dpBinSz:
            sMb=int(np.mean(stimResponses[-dpBinSz:])*100)*0.01
            nsMb=int(np.mean(noStimResponses[-dpBinSz:])*100)*0.01
            self.binDP.append(norm.ppf(max(sMb,0.0001))-norm.ppf(max(nsMb,0.0001)))
            self.binDPOutcomeLine.set_xdata(np.linspace(1,len(self.binDP),len(self.binDP)))
            self.binDPOutcomeLine.set_ydata(self.binDP)
            self.outcomeAxis.draw_artist(self.binDPOutcomeLine)
        
        self.outcomeAxis.set_xlim([-1,totalTrials+1])
        self.outcomeAxis.draw_artist(self.stimOutcomeLine)
        self.outcomeAxis.draw_artist(self.noStimOutcomeLine)
        self.outcomeAxis.draw_artist(self.outcomeAxis.patch)

        self.trialFig.canvas.draw_idle()
        self.trialFig.canvas.flush_events()

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$ Main Program Body $$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# initialize class instances and some flags.
makeBar=0
csVar=csVariables(1)
csSesHDF=csHDF(1)
csAIO=csMQTT(1)
csSer=csSerial(1)
csPlt=csPlot(1)

csPlt.makeTrialFig(100)

# datestamp/rig id/session variables
cTime = datetime.datetime.now()
dStamp=cTime.strftime("%m_%d_%Y")
curMachine=csVar.getRig()
sesVars=csVar.sesVarDict

# ****************************
# ***** trial data logging ***
# ****************************

# pre-alloc lists for variables that only change across trials.

contrastList=[]
orientationList=[]
spatialFreqs=[]
waitPad=[]


def getPath():
    try:
        selectPath = fd.askdirectory(title ="what what?")
    except:
        selectPath='/'

    dirPath_TV.set(selectPath)
    subjID_TV.set(os.path.basename(selectPath))
    sesVars['dirPath']=selectPath
    sesVars['subjID']=os.path.basename(selectPath)
    tc['state'] = 'normal'
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
                if int(tType)==tType:
                    tType=int(tType)
                # update any text variables that may exist.
                try:
                    exec(varKey + '_TV.set({})'.format(tType))
                except:
                    g=1
            except:
                tType=varVal
                # update any text variables that may exist.
                try:
                    exec(varKey + '_TV.set("{}")'.format(tType))
                except:
                    g=1
            sesVars[varKey]=tType
    except:
        g=1

def runDetectionTask():
    
    # A) Update the dict from gui, in case the user changed things.
    csVar.updateDictFromGUI(sesVars) 

        
    # C) Create a com object to talk to the main Teensy.
    sesVars['comPath_teensy']=comPath_teensy_TV.get()
    teensy=csSer.connectComObj(sesVars['comPath_teensy'],sesVars['baudRate_teensy'])

    # D) Task specific: preallocate sensory variables that need randomization.
    # prealloc random stuff (assume no more than 1k trials)
    maxTrials=1000
    sesVars['contrastChange']=1
    if sesVars['contrastChange']:
        contList=np.array([0,0,0,1,2,5,10,20,40,50,70,90,100,100])
        randContrasts=contList[np.random.randint(0,len(contList),size=maxTrials)]
    elif sesVars['contrastChange']==0:
        defaultContrast=100
        randContrasts=defaultContrast*np.ones(maxTrials)
        teensy.write('c{}>'.format(defaultContrast).encode('utf-8'))
    sesVars['orientationChange']=1
    if sesVars['orientationChange']:
        orientList=np.array([90,0,270])
        # orientList=np.array([0,45,90,120,180,225,270,315])
        randOrientations=orientList[np.random.randint(0,len(orientList),size=maxTrials)]
    elif sesVars['orientationChange']==0:
        defaultOrientation=0
        randOrientations=defaultOrientation*np.ones(maxTrials)
        teensy.write('o{}>'.format(defaultOrientation).encode('utf-8'))
    randSpatialContinuous=0
    sesVars['spatialChange']=1
    if sesVars['spatialChange']:
        randSpatials=np.random.randint(0,5,size=maxTrials)
    elif sesVars['spatialChange']==0:
        defaultSpatial=1
        randSpatials=defaultSpatial*np.ones(maxTrials)
        teensy.write('s{}>'.format(defaultSpatial).encode('utf-8'))

    randWaitTimePad=np.random.randint(sesVars['minTrialVar'],sesVars['maxTrialVar'],size=maxTrials)

    # D) Flush the teensy serial buffer. Send it to the init state (#0).
    csSer.flushBuffer(teensy)
    teensy.write('a0>'.encode('utf-8'))
    time.sleep(0.01)

    # E) Make sure the main Teensy is actually in state 0.
    # check the state.
    sChecked=0
    while sChecked==0:
        [tTeensyState,sChecked]=csSer.checkVariable(teensy,'a',0.005)

    while tTeensyState != 0:
        print("not in 0, will force")
        teensy.write('a0>'.encode('utf-8'))
        time.sleep(0.005)
        cReturn=csSer.checkVariable(teensy,'a',0.005)
        if cReturn(1)==1:
            tTeensyState=cReturn(0)
    
    # F) Get lick sensor and load cell baseline. Estimate and log weight.
    try:
        wVals=[]
        lIt=0
        while lIt<=50:
            [rV,vN]=csSer.checkVariable(teensy,'w',0.002)
            if vN:
                wVals.append(rV)
                lIt=lIt+1
        sesVars['curWeight']=(np.mean(wVals)-sesVars['loadBaseline'])*sesVars['loadScale'];
        preWeight=sesVars['curWeight']
    except:
        sesVars['curWeight']=20

    # Optional: Update MQTT Feeds
    if sesVars['logMQTT']==1:

        aioHashPath=sesVars['hashPath'] + '/simpHashes/cdIO.txt'
        # aio is csAIO's mq broker object.
        aio=csAIO.connectBroker(aioHashPath)
        
        try:
            csAIO.rigOnLog(aio,sesVars['subjID'],sesVars['curWeight'],curMachine,sesVars['mqttUpDel'])
        except:
            print('no mqtt logging')
            sesVars['logMQTT']=0
            logMQTT_Toggle.deselect()
        [sesVars['waterConsumed'],hrDiff]=csAIO.getDailyConsumption(aio,sesVars['subjID'],sesVars['rigGMTZoneDif'],12)
        print('{} already had {} ml'.format(sesVars['subjID'],sesVars['waterConsumed']))

    # F) Set some session flow variables before the task begins
    # Turn the session on. 
    sesVars['sessionOn']=1
    # Set the state of the quit button to 0, it now ends the session.
    # This is part of the scheme to ensure data always gets saved. 
    sesVars['canQuit']=0
    quitButton['text']="End Ses"
    # For reference, confirm the Teensy's interrupt (sampling) rate. 
    sesVars['sampRate']=1000
    # Set maxDur to be two hours.
    sesVars['maxDur']=60*60*sesVars['sampRate']*2
    # Determine the max samples. We preallocate a numpy array to this depth.
    npSamps=sesVars['maxDur']
    sesData=np.zeros([npSamps,sesVars['dStreams']])
    dStreamLables=['interrupt','trialTime','stateTime','teensyState','lick0_Data',\
    'lick1_Data','pythonState','thrLicksA','motion','contrast','orientation']

    # Temp Trial Variability
    sesVars['curSession']=int(curSession_TV.get())
    f=csSesHDF.makeHDF(sesVars['dirPath']+'/',sesVars['subjID'] + '_ses{}'.format(sesVars['curSession']),dStamp)
    print('debug made hdf')
    pyState=1
    lastLick=0
    lickCounter=0
    
    tContrast=0
    tOrientation=0

    sHeaders=np.array([0,0,0,0,0,0])
    sList=[0,1,2,3,4,5]
    trialSamps=[0,0]
    
    
    sampLog=[]
    
    tc['state'] = 'disabled'
    stimResponses=[]
    stimTrials=[]
    noStimResponses=[]
    noStimTrials=[]
    print('debug past hdf')
    loopCnt=0
    sesVars['trialNum']=0
    sesVars['lickLatchA']=0
    outSyncCount=0

    # Send to 1, wait state.
    teensy.write('a1>'.encode('utf-8')) 
    while sesVars['sessionOn']:
        # try to execute the task.
        try:
            
            # a) Do we keep running?
            sesVars['totalTrials']=int(totalTrials_TV.get())
            try:
                sesVars['shapingTrial']=int(shapingTrial_TV.get())
            except:
                sesVars['shapingTrial']=0
                shapingTrial_TV.set('0')
            sesVars['lickAThr']=int(lickAThr_TV.get())
            sesVars['chanPlot']=chanPlotIV.get()
            sesVars['minStimTime']=int(minStimTime_TV.get())
            if sesVars['trialNum']>sesVars['totalTrials']:
                sesVars['sessionOn']=0

            
            # b) Look for teensy data.
            [tString,dNew]=csSer.readSerialData(teensy,'tData',9)
            if dNew:
                tStateTime=int(tString[3])
                tTeensyState=int(tString[4])
        

                tFrameCount=0  # Todo: frame counter in.
                for x in range(0,sesVars['dStreams']-2):
                    sesData[loopCnt,x]=int(tString[x+1])
                sesData[loopCnt,8]=pyState # The state python wants to be.
                sesData[loopCnt,9]=0 # Thresholded licks
                loopCnt=loopCnt+1
                
                # Plot updates.
                plotSamps=200
                updateCount=500
                if loopCnt>plotSamps and np.mod(loopCnt,updateCount)==0:
                    csPlt.updateTrialFig(np.arange(len(sesData[loopCnt-plotSamps:loopCnt,sesVars['chanPlot']])),\
                        sesData[loopCnt-plotSamps:loopCnt,sesVars['chanPlot']],sesVars['trialNum'],sesVars['totalTrials'],tTeensyState)


                # look for licks
                latchTime=50
                if sesData[loopCnt-1,5]>=sesVars['lickAThr'] and sesVars['lickLatchA']==0:
                    sesData[loopCnt-1,9]=1
                    sesVars['lickLatchA']=latchTime
                    # these are used in states
                    lickCounter=lickCounter+1
                    lastLick=tStateTime

                elif sesVars['lickLatchA']>0:
                    sesVars['lickLatchA']=sesVars['lickLatchA']-1

                # 2) Does pyState match tState?
                if pyState == tTeensyState:
                    stateSync=1

                elif pyState != tTeensyState:
                    stateSync=0
                
                
                # If we are out of sync for too long, push another change.
                if stateSync==0:
                    outSyncCount=outSyncCount+1
                    if outSyncCount>=100:
                        teensy.write('a{}>'.format(pyState).encode('utf-8'))  

                # 4) Now look at what state you are in and evaluate accordingly
                if pyState == 1 and stateSync==1:
                    
                    if sHeaders[pyState]==0:
                        sesVars['trialNum']=sesVars['trialNum']+1

                        csPlt.updateStateFig(1)
                        trialSamps[0]=loopCnt-1

                        # reset counters that track state stuff.
                        lickCounter=0
                        lastLick=0                    
                        outSyncCount=0
                        # get contrast and orientation
                        # trials are 0 until incremented, so incrementing
                        # trial after these picks ensures 0 indexing without -1.
                        tContrast=randContrasts[sesVars['trialNum']]
                        tOrientation=randOrientations[sesVars['trialNum']]
                        tSpatial=randSpatials[sesVars['trialNum']]
                        preTime=randWaitTimePad[sesVars['trialNum']]

                        contrastList.append(tContrast)
                        orientationList.append(tOrientation)
                        spatialFreqs.append(tSpatial)
                        waitPad.append(preTime)

                        # update visual stim params
                        teensy.write('c{}>'.format(tContrast).encode('utf-8'))
                        teensy.write('o{}>'.format(tOrientation).encode('utf-8'))
                        teensy.write('s{}>'.format(tSpatial).encode('utf-8'))
                       
                        # update the trial
                        print('start trial #{}'.format(sesVars['trialNum']))
                        print('contrast: {:0.2f} orientation: {}'.format(tContrast,tOrientation))

                        # close the header and flip the others open.
                        sHeaders[pyState]=1
                        sHeaders[np.setdiff1d(sList,pyState)]=0
                    
                    # exit if we've waited long enough (preTime) and animal isn't licking.
                    if (tStateTime-lastLick)>sesVars['minNoLickTime'] and tStateTime>preTime:
                        # we know we will be out of sync
                        stateSync=0
                        # we set python to new state.
                        if tContrast>0:
                            pyState=2
                            # we ask teensy to go to new state.
                            teensy.write('a2>'.encode('utf-8'))
                        elif tContrast==0:
                            pyState=3
                            # we ask teensy to go to new state.
                            teensy.write('a3>'.encode('utf-8'))
                if pyState == 2 and stateSync==1:
                    if sHeaders[pyState]==0:
                        csPlt.updateStateFig(pyState)
                        reported=0
                        lickCounter=0
                        lastLick=0
                        outSyncCount=0
                        sHeaders[pyState]=1
                        sHeaders[np.setdiff1d(sList,pyState)]=0                        
     
                    if lastLick>0.01:
                        reported=1

                    if tStateTime>sesVars['minStimTime']:
                        if reported==1 or sesVars['shapingTrial']:
                            stimTrials.append(sesVars['trialNum'])
                            stimResponses.append(1)
                            stateSync=0
                            pyState=4
                            teensy.write('a4>'.encode('utf-8'))
                            csPlt.updateOutcome(stimTrials,stimResponses,noStimTrials,noStimResponses,sesVars['totalTrials'])
                        elif reported==0:
                            stimTrials.append(sesVars['trialNum'])
                            stimResponses.append(0)
                            stateSync=0
                            pyState=1
                            trialSamps[1]=loopCnt
                            sampLog.append(np.diff(trialSamps)[0])
                            teensy.write('a1>'.encode('utf-8'))
                            csPlt.updateOutcome(stimTrials,stimResponses,noStimTrials,noStimResponses,sesVars['totalTrials'])
                            print('miss: last trial took: {} seconds'.format(sampLog[-1]/1000))

                
                if pyState == 3 and stateSync==1:
                    if sHeaders[pyState]==0:
                        csPlt.updateStateFig(pyState)
                        reported=0
                        lickCounter=0
                        lastLick=0
                        outSyncCount=0
                        sHeaders[pyState]=1
                        sHeaders[np.setdiff1d(sList,pyState)]=0
     
                    if lastLick>0.005:
                        reported=1

                    if tStateTime>sesVars['minStimTime']:
                        if reported==1:
                            noStimTrials.append(sesVars['trialNum'])
                            noStimResponses.append(1)
                            stateSync=0
                            pyState=5
                            teensy.write('a5>'.encode('utf-8'))
                            csPlt.updateOutcome(stimTrials,stimResponses,noStimTrials,noStimResponses,sesVars['totalTrials'])
                        elif reported==0:
                            noStimTrials.append(sesVars['trialNum'])
                            noStimResponses.append(0)
                            stateSync=0
                            pyState=1
                            trialSamps[1]=loopCnt
                            sampLog.append(np.diff(trialSamps)[0])
                            teensy.write('a1>'.encode('utf-8'))
                            csPlt.updateOutcome(stimTrials,stimResponses,noStimTrials,noStimResponses,sesVars['totalTrials'])
                            print('cor rejection: last trial took: {} seconds'.format(sampLog[-1]/1000))

                if pyState == 4 and stateSync==1:
                    if sHeaders[pyState]==0:
                        csPlt.updateStateFig(pyState)
                        lickCounter=0
                        lastLick=0
                        outSyncCount=0
                        sesVars['waterConsumed']=sesVars['waterConsumed']+sesVars['volPerRwd']
                        sHeaders[pyState]=1
                        sHeaders[np.setdiff1d(sList,pyState)]=0
                    
                    # exit
                    if tStateTime>sesVars['rewardDur']:
                        trialSamps[1]=loopCnt
                        sampLog.append(np.diff(trialSamps)[0])
                        stateSync=0
                        pyState=1
                        outSyncCount=0
                        teensy.write('a1>'.encode('utf-8'))
                        print('last trial took: {} seconds'.format(sampLog[-1]/1000))

                if pyState == 5 and stateSync==1:
                    if sHeaders[pyState]==0:
                        csPlt.updateStateFig(pyState)
                        lickCounter=0
                        lastLick=0
                        outSyncCount=0
                        sHeaders[pyState]=1
                        sHeaders[np.setdiff1d(sList,pyState)]=0
                    
                    # exit
                    if tStateTime>sesVars['toTime']:
                        trialSamps[1]=loopCnt
                        sampLog.append(np.diff(trialSamps)[0])
                        stateSync=0
                        pyState=1
                        teensy.write('a1>'.encode('utf-8'))
                        print('last trial took: {} seconds'.format(sampLog[-1]/1000))
        except:
            
            tc['state'] = 'normal'
            sesVars['curSession']=sesVars['curSession']+1
            curSession_TV.set(sesVars['curSession'])
            teensy.write('a0>'.encode('utf-8'))
            time.sleep(0.05)
            teensy.write('a0>'.encode('utf-8'))

            print('finished {} trials'.format(sesVars['trialNum']-1))
            sesVars['trialNum']=0
            csVar.updateDictFromGUI(sesVars)
            sesVars_bindings=csVar.dictToPandas(sesVars)
            sesVars_bindings.to_csv(sesVars['dirPath'] + '/' +'sesVars.csv')

            f["session_{}".format(sesVars['curSession']-1)]=sesData[0:loopCnt,:]
            f["session_{}".format(sesVars['curSession']-1)].attrs['contrasts']=contrastList
            f["session_{}".format(sesVars['curSession'])].attrs['stimResponses']=stimResponses
            f["session_{}".format(sesVars['curSession'])].attrs['stimTrials']=stimTrials
            f["session_{}".format(sesVars['curSession'])].attrs['noStimResponses']=noStimResponses
            f["session_{}".format(sesVars['curSession'])].attrs['noStimTrials']=noStimTrials
            f["session_{}".format(sesVars['curSession']-1)].attrs['orientations']=orientationList
            f["session_{}".format(sesVars['curSession']-1)].attrs['spatialFreqs']=spatialFreqs
            f["session_{}".format(sesVars['curSession']-1)].attrs['waitTimePads']=waitPad
            f["session_{}".format(sesVars['curSession']-1)].attrs['trialDurs']=sampLog
            f.close()

            

            # Update MQTT Feeds
            if sesVars['logMQTT']==1:
                try:
                    sesVars['curWeight']=(np.mean(sesData[-200:-1,4])-sesVars['loadBaseline'])*sesVars['loadScale'];
                except:
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
            
            csSer.flushBuffer(teensy) 
            teensy.close()
            sesVars['canQuit']=1
            quitButton['text']="Quit"
                         
    
    f["session_{}".format(sesVars['curSession'])]=sesData[0:loopCnt,:]
    f["session_{}".format(sesVars['curSession'])].attrs['contrasts']=contrastList
    f["session_{}".format(sesVars['curSession'])].attrs['stimResponses']=stimResponses
    f["session_{}".format(sesVars['curSession'])].attrs['stimTrials']=stimTrials
    f["session_{}".format(sesVars['curSession'])].attrs['noStimResponses']=noStimResponses
    f["session_{}".format(sesVars['curSession'])].attrs['noStimTrials']=noStimTrials
    f["session_{}".format(sesVars['curSession'])].attrs['orientations']=orientationList
    f["session_{}".format(sesVars['curSession'])].attrs['spatialFreqs']=spatialFreqs
    f["session_{}".format(sesVars['curSession'])].attrs['waitTimePads']=waitPad
    f["session_{}".format(sesVars['curSession'])].attrs['trialDurs']=sampLog

    
    f.close()

    tc['state'] = 'normal'
    sesVars['curSession']=sesVars['curSession']+1
    curSession_TV.set(sesVars['curSession'])
    teensy.write('a0>'.encode('utf-8'))
    time.sleep(0.05)
    teensy.write('a0>'.encode('utf-8'))

    print('finished {} trials'.format(sesVars['trialNum']-1))
    sesVars['trialNum']=0
    csVar.updateDictFromGUI(sesVars)
    sesVars_bindings=csVar.dictToPandas(sesVars)
    sesVars_bindings.to_csv(sesVars['dirPath'] + '/' +'sesVars.csv')

    # Update MQTT Feeds
    if sesVars['logMQTT']==1:
        try:
            sesVars['curWeight']=(np.mean(sesData[loopCnt-plotSamps:loopCnt,4])-sesVars['loadBaseline'])*sesVars['loadScale'];
        except:
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
    
    csSer.flushBuffer(teensy)
    teensy.close()
    sesVars['canQuit']=1
    quitButton['text']="Quit"

def closeup():
    tc['state'] = 'normal'
    csVar.updateDictFromGUI(sesVars)
    try:
        sesVars_bindings=csVar.dictToPandas(sesVars)
        sesVars_bindings.to_csv(sesVars['dirPath'] + '/' +'sesVars.csv')
    except:
        g=1

    try:
        sesVars['sessionOn']=0
    except:
        sesVars['canQuit']=1
        quitButton['text']="Quit"


    if sesVars['canQuit']==1:
        # try to close a plot and exit    
        try:
            plt.close(detectPlotNum)
            os._exit(1)
        # else exit
        except:
            os._exit(1)

# Make the main window
if makeBar==0:
    c1Wd=14
    c2Wd=8
    taskBar = Frame(root)
    root.title("csVisual")

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
    comPath_teensy_TV=StringVar(taskBar)
    comPath_teensy_TV.set(sesVars['comPath_teensy'])
    comPath_teensy_entry=Entry(taskBar, width=24, textvariable=comPath_teensy_TV)
    comPath_teensy_entry.grid(row=cpRw+1,column=0,padx=0,columnspan=2,sticky=W)
    
    beRW=4
    baudEntry_label = Label(taskBar,text="BAUD Rate:",justify=LEFT)
    baudEntry_label.grid(row=beRW, column=0,sticky=W)
    baudSelected=IntVar(taskBar)
    baudSelected.set(115200)
    baudPick = OptionMenu(taskBar,baudSelected,115200,19200,9600)
    baudPick.grid(row=beRW, column=1,sticky=W)
    baudPick.config(width=8)

    sbRw=5
    subjID_label=Label(taskBar, text="Subject ID:", justify=LEFT)
    subjID_label.grid(row=sbRw,column=0,padx=0,sticky=W)
    subjID_TV=StringVar(taskBar)
    subjID_TV.set(sesVars['subjID'])
    subjID_entry=Entry(taskBar, width=10, textvariable=subjID_TV)
    subjID_entry.grid(row=sbRw,column=1,padx=0,sticky=W)

    ttRw=6
    teL=Label(taskBar, text="Total Trials:",justify=LEFT)
    teL.grid(row=ttRw,column=0,padx=0,sticky=W)
    totalTrials_TV=StringVar(taskBar)
    totalTrials_TV.set(sesVars['totalTrials'])
    te = Entry(taskBar, text="Quit",width=10,textvariable=totalTrials_TV)
    te.grid(row=ttRw,column=1,padx=0,sticky=W)
    
    
    ttRw=7
    teL=Label(taskBar, text="Current Session:",justify=LEFT)
    teL.grid(row=ttRw,column=0,padx=0,sticky=W)
    curSession_TV=StringVar(taskBar)
    curSession_TV.set(sesVars['curSession'])
    te = Entry(taskBar,width=10,textvariable=curSession_TV)
    te.grid(row=ttRw,column=1,padx=0,sticky=W)

    lcThrRw=8
    lickAThr_label=Label(taskBar, text="Lick Thresh:", justify=LEFT)
    lickAThr_label.grid(row=lcThrRw,column=0,padx=0,sticky=W)
    lickAThr_TV=StringVar(taskBar)
    lickAThr_TV.set(sesVars['lickAThr'])
    lickAThr_entry=Entry(taskBar, width=10, textvariable=lickAThr_TV)
    lickAThr_entry.grid(row=lcThrRw,column=1,padx=0,sticky=W)

    lcThrRw=9
    minStimTime_label=Label(taskBar, text="Min Stim Time:", justify=LEFT)
    minStimTime_label.grid(row=lcThrRw,column=0,padx=0,sticky=W)
    minStimTime_TV=StringVar(taskBar)
    minStimTime_TV.set(sesVars['minStimTime'])
    minStimTime_entry=Entry(taskBar, width=10, textvariable=minStimTime_TV)
    minStimTime_entry.grid(row=lcThrRw,column=1,padx=0,sticky=W)


    sBtRw=10
    shapingTrial_label=Label(taskBar, text="Shaping Trial (0/1):", justify=LEFT)
    shapingTrial_label.grid(row=sBtRw,column=0,padx=0,sticky=W)
    shapingTrial_TV=StringVar(taskBar)
    shapingTrial_TV.set(sesVars['shapingTrial'])
    shapingTrial_entry=Entry(taskBar, width=10, textvariable=shapingTrial_TV)
    shapingTrial_entry.grid(row=sBtRw,column=1,padx=0,sticky=W)

    # Main Buttons
    ttRw=11
    blL=Label(taskBar, text=" ——————— ",justify=LEFT)
    blL.grid(row=ttRw,column=0,padx=0,sticky=W)

    cprw=12
    chanPlotIV=IntVar()
    chanPlotIV.set(sesVars['chanPlot'])
    Radiobutton(taskBar, text="Load Cell", variable=chanPlotIV, value=4).grid(row=cprw,column=0,padx=0,sticky=W)
    Radiobutton(taskBar, text="Lick Sensor", variable=chanPlotIV, value=5).grid(row=cprw+1,column=0,padx=0,sticky=W)
    Radiobutton(taskBar, text="Motion", variable=chanPlotIV, value=6).grid(row=cprw+2,column=0,padx=0,sticky=W)
    Radiobutton(taskBar, text="Scope", variable=chanPlotIV, value=7).grid(row=cprw,column=1,padx=0,sticky=W)
    Radiobutton(taskBar, text="Thr Licks", variable=chanPlotIV, value=9).grid(row=cprw+1,column=1,padx=0,sticky=W)


    # MQTT Stuff

    ttRw=15
    blL=Label(taskBar, text=" ——————— ",justify=LEFT)
    blL.grid(row=ttRw,column=0,padx=0,sticky=W)

    btnRw=16
    logMQTT_SV=StringVar()
    logMQTT_Toggle=Checkbutton(taskBar,text="Log MQTT Info?",variable=sesVars['logMQTT'],onvalue=1,offvalue=0)
    logMQTT_Toggle.grid(row=btnRw,column=0)
    logMQTT_Toggle.select()

    ttRw=17
    hpL=Label(taskBar, text="Hash Path:",justify=LEFT)
    hpL.grid(row=ttRw,column=0,padx=0,sticky=W)
    hashPath_TV=StringVar(taskBar)
    hashPath_TV.set(sesVars['hashPath'])
    te = Entry(taskBar,width=10,textvariable=hashPath_TV)
    te.grid(row=ttRw,column=1,padx=0,sticky=W)

    ttRw=18
    vpR=Label(taskBar, text="Vol/Rwd (~):",justify=LEFT)
    vpR.grid(row=ttRw,column=0,padx=0,sticky=W)
    volPerRwd_TV=StringVar(taskBar)
    volPerRwd_TV.set(sesVars['volPerRwd'])
    te = Entry(taskBar,width=10,textvariable=volPerRwd_TV)
    te.grid(row=ttRw,column=1,padx=0,sticky=W)
    
    # Main Buttons
    ttRw=19
    blL=Label(taskBar, text=" ——————— ",justify=LEFT)
    blL.grid(row=ttRw,column=0,padx=0,sticky=W)

    btnRw=20
    tc = Button(taskBar,text="Task: Detection",width=c1Wd,command=runDetectionTask)
    tc.grid(row=btnRw,column=0)
    tc['state'] = 'disabled'
    quitButton = Button(taskBar,text="Quit",width=c1Wd,command=closeup)
    quitButton.grid(row=btnRw+1,column=0)
    taskBar.pack(side=TOP, fill=X)

    makeBar=1

mainloop()


