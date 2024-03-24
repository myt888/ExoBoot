traj_data_path = "I:\My Drive\Locomotor\ExoBoot\JIM_setup\ankle_test_right_swing_112run1.csv";
traj_data = readtable(traj_data_path,'VariableNamingRule','modify');

traj_data_angle = -rad2deg(traj_data.AnkleAngle);
traj_data_torque = -traj_data.CommandedTorque;
traj_data_time = traj_data.Time;

start_index = find(traj_data_time > 8, 1);  % Trim off first 8 seconds

trim_data_angle = traj_data_angle(start_index:end);
trim_data_torque = traj_data_torque(start_index:end);
trim_data_time = traj_data_time(start_index:end);
trim_data_time = trim_data_time - trim_data_time(1);    % Reset starting point

freq = 250;
period = 1/freq;

new_times = linspace(trim_data_time(1), trim_data_time(end), round((trim_data_time(end)/period)+1));
new_angles = interp1(trim_data_time, trim_data_angle, new_times);
new_torque = interp1(trim_data_time, trim_data_torque, new_times);

fc = 6;
order = 4;

[b, a] = butter(order, fc / (freq / 2), 'low');
filtered_angles = filtfilt(b, a, new_angles);
filtered_torques = filtfilt(b, a, new_torque);

figure
plot(traj_data_time(1:3000),traj_data_angle(1:3000),'LineWidth',1)


figure
plot(new_times(1:3000),new_torque(1:3000),'LineWidth',1)
hold on
plot(new_times(1:3000),filtered_torques(1:3000),'LineWidth',1)
hold off

figure
plot(new_times(1:3000),new_angles(1:3000),'LineWidth',1)
hold on
plot(new_times(1:3000),filtered_angles(1:3000),'LineWidth',1)
hold off

output_data = table(new_times', filtered_angles', filtered_torques', 'VariableNames', {'time', 'ankle_angle', 'commanded_torque'});
output_path = "I:\My Drive\Locomotor\ExoBoot\JIM_setup\traj_data_Katharine.csv";
writetable(output_data, output_path);