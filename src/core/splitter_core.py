"""
@package p2psp-simulator
splitter_core module
"""
import time
from .common import Common

class Splitter_core():
    
    def __init__(self):
        self.id = "S"
        self.alive = True
        self.chunk_number = 0
        print("Splitter Core initialized")
        
    def send_chunk(self, message, destination):
        print("S -",self.chunk_number, "->", destination)
        
        print(self.id,"Put (INTENT)",message, destination)
        Common.UDP_SOCKETS[destination].put((self.id,message))
        print(self.id,"Put (DONE)",message, destination)

        
    def receive_chunk(self):
        time.sleep(0.1) #bit-rate control
        #C->Chunk, L->Lost, G->Goodbye, B->Broken, P->Peer, M->Monitor, R-> Ready
        return "C"

    def handle_arrivals(self):
        while(self.alive):
            #Thread(target=self.handle_a_peer_arrival).start()
            self.handle_a_peer_arrival()
    
    def run(self):
        raise NotImplementedError
