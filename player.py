__author__ = 'Tom'

import sys
import uuid
import random
import socket
import asyncore
import threading
import tkinter.messagebox
from tkinter import *
from tkinter.ttk import *
from client import *
from cards import *

class PlayerCanvas:
    def __init__(self, root, position):
        self.canvas = Canvas(root, width=325, height=135)
        self.position = position
        self.cards = []

    def get_position(self):
        positions = ((500, 600), (160, 330), (500, 60), (850, 330),)
        return positions[self.position]

    def get_card_position(self):
        positions = ((500, 350), (450, 325), (500, 300), (550, 325),)
        return positions[self.position]

class Player(threading.Thread):
    def __init__(self, root, port):
        threading.Thread.__init__(self)
        self.id = uuid.uuid4()
        self.max_raised_cards = 1
        self.raised_cards = []
        self.table_cards = []
        self.in_turn = True
        self.player_canvases = []
        self.player_canvas = None
        self.suit_played = ''
        self.hearts_broken = False
        self.turn = 0
        self.round = 0
        self.root = root
        self.canvas = Canvas(self.root, width=1000, height=650)
        self.player_frame = Frame(self.root)
        self.player_btn = Button(self.player_frame, state=DISABLED)
        self.face_down_image = PhotoImage(file="cards/b1fv.gif", master=self.root)
        self.card_images = self.get_card_images()
        self.setup_root()
        self.add_widgets()
        self.add_canvas_widgets()
        self.next_round()
        self.client = Client("localhost", port)
        self.addr = ("localhost", random.randint(1000, 60000),)
        self.join_game()
        self.start()

    def setup_root(self):
        self.root.title("Hearts")
        self.root.geometry("1000x700")
        self.root.resizable(0, 0)
        #self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def add_widgets(self):
        self.canvas.pack(fill='both', expand='yes')
        self.player_frame.pack()
        self.player_btn.pack()

    def add_canvas_widgets(self):
        for position in range(4):
            player_canvas = PlayerCanvas(self.root, position)
            for i in range(13):
                player_canvas.cards.append((None, player_canvas.canvas.create_image(20 * i + 5, 70,
                                                                             anchor=W),))
                if position:
                    player_canvas.canvas.itemconfig(player_canvas.cards[-1][1], image=self.face_down_image)
            self.canvas.create_window(player_canvas.get_position(), window=player_canvas.canvas)
            self.player_canvases.append(player_canvas)
        self.player_canvas = self.player_canvases[0]

    def join_game(self):
        self.client.send("join {} {} {}".format(self.id, *self.addr))

    def add_hand(self, cards):
        # lower raised cards
        while len(self.raised_cards):
            self.player_canvas.canvas.move(self.raised_cards.pop()[1], 0, 20)
        # iterate over cards and apply appropriate image
        for i, card in enumerate(cards):
            if len(self.player_canvas.cards) <= i:
                self.player_canvas.cards.append((card, self.player_canvas.canvas.create_image(20 * i + 5, 70, anchor=W),))
            else:
                self.player_canvas.cards[i] = (card, self.player_canvas.cards[i][1],)
            self.player_canvas.canvas.itemconfig(self.player_canvas.cards[i][1], image=self.card_images[hash(card)])

    def pass_cards(self):
        self.client.send("pass {} {}".format(self.id, " ".join([str(hash(card[0])) for card in self.raised_cards])))
        self.player_btn.config(text='Play', state=DISABLED)
        self.max_raised_cards = 1
        self.in_turn = False
        self.unbind_images()

    def take_turn(self):
        self.player_btn.config(command=self.play_card)
        self.in_turn = True
        self.bind_images()

    def play_card(self):
        raised_card = self.raised_cards.pop()
        card, image = raised_card
        if self.validate_card(card):
            self.player_canvas.canvas.delete(image)
            self.player_canvas.cards.remove(raised_card)
            self.client.send("play {}".format(str(hash(card))))
            self.player_btn.config(state=DISABLED)
            self.in_turn = False
            self.unbind_images()
        else:
            self.player_canvas.canvas.move(image, 0, 20)
            self.player_canvas.canvas.tag_bind(image, "<Button-1>",
                                               lambda x, y=raised_card:self.lift_card(x, *y))
            self.player_btn.config(state=DISABLED)

    def validate_card(self, card):
        is_valid = True
        if not self.turn and Card("2", "Club") != card:
            tkinter.messagebox.showwarning("Invalid Choice", "You must start with the Two of Clubs!", master=self.root)
            is_valid = False
        elif self.suit_played.strip():
            if self.suit_played in [c[0].suit for c in self.player_canvas.cards] and card.suit != self.suit_played:
                tkinter.messagebox.showwarning("Play a {}".format(self.suit_played), "You must follow suit!", master=self.root)
                is_valid = False
        elif card.suit == "Heart" and not self.hearts_broken:
            tkinter.messagebox.showwarning("Invalid Choice", "Hearts not broken yet!", master=self.root)
            is_valid = False
        return is_valid

    def bind_images(self):
        for card, image in self.player_canvas.cards:
            self.player_canvas.canvas.tag_bind(image, "<Button-1>",
                                   lambda x, y=(card, image,):self.lift_card(x, *y))

    def unbind_images(self):
        for card in self.player_canvas.cards:
            self.player_canvas.canvas.tag_unbind(card[1], "<Button-1>")

    def lift_card(self, event, card, image):
        card = (card, image,)
        if len(self.raised_cards) < self.max_raised_cards:
            event.widget.move(image, 0, -20)
            event.widget.tag_bind(image, "<Button-1>", lambda x, y=card:self.lower_card(x, *y))
            self.raised_cards.append(card)
            if len(self.raised_cards) >= self.max_raised_cards and self.in_turn:
                self.player_btn.config(state=ACTIVE)

    def lower_card(self, event, card, image):
        card = (card, image,)
        event.widget.move(image, 0, 20)
        event.widget.tag_bind(image, "<Button-1>", lambda x, y=card:self.lift_card(x, *y))
        self.raised_cards.remove(card)
        self.player_btn.config(state=DISABLED)

    def add_table_card(self, player_index, card):
        self.turn += 1
        if not self.turn % 4:
            self.canvas.after(1000, self.remove_table_cards)
            self.suit_played = ''
        elif self.turn % 4 <= 1:
            self.suit_played = card.suit
        if card.suit == "Heart":
            self.hearts_broken = True
        self.table_cards.append((card, self.canvas.create_image(self.player_canvases[player_index].get_card_position(),
                                                                image=self.card_images[hash(card)]),))

    def remove_table_cards(self):
        while len(self.table_cards):
            self.canvas.delete(self.table_cards.pop()[1])

    def show_score(self, points):
        score = Toplevel(self.root, takefocus=True)
        for i, point in enumerate(points):
            Label(score, text="Player {}".format(i)).grid(row=0, column=i)
            Label(score, text=point).grid(row=1, column=i)
        score.mainloop()

    def next_round(self):
        self.turn = 0
        self.round += 1
        self.hearts_broken = False
        if self.round % 4 > 0:
            self.player_btn.config(command=self.pass_cards)
            if self.round % 4 < 2:
                self.player_btn.config(text='Pass Left')
            elif self.round % 4 < 3:
                self.player_btn.config(text='Pass Right')
            else:
                self.player_btn.config(text='Pass Across')
            self.max_raised_cards = 3
            self.in_turn = True

    def run(self):
        server = PlayerServer(self, *self.addr)

    def get_card_images(self):
        card_images = {}
        deck = Deck()
        for card in deck:
            card_images[hash(card)] = PhotoImage(file=card.image, master=self.root)
        return card_images

class PlayerHandler(asyncore.dispatcher_with_send):
    def __init__(self, player, *args):
        self.player = player
        super(PlayerHandler, self).__init__(*args)

    def handle_read(self):
        try:
            data = pickle.loads(self.recv(1024))
        except (socket.error, EOFError):
            sys.exit("Error reading data from client.")
        if 'card_played' in data:
            self.player.add_table_card(data['player_turn'], data['card_played'])
        if 'cards' in data:
            self.player.add_hand(data['cards'])
            self.player.bind_images()
        if 'points' in data:
            self.player.root.after(2000, lambda x= data['points']:self.player.show_score(x))
            self.player.next_round()
        if 'player_index' in data and not data['player_index']:
            self.player.take_turn()

class PlayerServer(asyncore.dispatcher):
    def __init__(self, player, host, port):
        self.player = player
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
            self.handler = PlayerHandler(self.player, sock)

if __name__ == "__main__":
    root = Tk()
    player = Player(root, 9999)
    root.mainloop()