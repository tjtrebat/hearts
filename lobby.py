__author__ = 'Tom'

import uuid
import socket
import asyncore
import threading
from tkinter import *
from tkinter.ttk import *
from player import *
from client import *

class Lobby(threading.Thread):
    def __init__(self, root):
        threading.Thread.__init__(self)
        self.id = uuid.uuid4()
        self.root = root
        self.client = Client("localhost", 9999)
        self.addr = ("localhost", random.randint(1000, 60000),)
        self.game_list = Listbox(self.root)
        self.game_list.pack()
        Button(self.root, text="Join", command=self.join_game).pack()
        self.add_menu()
        self.join_server()
        self.start()

    def join_server(self):
        self.client.send("join {} {} {}".format(self.id, *self.addr))

    def join_game(self):
        self.play_game(int(self.game_list.get(self.game_list.curselection()[0])))

    def new_game(self):
        self.client.send("new {}".format(self.id))

    def play_game(self, port):
        root = Tk()
        player = Player(root, port)
        root.mainloop()

    def quit(self):
        self.client.close()
        self.root.destroy()

    def add_games(self, games):
        for game in games:
            self.game_list.insert(END, game)

    def add_menu(self):
        menu = Menu(self.root)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="New Game", command=self.new_game)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu)

    def run(self):
        server = LobbyServer(self, *self.addr)

class LobbyHandler(asyncore.dispatcher_with_send):
    def __init__(self, lobby, *args):
        self.lobby = lobby
        super(LobbyHandler, self).__init__(*args)

    def handle_read(self):
        try:
            data = self.recv(1024).decode("UTF-8").strip()
        except socket.error:
            sys.exit("Error reading data from client.")
        if data:
            data = data.split()
            if data[0] == "games":
                self.lobby.add_games(data[1:])
            if data[0] == "new":
                self.lobby.root.after(1000, lambda x= int(data[1]):self.lobby.play_game(x))

class LobbyServer(asyncore.dispatcher):
    def __init__(self, lobby, host, port):
        self.lobby = lobby
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
            self.handler = LobbyHandler(self.lobby, sock)

if __name__ == "__main__":
    root = Tk()
    games = Lobby(root)
    root.mainloop()