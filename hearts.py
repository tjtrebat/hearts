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
        self.trick_cards = []
        self.points = 0

    def get_trick_card_ids(self):
        return [str(hash(card)) for card in sorted(self.trick_cards)]

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.id

class Hearts:
    def __init__(self):
        self.deck = None
        self.players = []
        self.max_players = 4
        self.player_index = 0
        self.round = 0
        self.cards_played = 0
        self.suit_played = ''
        self.table_cards = {}
        self.winner = None
        self.line_num = 0
        update = multiprocessing.Process(target=self.update_server)
        update.start()

    def add_player(self, player, host, port):
        if player not in self.players:
            player.conn = Client(host, port)
            self.players.append(player)
            if len(self.players) >= self.max_players:
                self.deal_cards()
                for i, player in enumerate(self.players):
                    players = self.players[i:len(self.players)] + self.players[0:i]
                    player.conn.send("\n".join(["player {}".format(str(p)) for p in players]))
                    player.conn.send("cards {} {}".format(player.id, " ".join(player.get_card_ids())))

    def remove_player(self, player):
        self.players.remove(player)
        for p in self.players:
            p.conn.send("quit {}".format(player.id))

    def next_round(self):
        self.round += 1
        self.cards_played = 0
        self.send_players("\n".join(["points {} {}".format(player.id, player.points) for player in self.players]))
        #self.send_players("round {} {}".format(self.winner.id, " ".join(self.winner.get_trick_card_ids())))
        for player in self.players:
            player.cards = []
            player.trick_cards = []
            player.has_passed = False
            player.conn.send("cards {} {}".format(player.id, " ".join(player.get_card_ids())))

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
        if not self.round:
            player_index = (player_index + 1) % len(self.players)
        elif self.round % 4 < 2:
            player_index -= 1
            if player_index < 0:
                player_index = len(self.players) - 1
        elif self.round % 4 < 3:
            player_index = (player_index + 2) % len(self.players)
        other_player = self.players[player_index]
        for card in player.cards:
            if str(hash(card)) in cards:
                player.remove(card)
                other_player.add(card)
        other_player.cards = sorted(other_player.cards)

    def all_cards_passed(self):
        all_passed = True
        for player in self.players:
            if not player.has_passed:
                all_passed = False
        return all_passed

    def take_trick(self):
        player_id = None
        highest_rank = 0
        points = 0
        ranks = [str(i) for i in range(2, 11)] + ['Jack', 'Queen', 'King', 'Ace']
        for key, value in self.table_cards.items():
            rank = ranks.index(value.rank)
            if value.suit == self.suit_played and rank >= highest_rank:
                player_id = key
                highest_rank = rank
            if value.suit == 'Heart':
                points += 1
            elif value.suit == 'Spade' and value.rank == 'Queen':
                points += 13
        self.winner = self.get_player(player_id)
        self.winner.points += points
        for card in self.table_cards.values():
            self.winner.trick_cards.append(card)
        self.player_index = self.players.index(self.winner) - 1
        if self.player_index < 0:
            self.player_index = len(self.players) - 1
        self.table_cards = {}

    def deal_cards(self):
        self.deck = Deck()
        self.deck.shuffle()
        for i in range(13):
            for player in self.players:
                player.add(self.deck.pop())

    def send_players(self, data):
        for player in self.players:
            player.conn.send(data)

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
                            if self.all_cards_passed():
                                for p in self.players:
                                    p.conn.send("cards {} {}".format(p.id, " ".join(p.get_card_ids())))
                                self.next_turn()
                        elif line[0] == "play":
                            card = Deck().get_card(int(line[2]))
                            self.table_cards[line[1]] = card
                            self.send_players(" ".join(line))
                            self.cards_played += 1
                            if not self.cards_played % 4:
                                self.take_trick()
                                if self.cards_played >= 52:
                                    self.next_round()
                            elif self.cards_played % 4 <= 1:
                                self.suit_played = card.suit
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