import socket
import time
import pandas as pd

data = pd.read_csv('I:\\My Drive\\Locomotor\\ExoBoot\\JIM_setup\\ankle_test_right_swing_112run1.csv')

freq = 250  # Hz
sample_num = 1000
period = 1 / freq

remote_port = 12345
remote_ip = '35.3.141.14'
end_marker = 'END'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((remote_ip, remote_port))
print('TCP client is connected to the server.')

data_str = []
for i in range(sample_num):
    data_str.append(f"{data['Ankle Angle'][i]},{data['Controller Torque'][i]}")


start_time = time.time()
for i in range(sample_num):
    s.send(data_str[i].encode())
    elapsed_time = time.time() - start_time
    sleep_time = period - elapsed_time % period
    if sleep_time > 0:
        time.sleep(sleep_time)
s.send(end_marker.encode())


elapsed_time = time.time() - start_time
send_freq = sample_num / elapsed_time
print(f'Total transmission time: {elapsed_time:.3f} seconds')
print(f'Transmission frequency: {send_freq:.3f} Hz')

s.close()
print('TCP sender disconnected from the server.')