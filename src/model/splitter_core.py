"""
@package p2psp-simulator
splitter_core module
"""
from queue import Queue

class Splitter_core():
    def __init__(self):
        self.socket = Queue()
        self.buffer_size = 32
        self.alive = True
        print("DBS initialized")
        
    def send_chunk(self, message, destination):
        #TO-DO: enviar a la cola de destination
