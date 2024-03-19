%% TCP Port
port = 12345;
ip = '192.168.1.1';
ip_client = tcpclient(ip, port,"Timeout", 0.1);
disp('Client is connected to server');

%% Send Trigger
trigger = 'START';
write(ip_client, trigger);
disp('Trigger is sent to server');

%% Clear Connection
clear ip_client;
disp('Client disconnected from server.');