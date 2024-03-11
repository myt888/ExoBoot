function [ pos, time ] = ChrisJIMtraj( trajno )
%CHRISJIMTRAJ Summary of this function goes here
%   Detailed explanation goes here
    padtime = 10;
    timelength = 60*5;
    timelengthfull = timelength + padtime;
    dt = .01;
    if trajno == 0
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
    else
        trajectory.time = 0;
        trajectory.angle = 0;
        print('No Trajectory Produced')
    end

    time = trajectory.time;
end

