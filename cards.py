__author__ = 'Tom'

import random

class Card:
    def __init__(self, rank, suit):
        self.rank = str(rank)
        self.suit = suit
        self.image = self.get_image()

    def get_image(self):
        try:
            rank = int(self.rank)
        except ValueError:
            rank = self.rank[0].lower()
        return 'cards/{}.gif'.format(self.suit[0].lower() + str(rank))

    def get_card_id(self):
        return str(hash(self))

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
        if self.suit == other.suit:
            return Deck.ranks.index(self.rank) - Deck.ranks.index(other.rank)
        else:
            return Deck.suits.index(self.suit) - Deck.suits.index(other.suit)

    def __str__(self):
        return '{} of {}s'.format(self.rank, self.suit)

class Deck:
    ranks = tuple(str(i) for i in range(2, 11)) + ('Jack', 'Queen', 'King', 'Ace',)
    suits = ('Club', 'Diamond', 'Spade', 'Heart',)

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
            for rank in self.ranks:
                for suit in self.suits:
                    cards.append(Card(rank, suit))
        return cards

    @classmethod
    def get_card(cls, card_id):
        card = None
        for rank in cls.ranks:
            for suit in cls.suits:
                if card_id == hash(Card(rank, suit)):
                    card = Card(rank, suit)
        return card

    def __getitem__(self, item):
        return self.cards[item]

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        s = ""
        for card in self.cards:
            s += str(card) + "\n"
        return s + "\r\n"

class Hand(object):
    def __init__(self):
        self.cards = []

    def add(self, card):
        self.cards.append(card)

    def remove(self, card):
        self.cards.remove(card)

    def get_card_ids(self):
        return [card.get_card_id() for card in sorted(self.cards)]

    def __str__(self):
        s = ""
        for card in self.cards:
            s += str(card) + "\n"
        return s + "\r\n"