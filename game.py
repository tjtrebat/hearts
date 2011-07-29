__author__ = 'Tom'

import sqlite3
import socketserver
import threading
from hearts import *

class GameThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        hearts = Hearts()
        server = multiprocessing.Process(target=hearts.run_server)
        server.start()


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip()
        thread = GameThread()
        thread.start()
        print("Running Hearts")

        # self.request is the TCP socket connected to the client
        #self.data = self.request.recv(1024).strip()
        #print "%s wrote:" % self.client_address[0]
        #print self.data
        # just send back the same data, but upper-cased
        #self.request.send(self.data.upper())

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
  