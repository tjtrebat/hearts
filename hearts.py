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
        self.has_passed = False

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

    def new_game(self):
        for i in range(13):
            for player in self.players:
                player.add(self.deck.pop())
        for i, player in enumerate(self.players):
            players = self.players[i:len(self.players)] + self.players[0:i]
            player.conn.send("\n".join(["player {} {}".format(j, str(p)) for j, p in enumerate(players)]))
            self.send_player_cards(player)

    def send_player_cards(self, player):
        player.cards = sorted(player.cards)
        player.conn.send("cards {} {}".format(player.id, " ".join([str(hash(card)) for card in player.cards])))

    def get_player(self, id):
        player = None
        for p in self.players:
            if id == p.id:
                player = p
        return player
        
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
                        player = HeartsPlayer(line[1])
                        if not self.in_game:
                            if line[0] == "join":
                                if player not in self.players:
                                    player.conn = Client(line[2], int(line[3]))
                                    self.players.append(player)
                                    if len(self.players) >= self.max_players:
                                        self.new_game()
                                        self.in_game = True
                        else:
                            if line[0] == "pass":
                                player = self.players[self.players.index(player)]
                                player.has_passed = True
                                next_player = self.players[(self.players.index(player) + 1) % len(self.players)]
                                for card in player.cards:
                                    if str(hash(card)) in line[2:]:
                                        player.cards.remove(card)
                                        next_player.cards.append(card)
                                if len(list(filter(lambda p: p.has_passed, self.players))) >= self.max_players:
                                    for p in self.players:
                                        self.send_player_cards(p)
                                #next_player.conn.send("")
                            elif line[0] == "quit":
                                self.players.remove(player)
                                for p in self.players:
                                    p.conn.send("quit {}".format(player.id))
                        self.line_num += 1
                data.close()
            time.sleep(5)

if __name__ == "__main__":
    hearts = Hearts()
    server = multiprocessing.Process(target=hearts.run_server)
    server.start()