"""
@package simulator
peer_dbs3b module
"""

# DB3B optimizes the topology of the overlay. Defines an optimization
# horizon OH (smaller than the buffering horizon BH) and when a chunk
# is lost in the optimization horizon, it is requested to the peer
# with smaller debt in the optimization horizon. The OH starts being
# equal to the BH. If N consecutive rounds no optimization losses have
# been produced, the OH is decremented in 1. When a chunk is lost in
# the OH, the OH is incremented in 1.

import random
from .chunk_structure import ChunkStructure
from .peer_dbs import Peer_DBS
from .peer_dbs2 import Peer_DBS2
import colorama
import core.stderr as stderr
from .limits import Limits
import struct
from .ip_tools import IP_tools
from .messages import Messages
import time

class Peer_DBS3(Peer_DBS2):

    def __init__(self):
        Peer_DBS2.__init__(self)
        self.optimization_horizon = 0
        self.optimize_lost = 0

    def __set_optimization_horizon(self, optimization_horizon):
        self.optimization_horizon = optimization_horizon

    def __set_optimal_neighborhood_degree(self, optimal_neighborhood_degree):
        self.optimal_neighborhood_degree = optimal_neighborhood_degree

    def play_chunk(self, chunk_number):
        optimized_chunk = (chunk_number + self.optimization_horizon) % Limits.MAX_CHUNK_NUMBER
        buffer_box = self.buffer[optimized_chunk % self.buffer_size]
        #stderr.write(f"{buffer_box} {self.optimization_horizon} {optimized_chunk}\n")
        if buffer_box[ChunkStructure.CHUNK_DATA] == b'L':
            #try:
            #    peer = min(self.debt, key=self.debt.get)
            #    self.request_path(chunk_number, peer)
            #except ValueError:
            #    pass
            self.request_chunk_to_random_peer(chunk_number)
            self.optimization_horizon -= 1
            if self.optimization_horizon < 0:
                self.optimization_horizon = 0

        #self.chunk_potentially_lost = optimized_chunk + self.buffer_size//3
        Peer_DBS2.play_chunk(self, chunk_number)

    def on_chunk_received_from_the_splitter(self, chunk):
        Peer_DBS2.on_chunk_received_from_the_splitter(self, chunk)
        self.optimization_horizon += 1
