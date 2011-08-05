__author__ = 'Tom'

import asyncore
import socket
from tkinter import *
from tkinter.ttk import *
from player import *
from client import *

class GameList:
    def __init__(self, root):
        self.root = root
        self.client = Client("localhost", 9999)
        self.game_list = Listbox(self.root)
        self.game_list.pack()
        self.add_games()
        self.add_menu()

    def add_games(self):
        for game in self.client.receive().split()[1:]:
            self.game_list.insert(END, game)
        Button(self.root, text="Join", command=self.join).pack()

    def add_menu(self):
        menu = Menu(self.root)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="New Game", command=self.new_game)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu)

    def new_game(self):
        self.client.send("new")
        self.play_game(self.client.receive())

    def join(self):
        self.play_game(self.game_list.get(self.game_list.curselection()[0]))

    def play_game(self, port):
        root = Tk()
        player = PlayerGUI(root, "localhost", int(port))
        root.mainloop()

    def quit(self):
        self.client.close()
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    games = GameList(root)
    root.mainloop()