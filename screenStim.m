function varargout = screenStim(varargin)
% SCREENSTIM MATLAB code for screenStim.fig
%      SCREENSTIM, by itself, creates a new SCREENSTIM or raises the existing
%      singleton*.
%
%      H = SCREENSTIM returns the handle to a new SCREENSTIM or the handle to
%      the existing singleton*.
%
%      SCREENSTIM('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in SCREENSTIM.M with the given input arguments.
%
%      SCREENSTIM('Property','Value',...) creates a new SCREENSTIM or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before screenStim_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to screenStim_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help screenStim

% Last Modified by GUIDE v2.5 15-Mar-2018 06:51:29

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @screenStim_OpeningFcn, ...
                   'gui_OutputFcn',  @screenStim_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before screenStim is made visible.
function screenStim_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to screenStim (see VARARGIN)

cSc=Screen('Screens');
for n=1:numel(cSc)
    gh{n}=num2str(cSc(n));
end
set(handles.screenSelector,'String',gh);

% Choose default command line output for screenStim
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes screenStim wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = screenStim_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


function useSerial_Callback(hObject, eventdata, handles)
assignin('base','useSerial',get(handles.useSerial,'Value'));
evalin('base','prefs.useSerial=useSerial;,clear useSerial')


function screenSelector_Callback(hObject, eventdata, handles)
cScSt=get(handles.screenSelector,'String');
cScVl=get(handles.screenSelector,'Value');
assignin('base','scrID',str2num(cScSt{cScVl}));
evalin('base','prefs.scrID=scrID;,clear scrID')



function screenSelector_CreateFcn(hObject, eventdata, handles)

    % Hint: popupmenu controls usually have a white background on Windows.
    %       See ISPC and COMPUTER.
    if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
        set(hObject,'BackgroundColor','white');
    end


function startScreen_Callback(hObject, eventdata, handles)


function timeToDisplay_Callback(hObject, eventdata, handles)


function timeToDisplay_CreateFcn(hObject, eventdata, handles)

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
