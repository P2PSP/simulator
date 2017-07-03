"""
@package simulator
monitor_sss module
"""
from queue import Queue
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .peer_sss import Peer_SSS

class Monitor_SSS(Peer_SSS):
    
    def __init__(self,id):
        super().__init__(id)
        print("SSS initialized by monitor")

    def receive_buffer_size(self):
        (self.buffer_size, sender) = self.recv()
        self.buffer_size = self.buffer_size//2
        print(self.id,"buffer size received", self.buffer_size)

        #--- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        #-------------------------------------

    def say_hello(self, peer):
        hello = (-1,"H")
        #sim.UDP_SOCKETS[peer].put((self.id,hello))
        self.senndto(hello, peer)
        print("Hello sent to", peer)

    def connect_to_the_splitter(self):
        hello = (-1,"M")
        #self.splitter["socketTCP"].put((self.id,hello))
        self.connect(hello, self.splitter)

    def complain(self, chunk_position):
        lost = (chunk_position,"L")
        self.sendto(lost, self.splitter)
        #self.splitter["socketUDP"].put((self.id,lost))

    #def PlayNextChunk (with complaints)
