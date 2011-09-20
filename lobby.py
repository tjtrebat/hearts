__author__ = 'Tom'

import uuid
import socket
import asyncore
import threading
import tkinter.messagebox
from tkinter import *
from tkinter.ttk import *
from player import *
from client import *

class Lobby(threading.Thread):
    def __init__(self, root):
        threading.Thread.__init__(self)
        self.id = uuid.uuid4()
        self.root = root
        self.client = None
        self.addr = ("localhost", random.randint(1000, 60000),)
        self.menu = Menu(self.root)
        self.host_name = StringVar(self.root)
        self.player_name = StringVar(self.root)
        self.refresh_btn = None
        self.join_btn = None
        self.setup_root()
        self.add_menu()
        self.add_header()
        self.add_game_list()
        self.start()

    def setup_root(self):
        self.root.title("Lobby")
        self.root.resizable(0, 0)
        self.root.config(padx=50, pady=10)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.player_name.set(socket.gethostname())

    def add_menu(self):
        file_menu = Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Connect", command=self.host)
        file_menu.add_command(label="New Game", command=self.new_game, state=DISABLED)
        file_menu.add_command(label="Options", command=self.options)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=self.menu)

    def config_menu_entry(self, index, **kwargs):
        file_menu = list(self.menu.children.values())[0]
        file_menu.entryconfig(index, **kwargs)

    def add_header(self):
        frame = Frame(self.root)
        frame.pack(pady=10)
        style = Style()
        style.configure("R.TLabel", foreground="red", font=('Courier New', 20, 'italic'))
        Label(frame, text="Hearts", style="R.TLabel").pack()

    def add_game_list(self):
        # add game list frame
        label_frame = LabelFrame(self.root, text='Game List')
        frame = Frame(label_frame)
        self.game_list = Listbox(frame, width=40)
        self.game_list.pack()
        frame.pack(padx=30, pady=20)
        label_frame.pack()
        # add button frame
        frame = Frame(self.root)
        self.refresh_btn = Button(frame, text="Refresh", command=self.get_games, state=DISABLED)
        self.refresh_btn.pack(side='left')
        self.join_btn = Button(frame, text="Join", command=self.join_game, state=DISABLED)
        self.join_btn.pack(side='right')
        frame.pack()

    def host(self):
        top_level = Toplevel(self.root, padx=25, pady=25)
        label_frame = LabelFrame(top_level, text="Host")
        host_name = Entry(label_frame, textvariable=self.host_name)
        host_name.focus_set()
        host_name.pack(padx=5, pady=5)
        label_frame.pack()
        Button(top_level, text="Connect", command=lambda x= top_level:self.connect_to_host(x)).pack(pady=5)

    def connect_to_host(self, top_level):
        client = Client(self.host_name.get().strip(), 9999)
        client.connect()
        if client.conn is not None:
            self.client = client
            self.client.send("join {} {} {}".format(self.id, *self.addr))
            self.config_menu_entry(1, state=ACTIVE)
            self.config_menu_entry(0, state=DISABLED)
            self.refresh_btn.config(state=ACTIVE)
            self.join_btn.config(state=ACTIVE)
            top_level.destroy()
        else:
            tkinter.messagebox.showwarning("Connection Failed", "Could not establish connection to server.", master=self.root)

    def options(self):
        top_level = Toplevel(self.root, padx=25, pady=25)
        label_frame = LabelFrame(top_level, text="Player name")
        player_name = Entry(label_frame, textvariable=self.player_name)
        player_name.focus_set()
        player_name.select_range(0, END)
        player_name.pack(padx=5, pady=5)
        label_frame.pack()
        Button(top_level, text="OK", command=top_level.destroy).pack(pady=5)

    def new_game(self):
        self.client.send("new {}".format(self.id))

    def add_games(self, games):
        self.game_list.delete(0, END)
        for game in games:
            self.game_list.insert(END, game)

    def join_game(self):
        selection = self.game_list.curselection()
        if len(selection):
            self.play_game(self.game_list.get(selection[0]))

    def play_game(self, str_addr):
        root = Tk()
        player = Player(root, str_addr.split(":"), self.player_name.get())
        root.mainloop()

    def get_games(self):
        self.client.send("games " + str(self.id))

    def quit(self):
        if self.client is not None:
            self.client.close()
        self.root.destroy()

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
                self.lobby.root.after(1000, lambda x= data[1]:self.lobby.play_game(x))

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