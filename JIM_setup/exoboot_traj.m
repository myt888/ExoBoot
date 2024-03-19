function [pos, time] = exoboot_traj()
    padtime = 10;
    timelength = 60*5;
    timelengthfull = timelength + padtime;
    dt = .01;

    w = .2; %hz sine
    max = 18; %max PLANTAR
    min = -25; %max DORSI
    a = (max-min)/2;
    b = min+a;

    trajectory.time = linspace(0,timelengthfull,timelengthfull/dt + 1);
        
    for i = 1:numel(trajectory.time)
        trajectory.angle(i) = a*sin(2*pi*w*(trajectory.time(i)+padtime))+b;
    end

    k=1;
    while (trajectory.angle(k)<0)
        k = k+1;
    end
    phaseshift = trajectory.time(k) + (padtime/dt);
    
    pos = a*sin(2*pi*w*(trajectory.time + phaseshift))+b;
    pos(1:padtime/dt) = zeros(size(pos(1:padtime/dt)));

    time = trajectory.time;
end