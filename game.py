__author__ = 'Tom'

import sys
import random
import socket
import asyncore
import threading
import multiprocessing
from hearts import *

class GameThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = "localhost"
        self.port = random.randint(1000, 60000)

    def run(self):
        hearts = Hearts()
        server = multiprocessing.Process(target=hearts.run_server)
        server.start()

class GameHandler(asyncore.dispatcher_with_send):

    games = []

    def handle_read(self):
        try:
            data = self.recv(1024).decode("UTF-8").strip()
        except socket.error:
            sys.exit("Error reading data from client.")
        if data == "new":
            game = GameThread()
            self.games.append(game)
            game.start()
            print("new game")
        elif data == "games":
            self.send(bytes("games" + " ".join(["{}:{}".format(game.host, game.port) for game in self.games]), "UTF-8"))

    @classmethod
    def load_data(cls, line):
        line = line.decode("UTF-8")
        return line.split()

class GameServer(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(("localhost", 9999))
        self.listen(5)
        asyncore.loop()

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('Incoming connection from %s' % repr(addr))
            self.handler = GameHandler(sock)

if __name__ == "__main__":
    server = GameServer()