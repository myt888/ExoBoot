function [ pos, time ] = ChrisJIMtraj( trajno )
%CHRISJIMTRAJ Summary of this function goes here
%   Detailed explanation goes here
    if trajno == 0
        padtime = 10;
        timelength = 60*5;
        timelengthfull = timelength + padtime;
        dt = .01;

        w = .2; %hz sine
        max = 18; %max PLANTAR
        min = -25; %max DORSI
%         a = 50/2; %deg amp
        a = (max-min)/2;
%         b = -5; %deg offset
        b = min+a;
        trajectory.time = linspace(0,timelengthfull,timelengthfull/dt + 1);
        
        for i = 1:numel(trajectory.time)
            trajectory.angle(i) = a*sin(2*pi*w*(trajectory.time(i)+padtime))+b;
        end

        k=1;
        while (trajectory.angle(k)<0)
            k = k+1;
        end
%         phaseshift = 0;
        phaseshift = trajectory.time(k)+(padtime/dt);
        
        pos = a*sin(2*pi*w*(trajectory.time + phaseshift))+b;
        pos(1:padtime/dt) = zeros(size(pos(1:padtime/dt)));


    elseif trajno == 1
        traj_data_path = '/Users/yitengma/Library/CloudStorage/GoogleDrive-yitengma@umich.edu/My Drive/Locomotor/ExoBoot/JIM_setup/ankle_test_right_swing_112run1.csv';

        traj_data = csvread(traj_data_path,1,0);
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

        plot(traj_data_time(1:3000),traj_data_angle(1:3000),'r')
        hold on
        plot(newtimes(1:6000),pos(1:6000),'b')


    else
        trajectory.time = 0;
        trajectory.angle = 0;
        print('No Trajectory Produced')
    end

    time = trajectory.time;
end

