%% Notes
%changed pause in ankleTest.m from 3 seconds to 30 for Kevin's test
%%
disp('RUN SECTION BY SECTION')
break
% This file contains the steps necessary to setup the JIM for prosthesis characterization.

%% 1. Navigate to proper directory
% C:\xPC2011\Experiment_Software_R2011a\Ankle_Characterization

%% 2. Initialize rotary experiment
H = Experiment('Rotary'); 
% Wait for pop-up and click yes if applicable.

%% 3. Index motor
% Move up/down so both limit switches light up

%% 4. Check xPC status
% Check torque command low
% Check bottom box for GOOD on all properties
    
%% 5. Transform matrix
[FMout J] = FChangeFrame(zeros(1,6),[0 0.2032 0 0 0 0]); XformMatrix = J'; H=SetLoadcellTransformation(H,XformMatrix);

%% 6. Motor on
H = EnableMotorController(H,1); 
% H = EnableAdmittanceControl(H, 0);
%% 7. Reset zero angle (angle must be in radians)
% H = SetZeroPosition(H, deg2rad(0.4));

H = SetZeroPosition(H, deg2rad(-.1)); %Chris ExoBoot: jog until flair contact
H = SetZeroPosition(H, deg2rad(27.71)); %Chris ExoBoot: go to true neutral
% H = SetZeroPosition(H, deg2rad(18)); %Chris ExoBoot: CHECK max plantar

 
%% 8. Zero loadcell
H = ZeroSignals(H,'Loadcell'); 
  
%% 9. Configure Scopes
disp('******MAKE SURE TIME MATCHES TOTAL TIME OF ANKLETEST******')



%% 10. Run test (Nikko)
% %RoM = 7.5; %Degrees
% total_time = 15; % Set desired trial length (seconds)
% time = [0,0.25,0.75,1]*total_time;
% % total_time = 20; % Set desired trial length (seconds)
% % time = [0,0.25,0.75,1]*total_time;
% H = ConfigScopes(H,total_time,0,0.001,1,1); % Fs = 1 kHz
% 
% % position = [0, -10, 10, 0];
% % position = [0, -12, 12, 0];
% % position = [0, -15, 15, 0];
% position = [0, -10, 15, 0];
% %position = [0, -20, 20, 0]; %no need to go past 20 degrees in either direction
% 
% output = ankleTest(H, time,  position); 


%% 10. Run test (Kevin)
% clear position
% clear time
% clear output
% [position, time] = calcJimPositions_Try3(0);
% trialNames = fieldnames(position); 
% numTrials = length(trialNames);
% for ix = 1:numTrials
%     curTrial = trialNames{ix}; 
%     curTime = time.(curTrial); 
%     curPosition = position.(curTrial); 
%     total_time = max(curTime); % Set desired trial length 
%     H = ConfigScopes(H,total_time,0,0.001,1,1); % Fs = 1 kHz
%     disp(['Starting part ', num2str(ix),' of ', num2str(numTrials),': ',curTrial])
%     beep
%     output.(curTrial) = ankleTest(H, curTime, curPosition);
% end
% path2save = 'C:\Users\Max\Desktop\Kevin\20230713\Uncompensated';
% uisave('output',path2save);
 
%% 10. Run test (Chris)
%RoM = 7.5; %Degrees
clear position
clear time
clear output
[position, time] = ChrisJIMtraj(0);
% position_zeropad = zeros(size(position)); 
dt = time(2)-time(1);

position = position(1:20000); %max JIM input vector length
time = time(1:20000); %max JIM input vector length

total_time = max(time); % Set desired trial length 
H = ConfigScopes(H,total_time,0,dt,1,1); % Fs = 1 kHz
output = ankleTest(H, time, position);
path2save = 'C:\Users\Max\Desktop\Chris\20230802\CAL_long_slowsinewithpad005';
uisave('output',path2save);
  

%% 11. Save and Plot Stuff
t = output(:,1);
angle = output(:,2);
torque = -output(:,3);
angle_N = angle; 
torque_N = torque;



t1 = 1/4*(1000*total_time-2000);
t2 = 3/4*(1000*total_time-2000);

NameOfField = input('stiffness','s')
cam_blue_1_22_dry.(NameOfField).timeJIM = t;
cam_blue_1_22_dry.(NameOfField).angleJIM = angle;
cam_blue_1_22_dry.(NameOfField).torque = torque;
% save('tester1','DESR')figure(1); hold on

 
figure(5); hold on
n = length(output(:,1));
plot(angle(1:t1)*180/pi,torque(1:t1),'g')%g
plot(angle(t1:t2)*180/pi,torque(t1:t2),'k')%k
plot(angle(t2:end)*180/pi,torque(t2:end),'r')%r

% figure(6); hold on
% plot(t,torque,'c')%r