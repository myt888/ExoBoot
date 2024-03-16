clc;
clear;

data = readtable('ankle_test_right_swing_112run1.csv', 'VariableNamingRule','modify');
freq = 250; % Hz
period = 1/freq;
sample_num = 1000;

disp('Starting timing control test...');

tic; % Start timing

i = 1;
next_time = 0;
while i <= sample_num
    data_str = sprintf('%f,%f', data.AnkleAngle(i), data.ControllerTorque(i));
    next_time = next_time + period;

    elapsed_time = toc;
    while elapsed_time < next_time
        pause(1e-6); % Wait for a very short time to reduce CPU load
        elapsed_time = toc;
    end
    i = i + 1;
end

elapsed_time = toc; % Measure total elapsed time
send_freq = sample_num/elapsed_time;
fprintf('Total execution time: %.2f seconds\n', elapsed_time);
fprintf('Achieved frequency: %.2f Hz\n', send_freq);

disp('Timing control test finished.');