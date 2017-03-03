"""
@package p2psp-simulator
peer_ims module
"""
from queue import Queue

class Peer_core():
    def __init__(self):
        self.socket = Queue()
        self.buffer_size = 32
        print("DBS initialized")
        
    def process_message(self, message, sender):
        #TO-DO: contar el chunk

    def process_next_message(self):
        #TO-DO: Sacar de la cola y enviar a process_message

    def buffer_data(self):
        #TO-DO: buffering

    def play_next_chunk(self, last_received_chunk):
        #TO-DO: consumir el chunk (o perdido)

    def keep_the_buffer_full(self):
        #TO-DO: 
