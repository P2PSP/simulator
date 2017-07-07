"""
@package simulator
monitor_dbs module
"""

import time
from queue import Queue
from .common import Common
from .peer_dbs import Peer_DBS
#from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Socket_queue

class Monitor_DBS(Peer_DBS):
    
    def __init__(self,id):
        super().__init__(id)

    def receive_buffer_size(self):
        (self.buffer_size, sender) = self.recv()
        print(self.id,": received buffer_size =", self.buffer_size, "from", sender)
        self.buffer_size //= 2

        #--- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        #-------------------------------------
        
    def say_hello(self, peer):
        hello = (-1,"H")
        start = time.time()
        self.sendto(hello, peer)
        print(self.id, ":", hello, "sent to", peer)
        (m, s) = self.recvfrom()
        end = time.time()
        self.RTTs.append((s, end-start))
        
    def connect_to_the_splitter(self):
        hello = (-1,"M")
        self.send(hello, self.splitter)
        print(self.id, ":", hello, "sent to", self.splitter)

    def complain(self, chunk_position):
        lost = (chunk_position,"L")
        self.sendto(lost,  self.splitter)
        print(self.id, ": lost chunk =", lost, "sent to", self.splitter)

