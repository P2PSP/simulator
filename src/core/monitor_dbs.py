"""
@package simulator
monitor_dbs module
"""

import time
from queue import Queue
from .common import Common
from .peer_dbs import Peer_DBS
import pickle
#from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Socket_queue

class Monitor_DBS(Peer_DBS):
    
    def __init__(self, id):
        super().__init__(id)

    def receive_buffer_size(self):
        #(self.buffer_size, sender) = self.recv()
        self.buffer_size = pickle.loads(self.splitter_socket.recv(5))
        print(self.id, ": received buffer_size =", self.buffer_size, "from S")
        self.buffer_size //= 2

        # --- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        # -------------------------------------

    #def connect_to_the_splitter(self):
    #    hello = (-1, "M")
    #    self.send(hello, self.splitter)
    #    print(self.id, ":", hello, "sent to", self.splitter)

    def complain(self, chunk_position):
        lost = (chunk_position, "L")
        #self.sendto(lost,  self.splitter)
        self.team_socket.sendto(lost, self.splitter)
        print(self.id, ": lost chunk =", lost, "sent to", self.splitter)

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][1] == "C":
            self.played += 1
        else:
            self.losses += 1
            print(self.id, ": lost Chunk!", chunk_number)
            self.complain(chunk_number)
        self.number_of_chunks_consumed += 1
        return self.player_alive
