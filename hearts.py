__author__ = 'Tom'

import sys
import socket
import asyncore
from client import *
from cards import *

class Player(Hand):
    def __init__(self, id):
        super(Player, self).__init__()
        self.id = id
        self.client = None
        self.has_passed = False
        self.trick_cards = []
        self.points = 0

class Hearts:
    def __init__(self):
        self.deck = Deck()
        self.players = []

    def add_player(self, id, host, port):
        player = Player(id)
        player.client = Client(host, port)
        self.players.append(player)

    def deal(self):
        self.deck.shuffle()
        for i in range(13):
            for player in self.players:
                player.add(self.deck.pop())
        for player in self.players:
            player.client.send("cards {}".format(" ".join(player.get_card_ids())))

class HeartsHandler(asyncore.dispatcher_with_send):
    def __init__(self, hearts, *args):
        self.hearts = hearts
        super(HeartsHandler, self).__init__(*args)

    def handle_read(self):
        try:
            data = self.recv(1024).decode("UTF-8").strip()
        except socket.error:
            sys.exit("Error reading data from client.")
        print(data)
        if data:
            data = data.split()
            if data[0] == "join":
                if len(self.hearts.players) < 4:
                    self.hearts.add_player(data[1], data[2], int(data[3]))
                    if len(self.hearts.players) >= 4:
                        self.hearts.deal()
            elif data[0] == "pass":
                pass

class HeartsServer(asyncore.dispatcher):

    hearts = Hearts()

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        asyncore.loop()

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('Incoming connection from %s' % repr(addr))
            self.handler = HeartsHandler(self.hearts, sock)

if __name__ == "__main__":
    server = HeartsServer("localhost", 9999)

"""
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

    def add_trick_cards(self, cards):
        for card in cards:
            self.trick_cards.append(card)

    #def get_trick_card_ids(self):
    #    return [str(hash(card)) for card in sorted(self.trick_cards)]

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.id

class Hearts:
    def __init__(self, host, port):
        self.players = []
        self.player_index = 0
        self.round = 0
        self.cards_played = 0
        self.suit_played = ''
        self.table_cards = {}
        self.line_num = 0
        self.addr = (host, port,)
        update = multiprocessing.Process(target=self.update_server)
        update.start()

    def add_player(self, player, host, port):
        if player not in self.players:
            player.conn = Client(host, port)
            self.players.append(player)

    def send_player_info(self):
        for i, player in enumerate(self.players):
            players = self.players[i:len(self.players)] + self.players[0:i]
            player.conn.send("\n".join(["player {}".format(str(p)) for p in players]))

    def remove_player(self, player):
        self.players.remove(player)
        for p in self.players:
            p.conn.send("quit {}".format(player.id))

    def next_round(self):
        self.round += 1
        self.cards_played = 0
        for player in self.players:
            points = 0
            for card in player.trick_cards:
                if card.suit == 'Heart':
                    points += 1
                elif Card('Queen', 'Spade') == card:
                    points += 13
            if points < 26:
                player.points += points
            else:
                for p in self.players:
                    if p != player:
                        p.points += points
        self.send_players("\n".join(["points {} {}".format(player.id, player.points) for player in self.players]))
        for player in self.players:
            player.cards = []
            player.trick_cards = []
            player.has_passed = False
        if not self.game_over():
            self.deal_cards()

    def game_over(self):
        game_over = False
        for player in self.players:
            if player.points >= 100:
                game_over = True
        return game_over
            
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
            player_index = (player_index + 3) % 4
        elif self.round % 4 < 3:
            player_index = (player_index + 2) % len(self.players)
        other_player = self.players[player_index]
        for card_id in cards:
            card = Deck().get_card(int(card_id))
            player.remove(card)
            print("Removing card from " + str(player))
            other_player.add(card)
            print("Adding card to " + str(other_player))
        other_player.cards = sorted(other_player.cards)

    def all_cards_passed(self):
        all_passed = True
        for player in self.players:
            if not player.has_passed:
                all_passed = False
        return all_passed

    def get_trick_winner(self):
        player_id = None
        highest_rank = -1
        ranks = [str(i) for i in range(2, 11)] + ['Jack', 'Queen', 'King', 'Ace']
        for key, value in self.table_cards.items():
            rank = ranks.index(value.rank)
            if value.suit == self.suit_played and rank >= highest_rank:
                player_id = key
                highest_rank = rank
        return self.get_player(player_id)

    def deal_cards(self):
        deck = Deck()
        deck.shuffle()
        for i in range(13):
            for player in self.players:
                player.add(deck.pop())
        for player in self.players:
            player.conn.send("cards {} {}".format(player.id, " ".join(player.get_card_ids())))

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
        server = HeartsServer(self.addr[0], self.addr[1], "hearts.p")

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
                            if len(self.players) >= 4:
                                self.send_player_info()
                                self.deal_cards()
                        elif line[0] == "pass":
                            player = self.players[self.players.index(player)]
                            self.pass_cards(player, line[2:5])
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
                                trick_winner = self.get_trick_winner()
                                trick_winner.add_trick_cards(self.table_cards.values())
                                self.table_cards = {}
                                self.player_index = self.players.index(trick_winner) - 1
                                if self.player_index < 0:
                                    self.player_index = len(self.players) - 1
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
    hearts = Hearts("localhost", 9999)
    server = multiprocessing.Process(target=hearts.run_server)
    server.start()
"""