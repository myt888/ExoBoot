data = readtable('ankle_test_right_swing_112run1.csv', 'VariableNamingRule','modify');
freq = 250; % Hz
sample_num = 1000;
period = 1/freq;

port = 12345;
ip = '35.3.141.14';
ip_client = tcpclient(ip, port);
disp('Client is connected to server.');

tic; % Start timing
i = 1;
next_time = 0;
while i <= sample_num
    data_str = sprintf('%f,%f', data.AnkleAngle(i), data.ControllerTorque(i));
    writeline(ip_client, data_str);

    next_time = next_time + period;
    elapsed_time = toc;

    while elapsed_time < next_time
        pause(1e-6);
        elapsed_time = toc;
    end
    i = i + 1;
end

writeline(ip_client, "Data_End");

elapsed_time = toc;
send_freq = sample_num/elapsed_time;
fprintf('Total transmission time: %.2f seconds\n', elapsed_time);
fprintf('Transmission frequency: %.2f Hz\n', send_freq);

clear ip_client;
disp('Client disconnected from server.');