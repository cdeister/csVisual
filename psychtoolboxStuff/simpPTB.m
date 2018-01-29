% % ptb only, but with trigger out.
featherPath='COM16';
featherBaud=9600;
feather=serial(featherPath,'BaudRate',featherBaud);
fopen(feather);
flushinput(feather);
% 
animalID='ci00';
% Setup PTB with default values
PsychDefaultSetup(2);

% Set the screen number to the secondary monitor if there is one
screenNumber = max(Screen('Screens'));   

% Define black, white and grey
white = WhiteIndex(screenNumber);
grey = white / 2; 

Screen('Preference', 'SkipSyncTests', 2);
Screen('Preference', 'Verbosity', 0);

[window, windowRect] = PsychImaging('OpenWindow',screenNumber,...
    grey, [], 32, 2,[], [],kPsychNeed32BPCFloat);

                  
headerFired=0;
% default values
tContrast = 0;
tOrient = 0;
tSFreq=0;
tTFreq=0;

runningTask=1;

trialNum=0;
tTime=[];
logStates=[];
tCntr=0;
cScale=100;
baselineTime=10;
stimTime=5;
numStims=10;
stimLoopCntr=0;

% visual set up

% Dimension of the region of Gabor in pixels
gaborDimPix = windowRect(4) / 2;

% Sigma of Gaussian
sigma = gaborDimPix / 7;
aspectRatio = 1.0;
phase = 0;


backgroundOffset = [0.5 0.5 0.5 0.0];
disableNorm = 1;          
preContrastMultiplier = 0.5;
[gabortex gabRec] = CreateProceduralGabor(window, gaborDimPix, gaborDimPix, [],...
    backgroundOffset, disableNorm, preContrastMultiplier);


orientationList=0:30:360;
sFreqList=5:5:20;
rndSeed=1;
freq=0;

totalStims=(numel(orientationList)*2)*numel(sFreqList);
rng(rndSeed)
tOrients=orientationList(randi(numel(orientationList),totalStims,1));
tFreqs=sFreqList(randi(numel(sFreqList),totalStims,1));



stimsDone=0;    
    
% drain the buffer
while feather.BytesAvailable>0
    fscanf(feather);
end

% primary tracker is curState

curState=0;
curStim=1;

while runningTask
    
    % State Zero is Sync State
    if headerFired==0 && curState==0
        s1Header=0;
        s2Header=0;
        
        trigTime=GetSecs();
         fprintf(feather,'1c1');
        curState=1;
        headerFired=1;
        disp(['curState=0 : ' num2str(curState)])

    
    elseif curState==1
        % header
        if s1Header==0
            s2Header=0;
            s1Header=1;
            tContrast=0;
            disp(['finished stim ' num2str(curStim) ' of ' num2str(totalStims)])
            disp(['curState=1 : ' num2str(curState)])
            stateOffset=GetSecs();
            
        else
            
            stateTime=GetSecs()-stateOffset;

            
            % exit
            if stateTime>baselineTime
                curState=2;
            else
            end
        end
        
        
    elseif curState==2
        if s2Header==0
            s1Header=0;
            curStim=curStim+1;
            freq = tFreqs(curStim) / gaborDimPix;
            tContrast=1;
            tOrient=tOrients(curStim); % todo: get this as a function of stimCount
            disp(['curState: ' num2str(curState) ' tFreq: ' num2str(freq) ' orient: ' num2str(tOrient)])
            s2Header=1;
            stateOffset=GetSecs();
            
        else
            stateTime=GetSecs()-stateOffset;

            
            
            if stateTime>stimTime
                curState=1;
            else
            end
        end
    else
    end
    

            
    
    % always log loop number and time.
    tCntr=tCntr+1;
    tTime(tCntr,1)=GetSecs()-trigTime;
    logStates(tCntr,1)=curState;
    

    propertiesMat = [phase, freq, sigma, tContrast, aspectRatio, 0, 0, 0];

    % Draw the Gabor
    Screen('DrawTextures', window, gabortex, [], OffsetRect(gabRec,150,200), tOrient, [], [], [], [],...
        kPsychDontDoRotation, propertiesMat');

    % Flip to the screen
    Screen('Flip', window);

    if curStim>totalStims
        disp('fin')
        runningTask=0;
        
    else
    end

end

sca
fclose(feather)
delete(feather)

% close and clean up


 
clearvars -except tTime logStates tFreqs tOrients rndSeed curStim animalID
a=clock;
a=a*100;
fix(a(end-1:end));

save(['C:\Users\Deister\Desktop\' animalID '_' date '_' num2str(a(1)) '_' num2str(a(2)) '_psychTBOutput.mat'])
clear all


