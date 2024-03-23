traj_data_path = "I:\My Drive\Locomotor\ExoBoot\JIM_setup\ankle_test_right_swing_112run1.csv";

traj_data = readtable(traj_data_path,1,0);
traj_data_angle = -rad2deg(traj_data(:,7));
traj_data_time = traj_data(:,1);
traj_data_time = traj_data_time - traj_data_time(1);

freq = 250;
period = 1/freq;

newtimes = linspace(traj_data_time(1), traj_data_time(end), round((traj_data_time(end)/period)+1));
newangles = interp1(traj_data_time, traj_data_angle, newtimes, 'spline');

fc = 6;
order = 5;
[b, a] = butter(order, fc / (freq / 2), 'low');
filtered_angles = filtfilt(b, a, newangles);

pos = filtered_angles;
trajectory.time = newtimes;