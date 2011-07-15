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
        self.player_index = 0
        self.round = 0
        self.cards_played = 0
        self.line_num = 0
        update = multiprocessing.Process(target=self.update_server)
        update.start()

    def add_player(self, player, host, port):
        if player not in self.players:
            player.conn = Client(host, port)
            self.players.append(player)
            if len(self.players) >= self.max_players:
                self.new_game()

    def remove_player(self, player):
        self.players.remove(player)
        for p in self.players:
            p.conn.send("quit {}".format(player.id))

    def new_game(self):
        for i in range(13):
            for player in self.players:
                player.add(self.deck.pop())
        for i, player in enumerate(self.players):
            players = self.players[i:len(self.players)] + self.players[0:i]
            player.conn.send("\n".join(["player {}".format(str(p)) for p in players]))
            self.send_player_cards(player)

    def next_turn(self):
        if not self.cards_played:
            card = Card('2', 'Club')
            for i, player in enumerate(self.players):
                if card in player.cards:
                    self.player_index = i
        else:
            self.player_index = (self.player_index + 1) % len(self.players)
        player = self.players[self.player_index]
        player.conn.send("turn {}".format(player.id))

    def pass_cards(self, player, cards):
        player.has_passed = True
        player_index = self.players.index(player)
        if not self.round % 4:
            player_index = (player_index + 1) % len(self.players)
        elif self.round < 2:
            player_index -= 1
            if player_index < 0:
                player_index = len(self.players) - 1
        elif self.round < 3:
            player_index = (player_index + 2) % len(self.players)
        for card in player.cards:
            if str(hash(card)) in cards:
                player.cards.remove(card)
                self.players[player_index].cards.append(card)

    def passed_all_cards(self):
        passed = True
        for player in self.players:
            if not player.has_passed:
                passed = False
        return passed

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
                        if line[0] == "join":
                            self.add_player(player, line[2], int(line[3]))
                        elif line[0] == "pass":
                            player = self.players[self.players.index(player)]
                            self.pass_cards(player, line[2:])
                            if self.passed_all_cards():
                                for p in self.players:
                                    self.send_player_cards(p)
                                self.next_turn()
                        elif line[0] == "play":
                            for p in self.players:
                                p.conn.send(" ".join(line))
                            self.cards_played += 1
                            self.next_turn()
                        elif line[0] == "quit":
                            self.remove_player(player)
                        self.line_num += 1
                data.close()
            time.sleep(5)

if __name__ == "__main__":
    hearts = Hearts()
    server = multiprocessing.Process(target=hearts.run_server)
    server.start()