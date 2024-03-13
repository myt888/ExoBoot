clc;
clear;

data = readtable('ankle_test_right_swing_112run1.csv', 'VariableNamingRule','modify');
port = serialport('COM3',115200);
%%

for i = 1:height(data)
    % ank_ang = data.AnkleAngle(i);

    data_struct = table2struct(data(i, :));
    data_json = jsonencode(data_struct);

    writeline(port, data_json);
    pause(0.04);
end

clear port;