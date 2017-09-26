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
        self.buffer_size = self.splitter_socket.recv(5)
        print(self.id,": received buffer_size =", self.buffer_size, "from S")
        self.buffer_size //= 2
        
        #--- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        #-------------------------------------

    def complain(self, chunk_position):
        lost = (chunk_position, "L")
        self.team_socket.sendto(lost, self.splitter)
        print(self.id, ": lost chunk =", lost, "sent to", self.splitter)

    #def PlayNextChunk (with complaints)
