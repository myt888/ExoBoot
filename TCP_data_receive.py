import socket
import time

class TCPServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.start_time = None
        self.server_socket = None
        self.client_connection = None
        self.client_address = None
        self.count = 0

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(1)
        print("Waiting for a connection...")
        self.client_connection, self.client_address = self.server_socket.accept()
        print(f"Connection established with {self.client_address}")

    def process_data(self):
        try:
            buffer = ""
            while True:
                data = self.client_connection.recv(1024).decode()
                buffer += data
                lines = buffer.split("\n")
                buffer = lines.pop()

                for line in lines:
                    line = line.strip()
                    if line == "END":
                        raise StopIteration
                    elif line:
                        self.handle_line(line)
        except StopIteration:
            print("Stopping Data Processing")
        except socket.error as error:
            print(f"TCP Communication Error: {error}")
        except KeyboardInterrupt:
            print("Stopping Manually")

    def handle_line(self, line):
        if self.start_time is None:
            self.start_time = time.time()
        try:
            ankleAngleStr, controllerTorqueStr = line.split(',')
            ankleAngle = float(ankleAngleStr)
            controllerTorque = float(controllerTorqueStr)
            self.count += 1
            print(f"Received data: Ankle Angle: {ankleAngle}, Controller Torque: {controllerTorque}")
        except ValueError:
            print(f"Error processing data: {line}")

    def stop_server(self):
        if self.client_connection:
            self.client_connection.close()
        if self.server_socket:
            self.server_socket.close()
            
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            print(f"Received {self.count} lines in {elapsed_time:.3f} seconds.")
            if elapsed_time > 0:
                frequency = self.count / elapsed_time
                print(f"Receiving frequency: {frequency:.3f} Hz")
        else:
            print("No data received or time too short to calculate frequency.")


if __name__ == "__main__":
    ip = '192.168.1.1'
    port = 12345
    server = TCPServer(ip, port)
    try:
        server.start_server()
        server.process_data()
    finally:
        server.stop_server()
