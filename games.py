__author__ = 'Tom'

from tkinter import *
from tkinter.ttk import *
from client import *

class GameList:
    def __init__(self, root):
        self.root = root
        self.client = Client("localhost", 9999)
        self.add_games()
        self.add_menu()

    def add_games(self):
        l = Listbox(self.root)
        l.pack()
        for game in self.get_games():
            l.insert(END, game)
        Button(self.root, text="Join").pack()

    def add_menu(self):
        menu = Menu(self.root)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="New Game", command=self.new_game)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=quit)
        menu.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu)

    def new_game(self):
        self.client.send("new")

    def get_games(self):
        self.client.send("games")
        games = self.client.receive()
        print(games)
        return games.split()

if __name__ == "__main__":
    root = Tk()
    games = GameList(root)
    root.mainloop()