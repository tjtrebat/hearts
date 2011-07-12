__author__ = 'Tom'

import uuid
import random
import threading
import multiprocessing
from tkinter import *
from tkinter.ttk import *
from client import *
from server import *
from cards import *

class PlayerCanvas:
    def __init__(self, root, position):
        self.id = ""
        self.canvas = Canvas(root, width=260, height=115)
        self.cards = []
        self.position = position

    def get_position(self):
        positions = ((400, 470), (75, 250), (400, 60), (725, 250),)
        return positions[self.position]

    def __eq__(self, other):
        return self.id == other.id

class PlayerGUI(threading.Thread):
    def __init__(self, root):
        threading.Thread.__init__(self)
        self.root = root
        self.canvas = Canvas(self.root, width=800, height=520)
        self.player_frame = Frame(self.root)
        self.play_btn = Button(self.player_frame, text='Play', command=self.play_card, state=DISABLED)
        self.players = []
        self.face_down_image = PhotoImage(file="cards/b1fv.gif")
        self.cards = self.get_cards()
        self.id = str(uuid.uuid4())
        self.add_widgets()
        self.add_canvas_widgets()
        self.HOST, self.PORT = "localhost", random.randint(10000, 60000)
        self.conn = Client("localhost", 50007)
        self.conn.send("join {} {} {}".format(self.id, self.HOST, self.PORT))
        self.start()
        self.line_num = 0
        self.update_widgets()

    def add_widgets(self):
        self.root.title("Hearts")
        self.root.geometry("800x580")
        self.root.resizable(0, 0)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.canvas.pack(fill='both', expand='yes')
        self.player_frame.pack()
        self.play_btn.pack()

    def add_canvas_widgets(self):
        for position in range(4):
            player_canvas = PlayerCanvas(self.canvas, position)
            for i in range(13):
                player_canvas.cards.append(player_canvas.canvas.create_image(20 * i + 5, 50,
                                                                             image=self.face_down_image, anchor=W))
            self.canvas.create_window(player_canvas.get_position(), window=player_canvas.canvas)
            self.players.append(player_canvas)

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
                    if line[0] == "player":
                        self.players[int(line[1])].id = line[2]
                    elif line[0] == "cards":
                        player_canvas = self.get_player_canvas(line[1])
                        for i, card in enumerate(line[2:]):
                            player_canvas.canvas.itemconfig(player_canvas.cards[i], image=self.cards[int(card)])
                    self.line_num += 1
            data.close()
        self.root.after(5000, self.update_widgets)

    def play_card(self):
        pass

    def quit(self):
        self.conn.send("quit {}".format(self.id))
        self.root.destroy()

    def get_cards(self):
        cards = {}
        deck = Deck()
        for card in deck:
            cards[hash(card)] = PhotoImage(file=card.get_image())
        return cards

    def get_player_canvas(self, id):
        player_canvas = None
        for player in self.players:
            if id == player.id:
                player_canvas = player
        return player_canvas

if __name__ == "__main__":
    root = Tk()
    gui = PlayerGUI(root)
    root.mainloop()