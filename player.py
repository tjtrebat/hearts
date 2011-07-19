__author__ = 'Tom'

import uuid
import random
import threading
import multiprocessing
import tkinter.messagebox
from tkinter import *
from tkinter.ttk import *
from client import *
from server import *
from cards import *

class PlayerCanvas:
    def __init__(self, root, position):
        self.id = ""
        self.canvas = Canvas(root, width=325, height=135)
        self.position = position
        self.cards = []

    def get_position(self):
        positions = ((500, 600), (160, 330), (500, 60), (850, 330),)
        return positions[self.position]

    def get_card_position(self):
        positions = ((500, 350), (450, 325), (500, 300), (550, 325),)
        return positions[self.position]

    def __eq__(self, other):
        return self.id == other.id

class PlayerGUI(threading.Thread):
    def __init__(self, root):
        threading.Thread.__init__(self)
        self.root = root
        self.canvas = Canvas(self.root, width=1000, height=650)
        self.player_frame = Frame(self.root)
        self.player_btn = Button(self.player_frame, text='Pass Left', command=self.pass_cards, state=DISABLED)
        self.face_down_image = PhotoImage(file="cards/b1fv.gif")
        self.cards = self.get_cards()
        self.id = str(uuid.uuid4())
        self.players = []
        self.players_added = 0
        self.raised_cards = []
        self.table_cards = []
        self.max_raised_cards = 3
        self.turn = 0
        self.in_turn = True
        self.suit_played = ''
        self.add_widgets()
        self.add_canvas_widgets()
        self.HOST, self.PORT = "localhost", random.randint(1000, 60000)
        self.conn = Client("localhost", 50007)
        self.conn.send("join {} {} {}".format(self.id, self.HOST, self.PORT))
        self.start()
        self.line_num = 0
        self.update_widgets()

    def add_widgets(self):
        self.root.title("Hearts")
        self.root.geometry("1000x700")
        self.root.resizable(0, 0)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.canvas.pack(fill='both', expand='yes')
        self.player_frame.pack()
        self.player_btn.pack()

    def add_canvas_widgets(self):
        for position in range(4):
            player_canvas = PlayerCanvas(self.canvas, position)
            for i in range(13):
                player_canvas.cards.append((None, player_canvas.canvas.create_image(20 * i + 5, 70,
                                                                             image=self.face_down_image,
                                                                             anchor=W),))
            self.canvas.create_window(player_canvas.get_position(), window=player_canvas.canvas)
            self.players.append(player_canvas)

    def pass_cards(self):
        self.unbind_images()
        self.player_btn.config(text='Play', state=DISABLED)
        self.conn.send("pass {} {}".format(self.id, " ".join([str(hash(card[0])) for card in self.raised_cards])))
        self.max_raised_cards = 1
        self.in_turn = False

    def play_card(self):
        player = self.players[0]
        raised_card = self.raised_cards.pop()
        card, image = raised_card
        if self.validate_card(card):
            player.canvas.delete(image)
            player.cards.remove(raised_card)
            self.conn.send("play {} {}".format(self.id, str(hash(card))))
            self.unbind_images()
            self.player_btn.config(state=DISABLED)
            self.in_turn = False
        else:
            player.canvas.move(image, 0, 20)
            player.canvas.tag_bind(image, "<Button-1>",
                                               lambda x, y=raised_card:self.lift_card(x, *y))
            self.player_btn.config(state=DISABLED)

    def validate_card(self, card):
        is_valid = True
        if not self.turn and Card('2', 'Club') != card:
            tkinter.messagebox.showinfo("Invalid Choice", "You must start with the Two of Clubs.")
            is_valid = False
        elif self.suit_played.strip():
            if self.suit_played in [c[0].suit for c in self.players[0].cards] and card.suit != self.suit_played:
                tkinter.messagebox.showinfo("Invalid Choice", "You must follow suit.")
                is_valid = False
        return is_valid

    def add_table_card(self, card):
        self.turn += 1
        if not self.turn % 4:
            self.canvas.after(3000, self.remove_table_cards)
            self.suit_played = ''
        elif self.turn % 4 <= 1:
            self.suit_played = card[0].suit
        self.table_cards.append(card)

    def remove_table_cards(self):
        while len(self.table_cards):
            self.canvas.delete(self.table_cards.pop()[1])

    def quit(self):
        self.conn.send("quit {}".format(self.id))
        self.root.destroy()

    def get_player_canvas(self, id):
        player_canvas = None
        for player in self.players:
            if id == player.id:
                player_canvas = player
        return player_canvas

    def bind_images(self):
        player = self.players[0]
        for card, image in player.cards:
            player.canvas.tag_bind(image, "<Button-1>",
                                   lambda x, y=(card, image,):self.lift_card(x, *y))

    def unbind_images(self):
        player = self.players[0]
        for card in player.cards:
            player.canvas.tag_unbind(card[1], "<Button-1>")

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

    def get_cards(self):
        cards = {}
        deck = Deck()
        for card in deck:
            cards[hash(card)] = PhotoImage(file=card.image)
        return cards

    def run(self):
        server = HeartsServer(self.HOST, self.PORT, "{}.p".format(self.id))

    def update_widgets(self):
        try:
            data = open("{}.p".format(self.id), "rb")
        except (IOError, EOFError):
            pass
        else:
            for line in data.readlines()[self.line_num:]:
                line = HeartsHandler.load_data(line)
                if len(line):
                    player_canvas = self.get_player_canvas(line[1])
                    if line[0] == "player":
                        self.players[self.players_added].id = line[1]
                        self.players_added += 1
                    elif line[0] == "cards":
                        for card in self.raised_cards:
                            player_canvas.canvas.move(card[1], 0, 20)
                        self.raised_cards = []
                        for i, card in enumerate(line[2:15]):
                            card = Deck().get_card(int(card))
                            player_card = player_canvas.cards[i]
                            player_card = (card, player_card[1],)
                            player_canvas.cards[i] = player_card
                            player_canvas.canvas.itemconfig(player_canvas.cards[i][1], image=self.cards[hash(card)])
                        if self.id == player_canvas.id and self.max_raised_cards >= 3:
                            self.bind_images()
                    elif line[0] == "turn":
                        self.bind_images()
                        self.player_btn.config(command=self.play_card)
                        self.in_turn = True
                    elif line[0] == "play":
                        card = Deck().get_card(int(line[2]))
                        self.add_table_card((card, self.canvas.create_image(player_canvas.get_card_position(),
                                                                            image=self.cards[hash(card)]),))
                    elif line[0] == "quit":
                        player_canvas.canvas.delete(ALL)
                    self.line_num += 1
            data.close()
        self.root.after(5000, self.update_widgets)

if __name__ == "__main__":
    root = Tk()
    gui = PlayerGUI(root)
    root.mainloop()