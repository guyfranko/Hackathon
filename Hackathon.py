import operator
import socket
from threading import Thread
from time import sleep, time
import struct
from Constants import Colors
from datacollect import Statistics


class Server:
    def __init__(self, statistics, flag=True):
        interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
        ip = [ip[-1][0] for ip in interfaces][1]
        self.serverIp = ip
        self.broadcastFlag = flag
        self.serverPort = 2110
        self.serverSocketUdp = None
        self.serverSocketTcp = None
        self.gameParticipants = ['Test']
        # self.participantsDict = {}
        self.clientsSockets = []
        self.clientsSocketsDict = {}
        self.clientThreads = []
        self.gameStarted = False
        self.GameStartMsg = ""
        self.udpThread = None
        self.tcpThread = None
        self.scoreDict = {'Test': 20}
        self.winnerMsg = ""
        self.statistics = statistics

    def ServerInitializer(self):
        try:
            print(f'Server started, listening on IP address {self.serverIp}')
            self.serverSocketUdp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.serverSocketTcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        except Exception as e:
            print(e)
            sleep(1)
            self.serverSocketUdp.close()

    def ActivateServerUdp(self):
        self.serverSocketUdp.settimeout(10)
        message = struct.pack('Ibh', 0xabcddcba, 0x2, self.serverPort)
        timeStarted = time()
        while True:
            if time() > timeStarted + 10:
                print(10, "second passed")
                self.broadcastFlag = False
                return
            self.serverSocketUdp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.serverSocketUdp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.serverSocketUdp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.serverSocketUdp.bind((self.serverIp, 50005))
            self.serverSocketUdp.sendto(message, ("255.255.255.255", 13117))
            self.serverSocketUdp.close()
            sleep(1)

    def ActivateServerTcp(self):
        print(f'opened tcp on {self.serverIp} with port num {self.serverPort}')
        self.serverSocketTcp.bind(('', self.serverPort))
        self.serverSocketTcp.listen(1)
        self.serverSocketTcp.setblocking(False)
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
                self.clientsSocketsDict[clientName] = connectionSocket
                self.gameParticipants.append(clientName)
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable":
                    print("testing")
                    continue
                sleep(1)

    def GameInitializer(self):
        for clientSocket in self.clientsSocketsDict:
            # self.participantsDict[clientSocket] = 0
            client_thread: Thread = Thread(target=self.NewGameForClient,
                                   args=(self.clientsSocketsDict[clientSocket], clientSocket))
            client_thread.start()
            self.clientThreads.append(client_thread)
        for clientThread in self.clientThreads:
            clientThread.join()
        self.gameStarted = True

    def NewGameForClient(self, clientSocket, clientName):
        """
        Sends welcome message to a client and starts the game for the client.
        :param clientSocket: The Client socket
        :param clientName: The Client name
        :return: None
        """
        print("connected")
        msg = Colors.TITLE + "Welcome to Quick Maths." + Colors.END_COLOR + '\n'
        msg += Colors.Player_1 + "Player 1: " + Colors.END_COLOR + '\n'
        msg += "".join(
            [Colors.Player_1 + str(group_name) + Colors.END_COLOR for group_name in self.gameParticipants]) + '\n'
        msg += Colors.Player_2 + "Player 2:" + Colors.END_COLOR + '\n'
        msg += Colors.Player_2 + '==' + Colors.END_COLOR + '\n'
        msg += Colors.Player_2 + "".join(
            [str(group_name) for group_name in self.gameParticipants]) + Colors.END_COLOR
        msg += '\n' + Colors.TITLE + "Please answer the following question as fast as you can:" + Colors.END_COLOR
        msg += '\n' + Colors.TITLE + "How much is 2+2?" + Colors.END_COLOR + '\n'
        msg += '\n'
        clientSocket.send(msg.encode())
        self.RunGame(clientName, clientSocket)

    def GameOverMsg(self):
        """
        Initiate and setting winner message
        :return: None
        """
        self.statistics.update(self.scoreDict)
        winner = min(self.scoreDict.items(), key=operator.itemgetter(1))[0]
        winner_msg = "Game over!" + '\n' + "The correct answer was 4!" + '\n' + '\n'
        if self.scoreDict[winner] == 20:
            winner_msg += Colors.TITLE + "The game over in Draw" + Colors.END_COLOR
        else:
            winner_msg += Colors.TITLE + "Congratulations to the winners:" + Colors.END_COLOR + str(winner)
        winner_msg += '\n' + self.statistics.printStatistic()
        self.winnerMsg = winner_msg

    def RunGame(self, clientName, clientSocket):
        """
        Getting answers from clients
        :param clientSocket: 
        :param clientName: 
        :return:
        """
        clientSocket.setblocking(0)
        time_started_game = time()
        while time() < time_started_game + 10:
            try:
                msg = clientSocket.recv(1024).decode('utf-8')
                if msg == str(4):
                    self.scoreDict[clientName] = time() - time_started_game
                else:
                    for name in self.scoreDict:
                        if name != clientName:
                            self.scoreDict[name] = time() - time_started_game
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable" or \
                        "[Errno 11] Resource temporarily unavailable":
                    sleep(0.5)
                    continue
                else:
                    print(ex)
                sleep(0.5)
        self.GameOverMsg()


    def ResetServer(self):
        """
        Resetting the game
        :return: None
        """
        self.gameStarted = False
        self.broadcastFlag = True
        self.GameStartMsg = ""

    def CloseConnectionsWithClients(self):
        """
        Sends winning message to all players and close their sockets.
        :return: None
        """
        for clientSock in self.clientsSockets:
            clientSock.send(self.winnerMsg.encode())
            clientSock.close()

def main():
    """
    Main function, initialize server and starting games
    :return:
    """
    statistics = Statistics()
    while True:
        server = Server(statistics)
        server.ServerInitializer()
        sleep(3)


if __name__ == "__main__":
    main()
# a = {'Test': 20, 'DG-Hac': 4.639542579650879}
# winner = min(a.items(), key=operator.itemgetter(1))[0]
# print(winner)
    # sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_address = ('10.100.102.7', 13117)
    # sockTCP.bind(server_address)
    # msg = b'Server started, listening on IP address 10.100.102.7'
    # while True:
    #     print(f'sending on {ip}')
    #     sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #     sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #     sockUDP.bind((ip, 13117))
    #     sockUDP.sendto(msg, ("255.255.255.255", 5005))
    #     try:
    #         sockTCP.listen(1)
    #         sockTCP.settimeout(5)
    #         conn, addr = sockTCP.accept()
    #         print(sys.stderr, 'connection from', addr)
    #         sockUDP.close()
    #         break
    #     except:
    #         continue
    # with conn:
    #     while True:
    #         equ = b'2 + 2 = ?'
    #         conn.sendall(equ)
    #         while True:
    #             data = conn.recv(4).decode('utf-8')
    #             if len(data) > 0:
    #                 print(data)
    #                 break
    #         if data == str(4):
    #             msg = b'True'
    #             conn.sendall(msg)
    #             sleep(1)
    #         else:
    #             msg = b'False'
    #             conn.sendall(msg)
    #             sleep(1)

#
# main()
# interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
# ip = [ip[-1][0] for ip in interfaces][1]
# print(ip)
# try:
#     print(get_if_addr('eth1'))
# except:
#     print('1')
# try:
#     print(get_if_addr('eth2'))
# except:
#     print('2')
