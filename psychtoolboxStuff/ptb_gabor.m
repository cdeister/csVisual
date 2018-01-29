% TODO:
% _ Save Path
% _ Animal Tag?

% open com

featherPath='COM13';
featherBaud=9600;
feather=serial(featherPath,'BaudRate',featherBaud);
fopen(feather);
flushinput(feather);


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

                  
   
k=0;
lastK=k;    
h=0;


% default values
tContrast = 0;
tOrient = 0;
tSFreq=0;
tTFreq=0;

runningTask=1;

trialNum=0;
tTime={};
tCntr=0;
cScale=100;

% drain the buffer
while feather.BytesAvailable>0
    fscanf(feather);
end

while runningTask
    
    if feather.BytesAvailable>0 
        tempBuf=fscanf(feather);                                           
        splitBuf=strsplit(tempBuf,',');

        if strcmp(splitBuf{1},'v')
            
            lastTrial=trialNum;
            
            trialNum = str2num(splitBuf{2});
    
            orientation(trialNum) = str2num(splitBuf{3});
            tOrient=orientation(trialNum);

    
            contrast(trialNum) = str2num(splitBuf{4});
            tContrast=(contrast(trialNum)/cScale);
            
            sFreq(trialNum) = str2num(splitBuf{5});
            tSFreq=sFreq(trialNum);
     
            tempFreq(trialNum) = str2num(splitBuf{6});
            tTFreq=tempFreq(trialNum);
    
            runningTask = str2num(splitBuf{7});

            
            if trialNum-lastTrial>0
                tStart(trialNum)=GetSecs;
                tCntr=0;
            else
            end
            
            tCntr=tCntr+1;
            tTime{trialNum}(tCntr)=GetSecs-tStart(trialNum);  
        else
        end 
    else 
    end
    
    % Dimension of the region of Gabor in pixels
    gaborDimPix = windowRect(4) / 2;

    % Sigma of Gaussian
    sigma = gaborDimPix / 7;
    aspectRatio = 1.0;
    phase = 0;

    % Spatial Frequency (Cycles Per Degree)
    numCycles = tSFreq;
    freq = numCycles / gaborDimPix;

    backgroundOffset = [0.5 0.5 0.5 0.0];
    disableNorm = 1;          
    preContrastMultiplier = 0.5;
    [gabortex gabRec] = CreateProceduralGabor(window, gaborDimPix, gaborDimPix, [],...
        backgroundOffset, disableNorm, preContrastMultiplier);

    % Randomise the phase of the Gabors and make a properties matrix.
    propertiesMat = [phase, freq, sigma, tContrast, aspectRatio, 0, 0, 0];

    % Draw the Gabor
    Screen('DrawTextures', window, gabortex, [], OffsetRect(gabRec,150,200), tOrient, [], [], [], [],...
        kPsychDontDoRotation, propertiesMat');

    % Flip to the screen
    Screen('Flip', window);
    h=h+1;
%   KbStrokeWait;

end

sca
fclose(feather)
delete(feather)

% close and clean up
clearvars -except orientation contrast sFreq tempFreq tTime
save([date '_psychTBOutput.mat'])
clear all


