
%% look for state starts.
% make a copy of the teensy state vector.
tg=bData(5,:);
% null all but the state you want (1).
tg(tg~=1)=0;
% take the diff with the null accounted for.
tgD=diff(tg);


% for state 1, the session starts at 1. So, we have to add 1.
strts1=find(tgD>0.8);
strts1=horzcat(1,strts1);
strts1(end)=[];

%% look for state starts.
% make a copy of the teensy state vector.
tg=bData(5,:);
% null all but the state you want (1).
tg(tg~=2)=0;
% take the diff with the null accounted for.
tgD=diff(tg);


% for state 1, the session starts at 1. So, we have to add 1.
strts2=find(tgD>0.8);

%% make the image clock

imageClock=iAbTimes;
imageClockUS=interp(iAbTimes,50);
tDf=somaticF_DF(1,:);
tDfUS=interp(tDf,50);
behaviorClock=bData(2,:)/1000;

%%
clear stSamps
for j=1:size(somaticF_DF,1)
tDf=somaticF_DF(j,:);
tDfUS=interp(tDf,50);

contrasts=bData(10,strts2)/10;
filtStrts=strts2(find(contrasts>=0.0));
% filtStrts=strts2;
for n=1:numel(filtStrts)
    stSamps(:,n,j)=tDfUS(filtStrts(n)-250:filtStrts(n)+5000);
end
end

%%
stSampsMean=zscore(squeeze(mean(stSamps,2)));

%%

bls=mean(stSampsMean(40:240,:));
stmsA=mean(stSampsMean(1100:1300,:));
stmsB=mean(stSampsMean(1683:1713,:));
%%
figure,plot(stmsA-bls)
hold all,plot(stmsB-bls)
%%
figure(98)
hold all,plot(zscore(mean(stSamps,2)))