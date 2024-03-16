clc;
clear;

data = readtable('ankle_test_right_swing_112run1.csv', 'VariableNamingRule','modify');
port = serialport('COM3',115200);
ipAddress = '35.3.141.14';
freq = 4000; % Hz
%%
tic; % Start timing

for i = 1:2500
    % ank_ang = data.AnkleAngle(i);

    % data_struct = table2struct(data(i, :));
    % data_struct = struct(...
    %     'Ankle_Angle', data.AnkleAngle(i), ...
    %     'Controller_Torque', data.ControllerTorque(i));
    % data_json = jsonencode(data_struct);
    % writeline(port, data_json);

    data_str = sprintf('%f,%f', data.AnkleAngle(i), data.ControllerTorque(i));
    writeline(port, data_str);

    pause(1/freq);
end

writeline(port, "Data_End");

elapsedTime = toc; % Measure elapsed time
fprintf('Total transmission time: %.2f seconds\n', elapsedTime);

clear port;