__author__ = 'Tom'

import time
import multiprocessing
from client import *
from server import *
from cards import *

class HeartsPlayer(Hand):
    def __init__(self, id, conn=None):
        super(HeartsPlayer, self).__init__()
        self.id = id
        self.conn = conn

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.id

class Hearts:
    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.players = []
        self.max_players = 4
        self.in_game = False
        self.player_turn = 0
        self.line_num = 0
        update = multiprocessing.Process(target=self.update_server)
        update.start()

    def run_server(self):
        server = HeartsServer("localhost", 50007, "hearts.p")

    def update_server(self):
        while True:
            try:
                data = open("hearts.p", "rb")
            except (IOError, EOFError):
                pass
            else:
                for line in data.readlines()[self.line_num:]:
                    line = HeartsHandler.load_data(line)
                    if len(line):
                        if not self.in_game:
                            player = HeartsPlayer(line[1])
                            if line[0] == "join":
                                if player not in self.players:
                                    player.conn = Client(line[2], int(line[3]))
                                    self.players.append(player)
                                    if len(self.players) >= self.max_players:
                                        self.new_game()
                                        self.in_game = True
                            elif line[0] == "quit":
                                if player in self.players:
                                    self.players.remove(player)
                        self.line_num += 1
                data.close()
            time.sleep(5)

    def new_game(self):
        for i in range(13):
            for player in self.players:
                player.add(self.deck.pop())
        for i in range(len(self.players)):
            players = self.players[i:len(self.players)] + self.players[0:i]
            for position, player in enumerate(players):
                self.players[i].conn.send("player {} {}\n".format(position, str(player)))
            players[0].conn.send("cards {} {}\n".format(players[0].id,
                                                        " ".join([str(hash(card)) for card in players[0].cards])))

if __name__ == "__main__":
    hearts = Hearts()
    server = multiprocessing.Process(target=hearts.run_server)
    server.start()