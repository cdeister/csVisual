%% open
featherPath='/dev/cu.usbmodem3099121';
featherBaud=9600;
feather=serial(featherPath,'BaudRate',featherBaud);
fopen(feather);
flushinput(feather);

%% try some variables
% all writes end with an >
% all writes start with a variable flag:
% f= temporal freq; s= spatial freq; t=trial number; o=orientaion; r=reset

fprintf(feather,'f90>');
fprintf(feather,'o90>');
fprintf(feather,'t9>');

%% reset the variables

fprintf(feather,'r1>');

%%
h=0;
for h=1:1000000
    if feather.BytesAvailable>0
        tempBuf=fscanf(feather);
        splitBuf=strsplit(tempBuf,',');
        if numel(splitBuf)==2
            disp(h)
            eval([splitBuf{1} '=' num2str(splitBuf{2}) ';'])
            disp(k)
        elseif numel(splitBuf)~=2
            disp("no")
        end
    else
    end
    
    h=h+1;
end



%% close and clean up
fclose(feather)
delete(feather)
clear all
