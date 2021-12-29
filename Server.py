import socket
import threading
import time
import random
import struct
from scapy.all import get_if_addr


class Server:
    def __init__(self, TESTING):
        if TESTING:
            self.serverIP = get_if_addr(TESTING)
            self.broadcastAddr = BRODCAST_IP_TESTING
        else:
            self.serverIP = get_if_addr(DEV)
            self.broadcastAddr = BRODCAST_IP_DEV
        self.serverPort = OUR_PORT
        self.playerNumber = 1
        self.timeToStart = 0
        self.gameStarted = False
        self.result = 0
        self.gametime = 0
        self.gameParticipants = {}
        self.dictLock = threading.Lock()
        self.serverSocketUdp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.serverSocketUdp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.serverSocketUdp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.serverSocketTcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocketTcp.bind((self.serverIP, OUR_PORT))
        self.sT = threading.Semaphore()
        print('Server started, listening on IP address {}'.format(self.serverIP))
        self.udpThread = threading.Thread(target=self.ServerInitializer, args=(self.serverIP, self.serverPort))
        self.tcpThread = threading.Thread(target=self.ActivateServerTcp)
        self.udpThread.start()
        self.tcpThread.start()
        self.udpThread.join()
        self.tcpThread.join()

    def ServerInitializer(self, host, port):
        self.timeToStart = time.time() + 10
        while time.time() < self.timeToStart:
            message = struct.pack('IbH', 0xabcddcba, 0x2, port)
            self.serverSocketUdp.sendto(message, (self.broadcastAddr, BROADCAST_PORT))
            time.sleep(1.5)
        playerOne = ''
        playerTwo = ''
        for key in self.gameParticipants:
            team = self.gameParticipants[key]
            if team['playerNumber'] == 1:
                playerOne += team['teamName']
            else:
                playerTwo += team['teamName']
        participantsNames = [name for name in self.gameParticipants.keys()]
        if len(self.gameParticipants) == 2:
            a = random.randint(0, 10)
            b = random.randint(a, 10)
            self.result = str(a - b)
            try:
                for player in self.gameParticipants:
                    try:
                        player.sendall((openningMsg % (playerOne, playerTwo, a, '-', b)).encode())
                    except:
                        self.gameParticipants.popitem(player)
            except:
                pass
            self.gameStarted = True
            winnerFlag = True
            winner = 'Draw'
            self.gametime = time.time() + 10
            while time.time() < self.gametime and winnerFlag:
                if self.gameParticipants[participantsNames[0]]['time'] == self.gameParticipants[participantsNames[1]]['time']:
                    continue
                else:
                    winnerFlag = False
                    for name in participantsNames:
                        if min(self.gameParticipants[participantsNames[0]]['time'],
                               self.gameParticipants[participantsNames[1]]['time']) == self.gameParticipants[name]['time']:
                            team_to_check = self.gameParticipants[name]
                        else:
                            team_after = self.gameParticipants[name]
                    if team_to_check['answer'] == self.result:
                        winner = team_to_check['teamName']
                    else:
                        winner = team_after['teamName']
            for player in self.gameParticipants:
                try:
                    player.sendall((closeMsg % (self.result, winner)).encode())
                    player.close()
                except:
                    pass
        else:
            print("Not enough players!")
        for i in participantsNames:
            del self.gameParticipants[i]
        self.sT.release()
        self.ServerInitializer(host, port)

    def ActivateServerTcp(self):
        threads = []
        while not self.gameStarted:
            if len(threads) > 10:
                continue
            self.serverSocketTcp.settimeout(2)
            try:
                self.serverSocketTcp.listen()
                client, addr = self.serverSocketTcp.accept()
                t = threading.Thread(target=self.getPlayers, args=(client, addr))
                threads.append(t)
                t.start()
            except:
                pass
        for thread in threads:
            thread.join()
        self.gameStarted = False
        self.sT.acquire()
        self.ActivateServerTcp()

    def getPlayers(self, player, addr):
        game = False
        try:
            player.settimeout(2)
            teamName = player.recv(1024).decode()
            self.dictLock.acquire()
            if len(self.gameParticipants) < 2:
                game = True
                self.gameParticipants[player] = {"teamName": teamName, 'playerNumber': self.playerNumber, 'answer': None, "time": 20}
                if self.playerNumber == 1:
                    self.playerNumber = 2
            self.dictLock.release()
            time.sleep(self.timeToStart - time.time())
        except:
            return
        if game:
            self.StartGame(player)

    def StartGame(self, player):
        time_started_game = time.time()
        player.settimeout(1.5)
        while time.time() < time_started_game + 10:
            try:
                num = player.recv(1024).decode()
                if num is not None and num != '' and num != '\n':
                    self.gameParticipants[player]['time'] = time.time()
                    self.gameParticipants[player]['answer'] = num
                    return
            except:
                pass


openningMsg = f'Welcome to Quick Maths.' + f'\nPlayer 1: %s\n' + f'Player 2: %s\n' + f'==\n' + f'Please answer the following question as fast as you can:\n' + 'How much is ' + '%d%s%d?'
closeMsg = f'Game over!\n' + f'The correct answer was %s!\n\n' + f'Congratulations to the winner: %s'
OUR_PORT = 2114
DEV = "eth1"
TESTING = "eth2"
BRODCAST_IP_DEV = "172.1.255.255"
BRODCAST_IP_TESTING = "172.99.255.255"
BROADCAST_PORT = 13117


def main():
    Server(False)


if __name__ == "__main__":
    main()
