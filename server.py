__author__ = 'Tom'

import sys
import random
import socket
import asyncore
import threading
from hearts import *

class GameThread(threading.Thread):
    def __init__(self, player_id):
        threading.Thread.__init__(self)
        self.hearts = Hearts()
        self.addr = (socket.getfqdn(), random.randint(1000, 60000),)
        self.created_by = player_id

    def run(self):
        server = HeartsServer(self.hearts, *self.addr)

class GameServer(asyncore.dispatcher):
    def __init__(self):
        self.games = []
        self.players = {}
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
            self.handler = GameHandler(self, sock)

    def get_open_games(self, player_id):
        open_games = []
        for game in self.games:
            if len(game.hearts.players) < 4 and game.created_by != player_id:
                open_games.append("{}:{}".format(*game.addr))
        return open_games

    def add_player(self, player_id, host, port):
        client = Client(host, port)
        self.players[player_id] = client
        self.players[player_id].connect()
        self.send_games(player_id)

    def add_game(self, player_id):
        game = GameThread(player_id)
        self.games.append(game)
        game.start()
        self.players[player_id].send("new {}:{}".format(*game.addr))

    def send_games(self, player_id):
        self.players[player_id].send("games " + " ".join(self.get_open_games(player_id)))

class GameHandler(asyncore.dispatcher_with_send):
    def __init__(self, server, *args):
        self.server = server
        super(GameHandler, self).__init__(*args)

    def handle_read(self):
        try:
            data = self.recv(1024).decode("UTF-8").strip()
        except socket.error:
            sys.exit("Error reading data from client.")
        if data:
            data = data.split()
            if data[0] == "join":
                self.server.add_player(data[1], data[2], int(data[3]))
            if data[0] == "new":
                self.server.add_game(data[1])
            if data[0] == "games":
                self.server.send_games(data[1])

if __name__ == "__main__":
    server = GameServer()