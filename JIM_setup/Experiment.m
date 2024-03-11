function [ H ] = Experiment( System, LoadCellSerial )
% EXPERIMENT is the constructor for the xPC control object associated with
% the reaching experiment looking at startle reflexes.
%
%       H = Experiment( System );
%
%   SYSTEM      Specify whether this experiment is going to run on the
%               linear or rotary motor by providing the string 'Linear' or
%               'Rotary', respectively.
%						ADDED 2009-12-16 TMH: Additional system 'Rotary_ShortPert'
%						added to allow faster download of perturbations. This system
%						limits perturbation sequences to 1000 position-time pairs.
%
%	 LOADCELLSERIAL	By default, the calibration matrix used is for the loadcell
%							typically used with the system specified in SYSTEM. If you
%							are using another loadcell, provide that loadcell's serial
%							number as a string.
%			* As of 2009-03-12 the available calibration matrices are for serial
%			numbers '3698' (typically used with the rotary motor) and '2665'
%			(typically used with the linear motor).
%
%    If you want to change the signal set that will be collected, use the
%    AddScopeSignal method to add signal by their signal ID. To remove
%    existing signals use RemScopeSignal and specify the signals to remove
%    by their signal IDs. Look at the constructor output to see which
%    signals are already set. Use ListAvailableSignals to see all the
%    signals you have to chose from.
%      Exp = ListAvailableSignals(Exp);
%
%   Created: 2007/06/07  TMH

% Disable EJP Intranet NIC to avoid complications in Display and xPC
% communications
% disp('Disabling unused network card.')
% !devcon disable *"VEN_14E4"*

H.tg = xpc;
superiorto(class(H.tg));

% Set download time-out for the TCP/IP connection to 60 seconds so we don't
% get an error if it takes some time to download the model. 2011-08-04 TMH
% xpcgate('settimeout', 60);

% Check to see if the model is currently running and prompt the user to turn off
% the motor driver before we stop the model and load a new one.

if isfield(H.tg,'Status') && strcmpi(H.tg.Status, 'running')
	button = questdlg({'YOU HAVE MADE A REQUEST TO STOP xPC', '- You must power-down the "Rotary Motor Driver" box FIRST, then press Yes.', '- If you do not want to stop xPC, press No to cancel the request.'}, 'TURN OFF ROTARY MOTOR', 'Yes', 'No', 'No');
	if strcmpi(button, 'Yes')
		H.tg.stop;
	end
end

% Load the requested controller model
H.System = System;
if strcmpi(H.System, 'Linear')
	% 	H.tg.load('C:\Experiment_Software_R2011a\Simulink_Model\LinearControl');
	warnldg('The linear motor control model is not up-to-date.')
	H = [];
	return
elseif strcmpi(H.System, 'Rotary')
	H.tg.load('C:\xPC2011\Experiment_Software_R2011a\Simulink_Model\RotaryControl');
elseif strcmpi(H.System, 'Rotary_ShortPert')
	% 	H.tg.load('C:\Experiment_Software_R2011a\Simulink_Model\RotaryControl_ShortPert');
	warnldg('The shortpert rotary motor control model is not up-to-date.')
	H = [];
	return
elseif strcmpi(H.System, 'Rotary_Tracking')
	%    H.tg.load('C:\Experiment_Software_R2011a\Simulink_Model\RotaryControl_Tracking');
	warnldg('The tracking rotary motor control model is not up-to-date.')
	H = [];
	return
elseif strcmpi(H.System, 'Rotary_10V_DAQ')
	H.tg.load('C:\xPC2011\Experiment_Software_R2011a\Simulink_Model\RotaryControl_10V_DAQ');
elseif strcmpi(H.System, 'NewRotary')
    % DL Hack
    dr = 0;
    while dr ~= 5 && dr ~= 10;
        DR = (inputdlg('Enter voltage for ADC (Volts)','Input range',1,{'10'}));
        dr = str2double(DR{1});
    end
    
    if dr == 5
        H.tg.load([pwd '\NewRotaryControl']);
    elseif dr == 10
        H.tg.load([pwd '\NewRotaryControl10V']);
    else
        errordlg('Incorrect number of volts');
        H = [];
        return
    end
elseif strcmpi(H.System, 'Rotary_10V_DAQ_Moving_Target')
	H.tg.load('C:\xPC2011\Experiment_Software_R2011a\Simulink_Model\RotaryControl_10V_DAQ_Moving_Target');
elseif strcmpi(H.System, 'Rotary2')
	H.tg.load('C:\xPC2011\Experiment_Software_R2011a\Simulink_Model\RotaryControl2');
elseif strcmpi(H.System, 'Slow_Mover')
    H.tg.load('C:\xPC2011\Experiment_Software_R2011a\Simulink_Model\RotaryControl_SlowMover');
else
	error('Not a valid system setting.');
end

% Set download time-out for the TCP/IP connection to 10 seconds now that the
% model has been downloaded. 2011-10-31 TMH
% xpcgate('settimeout', 1);

% Create xPC target FTP and file system objects
H.ftp = xpctarget.ftp;
superiorto(class(H.ftp));
H.fsys = xpctarget.fs;
superiorto(class(H.fsys));

H.ConsecTCPIPErrorLimit = 10;

% Look up all the parameter and signal IDs that we need for the Experiment
% object to interact with the xPC target model
H = CaptureSigParamIDs(H);

H.Scopes.Data.TrigScope = [];

H = class(H, 'Experiment');

if nargin > 1
	IC; % load the model settings files to gain access to loadcell calibration matrices
	switch LoadCellSerial
		case '3698'
			H.Hardware.CalMatrix = xPCSetParam(H, H.Hardware.CalMatrix, CalMatrix_R);
		case '2665'
			H.Hardware.CalMatrix = xPCSetParam(H, H.Hardware.CalMatrix, CalMatrix);
	end
end

H = ConfigScopes( H, 2, 0, 0.0004,  H.Flags.Timing(1));
H = RemScopeSignal(H);
H = AddScopeSignal(H, [H.ScopeSigs.Analog(1:17) H.ScopeSigs.Command H.ScopeSigs.Audio]);

% Start xPC. Occasionally, xPC stops after the first sample due to slow
% initialization of some hardware components and displays a "CPU Overload
% Error". The while loop provides for several re-tries, but times out if
% we cannot successfully start after 10 seconds.
tic
SuccessFlag = true;
while ~strcmp(H.tg.Status, 'running')
	H.tg.start;
	pause(0.1)
	if toc > 10
		SuccessFlag = false;
		break
	end
end

if SuccessFlag
	button = questdlg({'CHECK THAT xPC IS RUNNING', '- RUNNING: power-up the "Rotary Motor Driver" box, then press Yes.', '- NOT RUNNING: press No to exit.'}, '*** IS xPC RUNNING? ***', 'Yes', 'No', 'No');
	if strcmpi(button, 'No')
		SuccessFlag = false;
	end
end

if SuccessFlag
	H = IndexLimits(H);
else
	warnldg('The xPC Target code could not be started successfully. Check for error messages on the xPC Target screen.');
	H = [];
end
