"""
@package p2psp-simulator
splitter_core module
"""

class Splitter_core():
    
    def __init__(self):
        self.alive = True
        self.chunk_number = 0
        print("Core initialized")
        
    def send_chunk(self, message, destination):
        #print(self.chunk_number, "->", destination)
        destination.socket.put((self,message))

    def receive_chunk(self):
        #C->Chunk, L->Lost, G->Goodbye, B->Broken, P->Peer, M->Monitor, R-> Ready
        return "C"

    def run(self):
        raise NotImplementedError
