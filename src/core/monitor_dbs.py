"""
@package simulator
monitor_dbs module
"""
from queue import Queue
from .common import Common
from .peer_dbs import Peer_DBS
from .simulator_stuff import Simulator_stuff as sim

class Monitor_DBS(Peer_DBS):
    
    def __init__(self,id):
        super().__init__(id)
        print("STRPEDS initialized by monitor")

    def receive_buffer_size(self):
        #self.buffer_size = self.socket.get()//2
        #self.buffer_size = sim.TCP_SOCKETS[self.id].get()//2
        self.buffer_size = sim.TCP_receive(self.id)//2
        print(self.id,"buffer size received", self.buffer_size)

        #--- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        #-------------------------------------
        
    def say_hello(self, peer):
        hello = (-1,"H")
        Common.UDP_SOCKETS[peer].put((self.id,hello))
        print("Hello sent to", peer)

    def connect_to_the_splitter(self):
        hello = (-1,"M")
        self.splitter["socketTCP"].put((self.id,hello))

    def complain(self, chunk_position):
        lost = (chunk_position,"L")
        self.splitter["socketUDP"].put((self.id,lost))

    #def PlayNextChunk (with complaints)
