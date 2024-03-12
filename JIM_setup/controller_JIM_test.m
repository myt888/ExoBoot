serialPort = 'COM1';
baudRate = 115200;

% s = serialport(serialPort,  115200);

data = readtable('ankle_test_right_swing_112run1.csv');
height(data)

for i = 1:height(data)    

    pause(0.04);
end
