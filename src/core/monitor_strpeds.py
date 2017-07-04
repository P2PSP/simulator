"""
@package simulator
monitor_strpeds module
"""
from queue import Queue
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .peer_strpeds import Peer_STRPEDS

class Monitor_STRPEDS(Peer_STRPEDS):
    
    def __init__(self,id):
        super().__init__(id)
        print("STRPEDS initialized by monitor")

    def receive_buffer_size(self):
        (self.buffer_size, sender) = self.recv()
        print(self.id,": received buffer_size =", self.buffer_size, "from", sender)
        self.buffer_size //= 2

        #--- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        #-------------------------------------

    def say_hello(self, peer):
        hello = (-1,"H")
        self.sendto(hello, peer)
        print("Hello sent to", peer)

    def connect_to_the_splitter(self):
        hello = (-1,"M")
        self.send(hello, self.splitter)

    def complain(self, chunk_position):
        lost = (chunk_position,"L")
        self.sendto(lost, self.splitter)

    #def PlayNextChunk (with complaints)
