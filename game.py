__author__ = 'Tom'

import sys
import random
import socket
import asyncore
import threading
import multiprocessing
from hearts import *

class GameThread(threading.Thread):
    def __init__(self, game):
        threading.Thread.__init__(self)
        self.game = game

    def run(self):
        server = multiprocessing.Process(target=self.game.run_server)
        server.start()

class GameServer(asyncore.dispatcher):

    games = []

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

    @classmethod
    def get_games(cls):
        return ["{}:{}".format(*game.game.addr) for game in cls.games]

class GameHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        try:
            data = self.recv(1024).decode("UTF-8").strip()
        except socket.error:
            sys.exit("Error reading data from client.")
        print(data)
        if data == "new":
            game = GameThread(Hearts("localhost", random.randint(1000, 60000)))
            GameServer.games.append(game)
            game.start()
            self.send(bytes("{} {}".format(*game.game.addr), "UTF-8"))
        elif data == "games":
            self.send(bytes("games " + " ".join(GameServer.get_games()), "UTF-8"))

if __name__ == "__main__":
    server = GameServer()