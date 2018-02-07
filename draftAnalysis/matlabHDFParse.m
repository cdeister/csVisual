%%
[hdfName,hdfPath]=uigetfile('*','what what?');

fullHdfPath=[hdfPath hdfName];
% h5disp(fullHdfPath)
h5InfoObj=h5info(fullHdfPath);

%% parse a specific trial

trialNum=1;
groupPath=h5InfoObj.Groups.Name;
curTData=h5read(fullHdfPath,[groupPath '/t' num2str(trialNum)]);
% example to itterate on known name.
% make a string map that lines up with teensydata
dataMap={'interrupt','trialTime','stateTime'};
% then you can logically index on a string like this. 
strcmp(dataMap,'interrupt')
figure,plot(curTData(strcmp(dataMap,'interrupt'),:))

%% get a contrast & orientation for all trials

% lets find the total number of datasets 
totTrials=numel(h5InfoObj.Groups.Datasets);

for n=1:totTrials
    tData=h5read(fullHdfPath,[groupPath '/t' num2str(n)]);
    orient(:,n)=tData(11,1)*10;
    contrast(:,n)=tData(10,1)/10;
    clear tData;
end

%% sort list magic!!!!

% gives an ascending list, but you can configure order.
[~,sortCInds]=sort(contrast);
figure,plot(orient(sortCInds))


[~,sortOInds]=sort(orient);
figure,plot(orient(sortOInds));