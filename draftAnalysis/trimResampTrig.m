%%Specify animal absTime and images_registered

absTime = ci02_ccdMap_13Feb2018_003_absTime;
images_registered = frameAvg_ci02_ccdMap_13Feb2018_003_images;

%% Trim (make images and image time, just short of the behavior time).
imEnd=absTime(end);
bhEnd=bData.sessionTime(end);
imOver=find(absTime>bhEnd);
try
    imTrim=imOver(1)-1;
catch

end

% this should always be true. 
if imEnd>bhEnd
    images_registered=...
        images_registered(:,:,1:imTrim);
    absTime=absTime(1:imTrim);   
else
    disp('your behavior time is longer than image time')
    disp('you either trimmed already or your images are messed up')
end
%% trim somaticF if you have it. 
try
    somaticF=somaticF(:,1:imTrim);
    %somaticF_DF=somaticF_DF(:,1:imTrim);
catch
end

%% Resample df to behavior time.
%rsData=rsCaData(somaticF',ci05_ccdMap_001_absTime',bData.sessionTime);
rsDataDF=rsCaData(somaticF',absTime',bData.sessionTime);
% sometime rs pads with nans on the ends.
rsDataDF(find(isnan(rsDataDF)==1))=0;
%% FYI: how did we do? 
% should look identical except a VERY small error around sharp noise peaks
% you would need to zoom in a lot to see the difference, so as a sanity
% check i make the rs data red and wide so you can see them together.
figure,plot(bData.sessionTime',rsDataDF(:,1),'r-','linewidth',5)
hold all,plot(absTime,somaticF(1,:),'k-','linewidth',2)


%% Crude regression, to make the point ... 
% look at correlation of df to velocity, when velocity is high or low
normVel=bData.velocity./max(bData.velocity);
highVelInd=find(normVel>0.1);
nonVelInd=setdiff(1:numel(normVel),highVelInd);
bottomCut=min(normVel)/4;
roiCount=size(rsDataDF,2);

velCorQuick=zeros(roiCount,3);
for n=1:size(rsDataDF,2)
    roiT=n;
    dfInt=rsDataDF(:,roiT);
    dfInt(find(dfInt<bottomCut))=bottomCut;

    velCorQuick(roiT,1)=corr(rsDataDF(:,roiT),bData.velocity');
    velCorQuick(roiT,2)=corr(rsDataDF(nonVelInd,roiT),bData.velocity(nonVelInd)');
    velCorQuick(roiT,3)=corr(rsDataDF(highVelInd,roiT),bData.velocity(highVelInd)');
end
figure,plot(dfInt)
hold all,plot(normVel)

%% quick stim trigger (example).
% this can and should be vectorized for long term use ... 
clear cR
roiNum=1;
% example shows 500 ms pre and 2 sec post trigger ...
preSamps=500;
postSamps=2000;
trigTimeVect=[-500:2000];
[stimOnSamps,stimOnVect]=getStateSamps(bData.states,2,1);

trigSamps=preSamps+postSamps+1;
trigDF = vertcat(rsDataDF(:,roiNum),NaN(trigSamps,1));
stimTrigs=zeros(trigSamps,numel(bData.curContrasts));
for n=1:numel(bData.curContrasts(1:400))
    stimTrigs(:,n)=trigDF(stimOnSamps(n)-preSamps:stimOnSamps(n)+postSamps);
end

% plot it
cR=figure(roiNum);
cR.Position=[560 528 1380 420];
subplot(2,4,1)
plot(trigTimeVect,stimTrigs,'k-','linewidth',0.5)
hold all,plot([0 0],[-0.01 0.1],'b:','linewidth',2)
hold all,plot(trigTimeVect,mean(stimTrigs,2),'r-','linewidth',1)
xlim([-500,2000])
xlabel('Time (ms)');
ylabel('dF/F')
subplot(2,4,5)
boundedline(trigTimeVect,nanmean(stimTrigs,2),standardError(stimTrigs,2),'cmap',[0,0,0])
hold all,plot([0 0],[-0.01 0.1],'r:','linewidth',2)
xlim([-500,2000])
xlabel('Time (ms)');
ylabel('dF/F')
% now contrast ...

% compare extremes to middle ... 
zeroContrasts=stimTrigs(:,find(bData.curContrasts==0));
maxContrasts=stimTrigs(:,find(bData.curContrasts==1));
midContrasts=stimTrigs(:,find(bData.curContrasts<=0.6 & bData.curContrasts>=0.4));
lowContrasts=stimTrigs(:,find(bData.curContrasts<=0.3 & bData.curContrasts>=0.1));
highContrasts=stimTrigs(:,find(bData.curContrasts<=0.9 & bData.curContrasts>=0.7));

subplot(2,4,[2 3 6 7])
boundedline(trigTimeVect,nanmean(zeroContrasts,2),standardError(zeroContrasts,2),'cmap',[0,0,0])
hold all
boundedline(trigTimeVect,nanmean(maxContrasts,2),standardError(maxContrasts,2),'cmap',[1,0,0])
hold all
boundedline(trigTimeVect,nanmean(midContrasts,2),standardError(midContrasts,2),'cmap',[0.1,0,1])
hold all
boundedline(trigTimeVect,nanmean(lowContrasts,2),standardError(lowContrasts,2),'cmap',[0.1,0.8,0.2])
hold all
boundedline(trigTimeVect,nanmean(highContrasts,2),standardError(highContrasts,2),'cmap',[0,1,1])
hold all

xlabel('Time (ms)');
ylabel('dF/F')'

%% now diffs (should see some crude contrast curve!)
bls(:,1)=mean(zeroContrasts(360:400,:),2);
bls(:,2)=mean(lowContrasts(360:400,:),2);
bls(:,3)=mean(midContrasts(360:400,:),2);
bls(:,4)=mean(highContrasts(360:400,:),2);
bls(:,5)=mean(maxContrasts(360:400,:),2);

stmRs(:,1)=mean(zeroContrasts(750:790,:),2);
stmRs(:,2)=mean(lowContrasts(750:790,:),2);
stmRs(:,3)=mean(midContrasts(750:790,:),2);
stmRs(:,4)=mean(highContrasts(750:790,:),2);
stmRs(:,5)=mean(maxContrasts(750:790,:),2);

subplot(2,4,[4 8])
plot(mean(stmRs)-mean(bls),'ko-')
ylabel('baselined response')
xlabel('rel contrast')
