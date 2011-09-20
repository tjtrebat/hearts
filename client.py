__author__ = 'Tom'

import socket
import pickle

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = int(port)
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.conn.connect((self.host, self.port))
        except socket.error:
            self.conn = None

    def send(self, data):
        try:
            self.conn.sendall(bytes(data + "\n", "UTF-8"))
        except socket.error:
            pass

    def send_data(self, obj):
        try:
            self.conn.sendall(pickle.dumps(obj))
        except socket.error:
            pass

    def receive(self):
        try:
            data = self.conn.recv(1024).decode("UTF-8")
        except socket.error:
            pass
        return data

    def close(self):
        self.conn.close()