data = readtable('ankle_test_right_swing_112run1.csv', 'VariableNamingRule','modify');
freq = 250;
sample_num = 500;
period = 1/freq;

%% TCP Port
port = 12345;
ip = '192.168.1.1';
ip_client = tcpclient(ip, port,"Timeout", 0.1);
disp('Client is connected to server.');

%% Load Data
data_str = cell(sample_num, 1);
for i = 1:sample_num
    data_str{i} = sprintf('%g,%g', data.AnkleAngle(i), data.ControllerTorque(i));
    data_str{i} = [data_str{i} newline];
end
disp('Data Loaded');

%% Send Data
tic;    % Start Timing
for i = 1:sample_num
    write(ip_client, data_str{i});

    elapsed_time = toc;
    pause_time = period - mod(elapsed_time, period);
    if pause_time > 0
        pause(pause_time);
    end
end
write(ip_client, ['END' newline]);

%% Frequency
elapsed_time = toc; % End Timing
send_freq = sample_num/elapsed_time;
fprintf('Total transmission time: %.3f seconds\n', elapsed_time);
fprintf('Transmission frequency: %.3f Hz\n', send_freq);

%% Clear Connection
clear ip_client;
disp('Client disconnected from server.');