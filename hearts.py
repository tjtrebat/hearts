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
        self.table_card = None
        self.points = 0

class Hearts:
    def __init__(self):
        self.deck = None
        self.players = []
        self.round = 0
        self.cards_played = 0
        self.player_index = 0

    def add_player(self, player_id, host, port):
        if len(self.players) < 4:
            player = Player(player_id)
            player.client = Client(host, port)
            self.players.append(player)
            if len(self.players) >= 4:
                self.deal()
                for player in self.players:
                    player.client.send_data({'cards': player.cards})

    def deal(self):
        self.deck = Deck()
        self.deck.shuffle()
        for i in range(13):
            for player in self.players:
                player.add(self.deck.pop())
        # sort player cards
        for player in self.players:
            player.cards = sorted(player.cards)

    def pass_cards(self, player_id, cards):
        player = self.get_player(player_id)
        player.has_passed = True
        player_index = self.players.index(player)
        if not self.round % 4:
            player_index = (player_index + 1) % len(self.players)
        elif self.round % 4 < 2:
            player_index = (player_index + 3) % 4
        elif self.round % 4 < 3:
            player_index = (player_index + 2) % len(self.players)
        other_player = self.players[player_index]
        for card_id in cards:
            card = Deck().get_card(int(card_id))
            player.remove(card)
            other_player.add(card)
        other_player.cards = sorted(other_player.cards)
        if self.passed_all_cards():
            self.next_turn()
            for i, player in enumerate(self.players):
                player.client.send_data({'player_index': (4 + self.player_index - i) % 4, 'cards': player.cards})

    def passed_all_cards(self):
        passed = True
        for player in self.players:
            if not player.has_passed:
                passed = False
        return passed

    def next_turn(self):
        if not self.cards_played:
            card = Card('2', 'Club')
            for i, player in enumerate(self.players):
                if card in player.cards:
                    self.player_index = i
        elif not self.cards_played % 4:
            trick_winner = self.get_trick_winner()
            for player in self.players:
                trick_winner.trick_cards.append(player.table_card)
            self.player_index = self.players.index(trick_winner)
        else:
            self.player_index = (self.player_index + 1) % len(self.players)

    def play_card(self, card):
        self.cards_played += 1
        self.players[self.player_index].table_card = card
        player_turn = self.player_index
        self.next_turn()
        for i, player in enumerate(self.players):
            player.client.send_data({'player_index': (4 + self.player_index - i) % 4,
                                       'player_turn': (4 + player_turn - i) % 4,
                                       'card_played': card})
        if self.cards_played >= 52:
            self.next_round()

    def next_round(self):
        self.round += 1
        self.cards_played = 0
        self.set_player_points()
        for player in self.players:
            player.cards = []
            player.trick_cards = []
            player.has_passed = False
        if not self.game_over():
            self.deal()
            player_index = -1
            if self.round % 4 > 2:
                self.next_turn()
                player_index = self.player_index
            player_points = [player.points for player in self.players]
            for i, player in enumerate(self.players):
                data = {'cards': player.cards, 'points': player_points[i:4] + player_points[0:i]}
                if player_index >= 0:
                    data['player_index'] = (4 + player_index - i) % 4
                player.client.send_data(data)
        else: # game over, send player points
            for i, player in enumerate(self.players):
                player.client.send_data({'points': player_points[i:4] + player_points[0:i]})

    def set_player_points(self):
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

    def game_over(self):
        game_over = False
        for player in self.players:
            if player.points >= 100:
                game_over = True
        return game_over

    def get_trick_winner(self):
        trick_winner = None
        highest_rank = -1
        ranks = [str(i) for i in range(2, 11)] + ['Jack', 'Queen', 'King', 'Ace']
        for player in self.players:
            card = player.table_card
            rank = ranks.index(card.rank)
            if card.suit == self.players[(self.player_index + 1) % 4].table_card.suit and rank >= highest_rank:
                trick_winner = player
                highest_rank = rank
        return trick_winner

    def get_player(self, player_id):
        player = None
        for p in self.players:
            if p.id == player_id:
                player = p
        return player

class HeartsHandler(asyncore.dispatcher_with_send):
    def __init__(self, hearts, *args):
        self.hearts = hearts
        super(HeartsHandler, self).__init__(*args)

    def handle_read(self):
        try:
            data = self.recv(1024).decode("UTF-8").strip()
        except socket.error:
            sys.exit("Error reading data from client.")
        #print(data)
        if data:
            data = data.split()
            if data[0] == "join":
                self.hearts.add_player(data[1], data[2], int(data[3]))
            elif data[0] == "pass":
                self.hearts.pass_cards(data[1], data[2:5])
            elif data[0] == "play":
                self.hearts.play_card(Deck().get_card(int(data[1])))

class HeartsServer(asyncore.dispatcher):
    def __init__(self, host, port):
        self.hearts = Hearts()
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