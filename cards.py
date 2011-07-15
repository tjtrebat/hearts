__author__ = 'Tom'

import random

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.image = self.get_image()

    def get_image(self):
        try:
            rank = int(self.rank)
        except ValueError:
            rank = self.rank[0].lower()
        return 'cards/{}.gif'.format(self.suit[0].lower() + str(rank))

    def __hash__(self):
        return hash(self.rank) ^ hash(self.suit)

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __cmp__(self, other):
        suits = ('Club', 'Diamond', 'Spade', 'Heart',)
        ranks = [str(i) for i in range(2, 11)] + ['Jack', 'Queen', 'King', 'Ace']
        if self.suit == other.suit:
            return ranks.index(self.rank) - ranks.index(other.rank)
        else:
            return suits.index(self.suit) - suits.index(other.suit)

    def __str__(self):
        return '{} of {}s'.format(self.rank, self.suit)

class Deck:
    def __init__(self, count=1):
        self.count = count
        self.cards = self.get_cards()

    def pop(self):
        return self.cards.pop()
    
    def shuffle(self):
        random.shuffle(self.cards)

    def get_cards(self):
        cards = []
        for i in range(self.count):
            for rank in list(range(2, 11)) + ['Jack', 'Queen', 'King', 'Ace']:
                for suit in ('Spade', 'Heart', 'Diamond', 'Club'):
                    cards.append(Card(str(rank), suit))
        return cards

    def __getitem__(self, item):
        return self.cards[item]

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        return ','.join([str(card) for card in self.cards])

class Hand(object):
    def __init__(self):
        self.cards = []

    def add(self, card):
        self.cards.append(card)

    def __str__(self):
        return ','.join([str(card) for card in self.cards])