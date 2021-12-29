import socket
import time
import struct
import multiprocessing
import getch


class Client:
    def __init__(self, TEST):
        self.teamName = "DG-hac"
        self.socketClientUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socketClientUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        if TEST:
            self.socketClientUDP.bind((BRODCAST_IP_TESTING, BROADCAST_PORT))
        else:
            self.socketClientUDP.bind((BRODCAST_IP_DEV, BROADCAST_PORT))
        print("Client started, listening for offer requests...")
        self.socketClientTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.WaitForGame()

    def WaitForGame(self):
        while True:
            self.socketClientUDP.settimeout(2.5)
            try:
                data, addr = self.socketClientUDP.recvfrom(8)
                data = struct.unpack('IbH', data)
                serverPort = data[2]
                if data[0] != 0xabcddcba:
                    continue
                print(f"Received offer from {format(addr[0])}, attempting to connect...")
                self.ConnectGame(addr[0], int(serverPort))
            except:
                pass

    def ConnectGame(self, addr, gamePort):
        try:
            self.socketClientTCP.settimeout(10)
            self.socketClientTCP.connect((addr, gamePort))
            self.socketClientTCP.sendall((self.teamName + '\n').encode())
            data = None
            try:
                data = self.socketClientTCP.recv(1024)
            except:
                pass
            if data is None:
                print('No welcome message received.')
                raise Exception('unconnected to Server .')
            else:
                print(data.decode())
            self.RunGame()
            print('Server disconnected, listening for offer requests...')
        except:
            pass
        self.socketClientTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def RunGame(self):
        treads = multiprocessing.Process(target=self.getResult).decode()
        treads.start()
        treads.join(10)
        if treads.is_alive():
            treads.terminate()
        self.socketClientTCP.settimeout(2.5)
        msg = None
        try:
            msg = self.socketClientTCP.recv(1024)
        except:
            pass
        if not msg:
            print("GameOver Message.")
        else:
            print(msg)

    def getResult(self):
        stop_time = time.time() + 10
        while time.time() < stop_time:
            try:
                char = getch.getch()
                self.socketClientTCP.sendall(char.encode())
            except:
                pass

OUR_PORT = 2114
DEV = "eth1"
TESTING = "eth2"
BRODCAST_IP_DEV = "172.1.255.255"
BRODCAST_IP_TESTING = "172.99.255.255"
BROADCAST_PORT = 13117


def main():
    Client(False)

if __name__ == "__main__":
    main()
