data = readtable('ankle_test_right_swing_112run1.csv', 'VariableNamingRule','modify');
freq = 250;
% sample_num = height(data);
sample_num = 1000;
period = 1/freq;

% TCP Port
port = 12345;
ip = '35.3.141.14';
ip_client = tcpclient(ip, port,"Timeout", 0.1);
disp('Client is connected to server.');

% Load Data
data_str = cell(sample_num, 1);
for i = 1:sample_num
    data_str{i} = sprintf('%g,%g', data.AnkleAngle(i), data.ControllerTorque(i));
end
disp('Data Loaded');

% Send Data
tic;    % Start Timing
i = 1;
next_time = 0;
while i <= sample_num
    write(ip_client, data_str{i});

    next_time = next_time + period;
    elapsed_time = toc;
    while elapsed_time < next_time
        pause(1e-6);
        elapsed_time = toc;
    end
    i = i + 1;
end

writeline(ip_client, "END");

elapsed_time = toc; % End Timing
send_freq = sample_num/elapsed_time;
fprintf('Total transmission time: %.3f seconds\n', elapsed_time);
fprintf('Transmission frequency: %.3f Hz\n', send_freq);

clear ip_client;
disp('Client disconnected from server.');