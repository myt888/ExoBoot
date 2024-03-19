import socket
import time
import pandas as pd

def read_data_from_file(file_path, freq):
    data = pd.read_csv(file_path)
    # num_rows = len(data)
    num_rows = 500
    period = 1 / freq
    start_time = time.time()

    for i in range(num_rows):
        ankle_angle = data['Ankle Angle'][i]
        controller_torque = data['Controller Torque'][i]
        yield ankle_angle, controller_torque
        
        elapsed_time = time.time() - start_time
        sleep_time = period - elapsed_time % period
        if sleep_time > 0:
            time.sleep(sleep_time)

    total_time = time.time() - start_time
    print(f"Total time to read all data: {total_time:.3f} seconds")
    print(f"Actual frequency: {num_rows/total_time:.3f} Hz")


def wait_for_trigger(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen(1)

    print("Waiting for the starting trigger...")
    conn, addr = sock.accept()
    print(f"Connected to Client at {addr}")

    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if data == 'START':
                print("Starting trigger received.")
                break
        except socket.error as error:
            print(f"TCP Communication Error: {error}")
        except KeyboardInterrupt:
            print("Stopping Manually")

    conn.close()
    sock.close()


ip = '192.168.1.1'
port = 12345
data_path = 'I:\\My Drive\\Locomotor\\ExoBoot\\JIM_setup\\ankle_test_right_swing_112run1.csv'
data_read_freq = 250

wait_for_trigger(ip, port)

for ankle_angle, controller_torque in read_data_from_file(data_path, data_read_freq):
    print(ankle_angle, controller_torque)