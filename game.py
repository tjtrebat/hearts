__author__ = 'Tom'

import random
import socketserver
import threading
from server import *
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

class MyTCPHandler(socketserver.BaseRequestHandler):

    games = []

    def handle(self):
        data = HeartsHandler.load_data(self.request.recv(1024).strip())
        print(data)
        if data[0] == "new":
            print("adding game")
            game = GameThread()
            self.games.append(game)
            game.start()
        elif data[0] == "games":
            print(self.games)
            self.request.send(bytes(" ".join(["{}:{}".format(game.host, game.port) for game in self.games]), "UTF-8"))

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()