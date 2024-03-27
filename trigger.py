import socket
import time


def wait_for_TCP_trigger(ip, port):
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

def wait_for_manual_trigger():
    input("Press Enter to start...")
    print("Starting trigger received.")