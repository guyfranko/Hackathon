import operator
import socket
from threading import Thread
from time import sleep, time
import struct
from datacollect import Statistics
from scapy.all import get_if_addr
import random


TITLE = '\x1b[41m'
Player_1 = '\x1b[1;31;40m'
Player_2 = '\x1b[1;34;40m'
NUM_CHARS = '\x1b[1;30;43m'
END_COLOR = '\x1b[0m'
OUR_PORT = 2114
DEV = "eth1"
TESTING = "eth2"
BRODCAST_IP_DEV = "172.1.255.255"
BRODCAST_IP_TESTING = "172.99.255.255"

BROADCAST_PORT = 13117


class Server:
    def __init__(self, statistics):
        self.serverIp = get_if_addr(DEV)
        self.broadcastFlag = True
        self.serverPort = OUR_PORT
        self.serverSocketUdp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.serverSocketTcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocketUdp.settimeout(10)
        self.gameParticipants = []
        self.clientsSockets = []
        self.clientsSocketsDict = {}
        self.clientThreads = []
        self.gameStarted = False
        self.GameStartMsg = ""
        self.udpThread = None
        self.tcpThread = None
        self.scoreDict = {}
        self.winnerMsg = ""
        self.statistics = statistics
        self.result = 0


    def ServerInitializer(self):
        try:
            print(f'Server started, listening on IP address {self.serverIp}')
            self.udpThread = Thread(target=self.ActivateServerUdp)
            self.tcpThread = Thread(target=self.ActivateServerTcp)
            self.udpThread.start()
            self.tcpThread.start()
            self.udpThread.join()
            self.tcpThread.join()
            self.GameInitializer()
            self.CloseConnectionsWithClients()
            sleep(0.5)
            self.ResetServer()
            sleep(0.5)
        except Exception as e:
            # print(e)
            sleep(0.5)

    def ActivateServerUdp(self):
        # message = struct.pack('IbH', 0xabcddcba, 0x2, self.serverPort)
        self.serverSocketUdp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.serverSocketUdp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.serverSocketUdp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        timeStarted = time()
        while True:
            if time() > timeStarted + 10:
                print(10, "second passed.")
                self.broadcastFlag = False
                if len(self.gameParticipants) != 2:
                    self.CloseConnectionsWithClients()
                    sleep(0.5)
                    self.ResetServer()
                    self.ServerInitializer()
            message = struct.pack('IbH', 0xabcddcba, 0x2, self.serverPort)
            self.serverSocketUdp.sendto(message, (BRODCAST_IP_DEV, BROADCAST_PORT))
            sleep(1)

    def ActivateServerTcp(self):
        print(f'opened tcp on {self.serverIp} with port num {self.serverPort}')
        try:
            self.serverSocketTcp.bind((self.serverIp, self.serverPort))
            self.serverSocketUdp.settimeout(10)
        except:
            pass
        try:
            self.serverSocketTcp.listen()
        except:
            pass
        while self.broadcastFlag:
            try:
                if len(self.scoreDict) == 2:
                    self.broadcastFlag = False
                    break
                connectionSocket, addr = self.serverSocketTcp.accept()
                msg = connectionSocket.recv(1024).decode('utf-8')
                print("Player ", msg, "is connected.")
                clientName = msg
                self.scoreDict[clientName] = 20
                self.clientsSockets.append(connectionSocket)
                self.clientsSocketsDict[connectionSocket] = clientName
                self.gameParticipants.append(clientName)
                sleep(1)
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable":
                    continue
                sleep(1)

    def GameInitializer(self):
        for clientSocket in self.clientsSocketsDict:
            clientThread = Thread(target = self.NewGameForClient, args=(clientSocket, self.clientsSocketsDict[clientSocket]))
            clientThread.start()
            self.clientThreads.append(clientThread)
        for clientThread in self.clientThreads:
            clientThread.join()
        self.gameStarted = True

    def NewGameForClient(self, clientSocket, clientName):
        sleep(0.5)
        if len(self.gameParticipants) != 2:
            return
        print(f"{clientName} connected")
        msg = TITLE + "Welcome to Quick Maths." + END_COLOR + '\n'
        msg += Player_1 + "Player 1: " + END_COLOR + '\n'
        msg += Player_1 + f"{self.gameParticipants[0]}" + END_COLOR + '\n'
        msg += Player_2 + "Player 2:" + END_COLOR + '\n'
        msg += Player_2 + '==' + END_COLOR + '\n'
        msg += Player_2 + f"{self.gameParticipants[1]}" + '\n'+ END_COLOR
        msg += '\n' + TITLE + "Please answer the following question as fast as you can:" + END_COLOR
        a = random.randint(0, 10)
        b = random.randint(a, 10)
        self.result = b - a
        msg += '\n' + TITLE + f"How much is {b}-{a}?" + END_COLOR + '\n'
        msg += '\n'
        clientSocket.send(msg.encode())
        self.RunGame(clientName, clientSocket)

    def GameOverMsg(self):
        sleep(0.5)
        self.statistics.update(self.scoreDict)
        winner = min(self.scoreDict.items(), key=operator.itemgetter(1))[0]
        winner_msg = "Game over!" + '\n' + "The correct answer was 4!" + '\n' + '\n'
        if self.scoreDict[winner] == 20:
            winner_msg += TITLE + "The game over in Draw" + END_COLOR
        else:
            winner_msg += TITLE + "Congratulations to the winners:" + END_COLOR + str(winner)
        winner_msg += '\n' + self.statistics.printStatistic()
        self.winnerMsg = winner_msg

    def RunGame(self, clientName, clientSocket):
        time_started_game = time()
        while time() < time_started_game + 10:
            try:
                msg = clientSocket.recv(1024).decode('utf-8')
                if not msg:
                    continue
                if msg == str(self.result):
                    self.scoreDict[clientName] = time() - time_started_game
                else:
                    for name in self.scoreDict:
                        if name != clientName:
                            self.scoreDict[name] = time() - time_started_game
                break
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable" or \
                        "[Errno 11] Resource temporarily unavailable":
                    sleep(1)
                    continue
                else:
                    continue
                sleep(1)
        self.GameOverMsg()


    def ResetServer(self):
        self.gameStarted = False
        self.broadcastFlag = True
        self.GameStartMsg = ""
        self.gameParticipants = []
        self.scoreDict = {}
        self.result = 0
        self.clientsSockets = []
        self.clientsSocketsDict = {}
        self.clientThreads = []
        self.udpThread = None
        self.tcpThread = None
        self.winnerMsg = ""
        self.result = 0

    def CloseConnectionsWithClients(self):
        sleep(3)
        for clientSock in self.clientsSockets:
            clientSock.send(self.winnerMsg.encode())
            sleep(0.5)
            clientSock.close()

def main():
    statistics = Statistics()
    server = Server(statistics)
    while True:
        server.ServerInitializer()
        sleep(3)


if __name__ == "__main__":
    main()

class Statistics:
    def __init__(self):
        self.bestPlayer = ""
        self.worstPlayers = ""
        self.fastPlayer = ""
        self.bestScore = 20
        self.mostGamePlayer = ""
        self.all_winners = {}
        self.all_losers = {}
        self.all_players = {}

    def update(self, scores):
        winner = min(scores.items(), key=operator.itemgetter(1))[0]
        looser = max(scores.items(), key=operator.itemgetter(1))[0]
        bestScore = min(scores.items(), key=operator.itemgetter(1))[1]
        print(scores)
        print(looser)
        print(bestScore)


        if bestScore < self.bestScore:
            self.bestScore = bestScore
            self.fastPlayer = winner

        if winner not in self.all_winners:
            self.all_winners[winner] = 1
        else:
            self.all_winners[winner] += 1
        self.bestPlayer = max(self.all_winners.items(), key=operator.itemgetter(1))[0]

        if looser not in self.all_losers:
            self.all_losers[looser] = 1
        else:
            self.all_losers[looser] += 1
        self.worstPlayers = max(self.all_losers.items(), key=operator.itemgetter(1))[0]

        if winner not in self.all_players:
            self.all_players[winner] = 1
        else:
            self.all_players[winner] += 1
        if looser not in self.all_players:
            self.all_players[looser] = 1
        else:
            self.all_players[looser] += 1
        self.mostGamePlayer = max(self.all_players.items(), key=operator.itemgetter(1))[0]

    def printStatistic(self):
        msg = '\n'
        msg += "Best player ever : " + self.bestPlayer + '\n'
        msg += "Fastest player ever :" + self.fastPlayer + '\n'
        msg += "Most game player : " + self.mostGamePlayer + '\n'
        msg += "Worst player ever : " + self.worstPlayers + '\n'
        return msg