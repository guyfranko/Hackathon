import socket
import multiprocessing
import time
import getch
import struct


class Client:
    def _init_(self, TESTING):
        self.socketClientUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socketClientUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        if TESTING:
            self.socketClientUDP.bind((BRODCAST_IP_TESTING, BROADCAST_PORT))
        else:
            self.socketClientUDP.bind((BRODCAST_IP_DEV, BROADCAST_PORT))
        self.teamName = "DG-hac"
        print("Client started listening for offer requests")
        self.socketClientTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.WaitForGame()

    def WaitForGame(self):
        while True:
            self.socketClientUDP.settimeout(2.5)
            try:
                data, addr = self.socketClientUDP.recvfrom(8)
                data = struct.unpack('IbH', data)
                if data[0] != 0xabcddcba:
                    continue
                print(f"Received offer from {format(addr[0])}, attempting to connect")
                self.ConnectGame(addr[0], int(data[2]))
            except:
                pass

    def ConnectGame(self, addr, port):
        try:
            self.socketClientTCP.settimeout(10)
            self.socketClientTCP.connect((addr, port))
            self.socketClientTCP.sendall((self.teamName + '\n').encode())
            data = None
            try:
                data = self.socketClientTCP.recv(1024)
            except:
                pass
            if data is None:
                print('No welcome message received')
                raise Exception('unable to connect Server')
            else:
                print(data.decode())
            self.RunGame()
            print('Server disconnected, listening for offer requests')
        except:
            pass
        self.socketClientTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def RunGame(self):
        playerAnswer = multiprocessing.Process(target=self.getResult)
        playerAnswer.start()
        playerAnswer.join(10)
        if playerAnswer.is_alive():
            playerAnswer.terminate()
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
        startTime = time.time()
        while time.time() < startTime + 10:
            try:
                ans = getch.getch()
                self.socketClientTCP.sendall(ans.encode())
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
