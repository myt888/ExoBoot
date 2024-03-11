function output = ankleTest(H,time,position)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here

% Zero loadcell
% H = ZeroSignals(H,'Loadcell');
% pause(2);

% Configure perturbation
H = SetPositionPerturbation(H, time, position*pi/180);
H = SetDelayedTrigs4Perts(H,1,0,0); % Position perturbation

% Run perturbation
H = ArmTrial(H);
H = ManualTrialTrigger(H);
pause(max(time));
H = DisarmTrial(H);

pause(30);
for i = 1:10
    data = Retrieve(H);
    if isempty(data)
        disp('huheh it failed but Max is clever (thanks Eric)')
        pause(10)
    else
        break
    end
end


% hold all;
% plot(data.data(:,7)*180/pi,-1*data.data(:,6))

output = [data.time data.data(:,7) data.data(:,6)]; % Time (s), Angle (rad), Torque (Nm)

end

