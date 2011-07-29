__author__ = 'Tom'

#from tkinter import *
#from tkinter.ttk import *
from client import *

if __name__ == "__main__":
    client = Client("localhost", 9999)
    client.send("new")