import serial
import json
import time

# Configure the serial connection to the virtual COM port
port = serial.Serial('COM4', 115200)

i=0
start_time = time.time()

# while True:
#     try:
#         data_line = port.readline().decode().strip()
#         if data_line:
#             i += 1
#             data_json= json.loads(data_line)
#             if i == 250:
#                 break
#                 # i = 0
#                 # print(f"Received data: {data_json}")
#         else:
#             print("Received an empty line")
            
#     except json.JSONDecodeError:
#         print(f"Could not decode JSON: '{data_line}'")
#     except serial.SerialException as e:
#         print("Serial communication error:", str(e))
#         break
#     except KeyboardInterrupt:
#         print("Stopping")
#         port.close()

try:
    while True:
        data_line = port.readline().decode().strip()
        if data_line:
            i += 1
            try:
                data_json = json.loads(data_line)
                print(f"Received data: {data_json}")

            except json.JSONDecodeError:
                print(f"Could not decode JSON: {data_line}")

            if i == 250:
                break
        else:
            print("Received an empty line")

except serial.SerialException as e:
    print(f"Serial communication error: {e}")
except KeyboardInterrupt:
    print("Stopping manually.")

port.close()

elapsed_time = time.time() - start_time

print(f"Received {i} lines in {elapsed_time:.2f} seconds.")
if elapsed_time > 0:
    frequency = i / elapsed_time
    print(f"Receiving frequency: {frequency:.2f} Hz")
else:
    print("No data received or time too short to calculate frequency.")