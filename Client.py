from socket import *
from scapy.all import *
import select
import struct
import traceback
import sys

OUR_PORT = 2114
DEV = "eth1"
TESTING = "eth2"
BRODCAST_IP_DEV = "172.1.255.255"
BRODCAST_IP_TESTING = "172.99.255.255"

BROADCAST_PORT = 13117

class Client:
    def _init_(self, name):
        self.teamName = name
        self.clientSocket = None
        self.serverSocket = None

    def start_client(self, Test):
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        print("Client started, listening for offer requests")
        if Test:
            # print(f'My IP: {get_if_addr("eth2")}')
            self.clientSocket.bind((BRODCAST_IP_TESTING, BROADCAST_PORT))
        else:
            self.clientSocket.bind((BRODCAST_IP_DEV, BROADCAST_PORT))
        while True:
            data_raw, addr = self.clientSocket.recvfrom(1024)
            try:
                # print(f'got from {addr}')
                data = struct.unpack('IbH', data_raw)
                if hex(data[0]) == "0xabcddcba" and hex(data[1]) == "0x2":
                    print(f'Received offer from {addr[0]}, attempting to connect...')
                    self.Start_client_tcp(addr[0], int(data[2]))
                    return
            except struct.error:
                pass
            except Exception as err:
                print(err)

    def wait_for_game(self):
        msg = ""
        self.serverSocket.setblocking(False)
        while len(msg) == 0:
            try:
                recive = self.serverSocket.recv(1024)
                msg = recive.decode("utf-8")
                if msg:
                    print(msg)
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable":
                    time.sleep(0)
                    continue
                time.sleep(0.3)

    def Start_client_tcp(self, server_name, server_port):
        print(f"connected to server {server_name} on port {server_port}")
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.connect((server_name, server_port))
        self.serverSocket.send(str(self.teamName).encode())
        self.wait_for_game()
        try:
            self.game_in_progress()
        except Exception as e:
            # os.system("stty -raw echo")
            traceback.print_exc()
            print("Activate client_tcp")
            time.sleep(1)
        self.close()

    def game_in_progress(self):
        message_ = ""
        while len(message_) == 0:
            try:
                message = self.serverSocket.recv(1024)
                message_ += message.decode("utf-8")
                if message_:
                    break
            except Exception as ex:
                # print("game_in_progress")
                if str(ex) == "[Errno 35] Resource temporarily unavailable":
                    time.sleep(0.01)
                    # continue
                time.sleep(0.01)
            # data, _, _ = select.select([sys.stdin, self.serverSocket], [], [], 0)
            # if sys.stdin in data:
            #     data_to_send = sys.stdin.read(1)
            #     self.serverSocket.send(data_to_send.encode())
            # elif self.serverSocket in data:
            #     messag = self.serverSocket.recv(1024)
            #     messag = message.decode("utf-8")
            data, _, _ = select.select([sys.stdin], [], [], 0)
            if data:
                data_to_send = sys.stdin.read(1)
                self.serverSocket.send(data_to_send.encode())
        os.system("stty -raw echo")
        print(message_)
        # print(messag)

    def close(self):
        print("Game Ended")
        time.sleep(1)
        self.serverSocket.close()
        self.clientSocket.close()


def main():
    while True:
        client = Client("DG-Hac")
        client.start_client(False)
        time.sleep(3)


if __name__ == "__main__":
    main()