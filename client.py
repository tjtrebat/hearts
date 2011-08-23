__author__ = 'Tom'

import sys
import socket
import pickle

class Client:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def connect(self):
        try:
            self.conn.connect((self.host, self.port))
        except socket.error:
            sys.exit("Remote host hung up unexpectedly.")

    def send(self, data):
        try:
            self.conn.sendall(bytes(data + "\n", "UTF-8"))
        except socket.error:
            sys.exit("Remote host hung up unexpectedly.")

    def send_data(self, obj):
        try:
            self.conn.sendall(pickle.dumps(obj))
        except socket.error:
            sys.exit("Remote host hung up unexpectedly.")

    def receive(self):
        try:
            data = self.conn.recv(1024).decode("UTF-8")
        except socket.error:
            sys.exit("Remote host hung up unexpectedly.")
        return data

    def close(self):
        self.conn.close()