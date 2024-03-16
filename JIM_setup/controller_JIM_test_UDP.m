clc;
clear;

data = readtable('ankle_test_right_swing_112run1.csv', 'VariableNamingRule','modify');
freq = 250;
sample_num = 1000;
period = 1/freq;

remote_port = 12345;
remote_ip = '35.3.141.14';
udp_sender = udpport('IPV4');

disp('UDP sender is connected to the server.');


data_str = cell(sample_num, 1);
for i = 1:sample_num
    data_str{i} = sprintf('%.3f,%.3f', data.AnkleAngle(i), data.ControllerTorque(i));
end

tic;

for i = 1:sample_num
    write(udp_sender, data_str{i}, 'string', remote_ip, remote_port);

    elapsed_time = toc;
    pause_time = period - mod(elapsed_time, period);
    if pause_time > 0
        pause(pause_time);
    end
end

end_marker = 'E';
write(udp_sender, end_marker, 'string', remote_ip, remote_port);

elapsed_time = toc;
send_freq = sample_num / elapsed_time;
fprintf('Total transmission time: %.3f seconds\n', elapsed_time);
fprintf('Transmission frequency: %.3f Hz\n', send_freq);

clear udp_sender;
disp('UDP sender disconnected from the server.');