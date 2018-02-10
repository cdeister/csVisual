%% Grab Behavior HDF
[hdfName,hdfPath]=uigetfile('*','what what?');
behavHDFPath=[hdfPath hdfName];
behavHDFInfo=h5info(behavHDFPath);
curDatasetPath=['/' behavHDFInfo.Datasets.Name];

curBData=h5read(behavHDFPath,curDatasetPath);
% attributes have int32 encoding and need to be converted.
curOrientations=double(h5readatt(behavHDFPath,curDatasetPath,'orientations')).*10;
curContrasts=double(h5readatt(behavHDFPath,curDatasetPath,'contrasts'))/10;

%% Now we can look for state times. 
% I wrote a function that parses a state.


%% sort list magic!!!!

% gives an ascending list, but you can configure order.
[~,sortCInds]=sort(contrast);
figure,plot(orient(sortCInds))


[~,sortOInds]=sort(orient);
figure,plot(orient(sortOInds));