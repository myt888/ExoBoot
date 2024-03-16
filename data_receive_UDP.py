import socket
import time

port = 12345
ip = '35.3.141.14'

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((ip, port))

print("Waiting to receive data...")

i = 0
start_time = None

try:
    while True:
        data_str, addr = s.recvfrom(1024)
        data_str = data_str.decode()
        if data_str:
            if data_str == 'E':
                break

            try:
                ankle_angle, controller_torque = map(float, data_str.split(','))
                if start_time is None:
                    start_time = time.time()
                i += 1
                print(f"Received data: Ankle Angle: {ankle_angle}, Controller Torque: {controller_torque}")
            except ValueError:
                print(f"Error processing data: {data_str}")
        else:
            print("Received an empty packet")

except KeyboardInterrupt:
    print("Stopping manually.")
finally:
    s.close()

if start_time is not None:
    elapsed_time = time.time() - start_time
    print(f"Received {i} packets in {elapsed_time:.3f} seconds.")
    if elapsed_time > 0:
        frequency = i / elapsed_time
        print(f"Receiving frequency: {frequency:.3f} Hz")
else:
    print("No data received or time too short to calculate frequency.")