import socket
import time

port = 12345
ip = '35.3.141.14'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ip, port))
s.listen(1)

print("Waiting for a connection...")
conn, addr = s.accept()  # Accept a connection
print(f"Connection established with {addr}")

i=0
start_time = None

try:
    while True:
        data_line = conn.recv(1024).decode().strip()
        if data_line == "END":
            break
        elif data_line:
            if start_time is None:
                start_time = time.time()
            i += 1
            try:
                ankleAngleStr, controllerTorqueStr = data_line.split(',')
                ankleAngle = float(ankleAngleStr)
                controllerTorque = float(controllerTorqueStr)
                print(f"Received data: Ankle Angle: {ankleAngle}, Controller Torque: {controllerTorque}")
            except ValueError:
                print(f"Error processing data: {data_line}")
        else:
            print("Received an empty line")

except socket.error as error:
    print(f"Serial communication error: {error}")
except KeyboardInterrupt:
    print("Stopping manually.")
finally:
    conn.close()
    s.close()

if start_time is not None:
    elapsed_time = time.time() - start_time
    print(f"Received {i} lines in {elapsed_time:.3f} seconds.")
    if elapsed_time > 0:
        frequency = i / elapsed_time
        print(f"Receiving frequency: {frequency:.3f} Hz")
else:
    print("No data received or time too short to calculate frequency.")